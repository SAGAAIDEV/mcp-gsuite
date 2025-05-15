import os
import json
import fire  # Added import for python-fire
import pickle  # Added import for pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- External ---
from mcp_gsuite.config.env import gsuite_config  # Added for config
import pydantic  # Added for AccountInfo
from saaga_mcp_base.lib.logging import logger  # Added logger
from .utils import (
    construct_credential_path,
    get_email_from_credentials,
)  # Added import for utils

# --- Configuration ---
# TODO: IMPORTANT - Replace these with the actual scopes you need!
DEFAULT_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar",
]

# USER_TOKEN_FILENAME = "token.json" # No longer a fixed filename


def authenticate(scopes=None):
    """
    Authenticates the user using the Google OAuth 2.0 installed app flow.
    Saves the credentials to a file named .oauth2.[user_id].json and returns them.

    Args:
        scopes (list, optional): A list of OAuth scopes to request.
                                 Defaults to DEFAULT_SCOPES.

    Returns:
        google.oauth2.credentials.Credentials: The authenticated credentials,
                                               or None if authentication fails.
    """
    if scopes is None:
        scopes = DEFAULT_SCOPES

    try:
        client_secret_file_path = str(gsuite_config.get_client_secrets_file())
        credentials_storage_dir = gsuite_config.credentials_dir
        gsuite_config.verify_credentials_dir()  # Ensure the directory exists
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return None

    os.makedirs(credentials_storage_dir, exist_ok=True)

    creds = None
    email = None

    if not creds or not creds.valid:
        logger.info("Starting new authentication flow...")
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_file_path, scopes
            )
            creds = flow.run_local_server(host="localhost", port=8080)

            if not creds:
                logger.error("Authentication flow did not return credentials.")
                return None
            logger.info("Authentication successful.")

            email = get_email_from_credentials(creds)
            if not email:
                logger.error(
                    "Auth successful, but could not extract user ID from credentials. Cannot save token."
                )
                return None

            final_token_path = construct_credential_path(email)
            with open(final_token_path, "wb") as token_file:  # Changed to wb for pickle
                pickle.dump(creds, token_file)  # Save as pickle
            logger.info(f"Credentials saved to {final_token_path}")

        except Exception as e:
            path_for_error_log = "unknown path"
            if email:
                try:
                    path_for_error_log = construct_credential_path(email)
                except Exception:
                    pass
                logger.error(
                    f"Error during authentication or saving credentials to {path_for_error_log}: {e}",
                    exc_info=True,
                )
            else:
                logger.error(
                    f"Error during authentication flow or user ID extraction: {e}",
                    exc_info=True,
                )
            return None

    return creds


def main():
    creds = authenticate()
    logger.info(creds)


if __name__ == "__main__":
    fire.Fire(authenticate)
