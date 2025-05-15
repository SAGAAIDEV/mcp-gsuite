import os
from googleapiclient.discovery import build
from mcp_gsuite.config.env import gsuite_config
from saaga_mcp_base.lib.logging import logger


def construct_credential_path(user_id: str) -> str:
    return os.path.join(gsuite_config.credentials_dir, f".oauth2.{user_id}.pickle")


def get_email_from_credentials(creds):
    """Helper function to get user ID (email address) from credentials."""
    if not creds:
        return None
    try:
        # Required scopes for userinfo are typically 'openid', 'email', 'profile'.
        # DEFAULT_SCOPES includes openid and userinfo.email.
        service = build("oauth2", "v2", credentials=creds)
        user_info = service.userinfo().get().execute()
        email = user_info.get("email")
        if not email:
            logger.error("Error: Email not found in user_info response.")
            return None
        # Return the full email as the user_id
        return email
    except Exception as e:
        logger.error(f"Error fetching user ID: {e}")
        return None
