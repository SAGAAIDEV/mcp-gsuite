import json
import asyncio
from typing import Optional, List, Dict
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import gmail
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def create_draft(
    user_id: str, to: str, subject: str, body: str, cc: Optional[List[str]] = None
) -> str:
    """
    Create a draft email message.

    Args:
        user_id: {user_id_arg}
        to (str): Email address of the recipient
        subject (str): Subject line of the email
        body (str): Body content of the email
        cc (list[str], optional): List of email addresses to CC
    """
    logger.info(
        f"Creating draft for user_id: {user_id}, to: {to}, subject: '{subject}'"
    )
    try:
        gmail_service = gmail.GmailService(user_id=user_id)
        logger.debug(f"GmailService initialized for user_id: {user_id}")

        draft = await asyncio.to_thread(
            gmail_service.create_draft, to=to, subject=subject, body=body, cc=cc
        )

        if draft is None:
            logger.warning(
                f"Failed to create draft for user_id: {user_id}, to: {to}, subject: '{subject}'"
            )
            return json.dumps(
                {
                    "message": "Failed to create draft.",
                    "user_id": user_id,
                    "to": to,
                    "subject": subject,
                },
                indent=2,
            )

        logger.info(
            f"Successfully created draft for user_id: {user_id}, draft_id: {draft.get('id')}"
        )
        return json.dumps(draft, indent=2)

    except Exception as e:
        logger.error(
            f"Error in create_draft for user_id: {user_id}, to: {to}, subject: '{subject}'. Error: {str(e)}",
            exc_info=True,
        )
        error_message = {"error": f"Failed to create draft for {user_id}: {str(e)}"}
        raise Exception(error_message)
