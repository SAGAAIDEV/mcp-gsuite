import json
import asyncio
from typing import (
    Any,
    Tuple,
)  # email_data could be Dict[str, Any], attachments could be Dict[str, Dict[str, Any]]
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import gmail
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def get_email_by_id(user_id: str, email_id: str) -> str:
    """
    Fetch and parse a complete email message by its ID including attachment IDs.

    Args:
        user_id: {user_id_arg} d
        email_id (str): The Gmail message ID to retrieve
    """
    logger.info(
        f"Fetching email by ID with attachments for user_id: {user_id}, email_id: {email_id}"
    )
    try:
        gmail_service = gmail.GmailService(user_id=user_id)
        logger.debug(f"GmailService initialized for user_id: {user_id}")

        email_data, attachments = await asyncio.to_thread(
            gmail_service.get_email_by_id, email_id=email_id
        )

        if email_data is None:
            logger.warning(
                f"Failed to retrieve email for user_id: {user_id}, email_id: {email_id}"
            )
            return json.dumps(
                {
                    "message": "Failed to retrieve email.",
                    "user_id": user_id,
                    "email_id": email_id,
                },
                indent=2,
            )

        logger.info(
            f"Successfully retrieved email for user_id: {user_id}, email_id: {email_id}"
        )
        return json.dumps({"email": email_data, "attachments": attachments}, indent=2)

    except Exception as e:
        logger.error(
            f"Error in get_email_by_id_with_attachments for user_id: {user_id}, email_id: {email_id}. Error: {str(e)}",
            exc_info=True,
        )
        error_message = {
            "error": f"Failed to get email by id with attachments for {user_id}: {str(e)}"
        }
        raise Exception(error_message)
