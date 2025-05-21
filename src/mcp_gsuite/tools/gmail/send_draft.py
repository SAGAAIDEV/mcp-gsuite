import json
import asyncio
from typing import Optional, List, Dict
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import gmail
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def send_draft(user_id: str, draft_id: str) -> str:
    """
    Sends a previously created draft email.

    Args:
        user_id: {user_id_arg}
        draft_id (str): The ID of the draft to send.
    """
    logger.info(f"Sending draft {draft_id} for user_id: {user_id}")
    try:
        gmail_service = gmail.GmailService(user_id=user_id)
        logger.debug(f"GmailService initialized for user_id: {user_id}")

        sent_message = await asyncio.to_thread(
            gmail_service.send_draft, draft_id=draft_id
        )

        if sent_message is None:
            logger.warning(f"Failed to send draft {draft_id} for user_id: {user_id}")
            return json.dumps(
                {
                    "message": "Failed to send draft.",
                    "user_id": user_id,
                    "draft_id": draft_id,
                },
                indent=2,
            )

        logger.info(f"Successfully sent draft {draft_id} for user_id: {user_id}")
        return json.dumps(sent_message, indent=2)

    except Exception as e:
        logger.error(
            f"Error in send_draft for user_id: {user_id}, draft_id: {draft_id}. Error: {str(e)}",
            exc_info=True,
        )
        error_message = {
            "error": f"Failed to send draft {draft_id} for {user_id}: {str(e)}"
        }
        raise Exception(error_message)
