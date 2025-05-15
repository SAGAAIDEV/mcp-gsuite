import os
from ...config.env import gsuite_config
from google.oauth2.credentials import Credentials
from saaga_mcp_base.lib.logging import logger
import pickle


def _get_credential_filename(user_id: str) -> str:
    path = os.path.join(gsuite_config.credentials_dir, f".oauth2.{user_id}.pickle")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Credential file does not exist: {path}")
    return path


def get_stored_credentials(user_email: str) -> Credentials | None:
    """Retrieved stored credentials for the provided user ID.

    Args:
    user_id: User's ID.
    Returns:
    Stored oauth2client.client.OAuth2Credentials if found, None otherwise.
    """
    try:
        cred_file_path = _get_credential_filename(user_id=user_email)
        logger.info(f"Loading credentials from {cred_file_path}")
        with open(cred_file_path, "rb") as f:
            creds = pickle.load(f)
        return creds
    except FileNotFoundError:
        logger.warning(
            f"No stored Oauth2 credentials yet at path for user: {user_email}"
        )
        return None
    except Exception as e:
        logger.error(f"Error loading credentials for user {user_email}: {e}")
        raise
