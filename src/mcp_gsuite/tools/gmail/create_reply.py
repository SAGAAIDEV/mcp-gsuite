import json
import asyncio
from typing import Optional, List, Dict, Any
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import gmail
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def create_reply(
    user_id: str,
    original_message_id: str,
    reply_body: str,
    send: bool = False,
    cc: Optional[List[str]] = None,
) -> str:
    """
    Create a reply to an email message and either send it or save as draft.

    Args:
        user_id: {user_id_arg}
        original_message_id (str): The ID of the original message to reply to.
        reply_body (str): Body content of the reply
        send (bool): If True, sends the reply immediately. If False, saves as draft.
        cc (list[str], optional): List of email addresses to CC
    """
    logger.info(
        f"Creating reply for user_id: {user_id}, original_message_id: {original_message_id}, send: {send}"
    )
    try:
        gmail_service = gmail.GmailService(user_id=user_id)
        logger.debug(f"GmailService initialized for user_id: {user_id}")

        # Fetch the original message details first
        original_message_data, _ = await asyncio.to_thread(
            gmail_service.get_email_by_id, email_id=original_message_id
        )

        if not original_message_data:
            logger.warning(
                f"Failed to retrieve original message for reply. user_id: {user_id}, original_message_id: {original_message_id}"
            )
            return json.dumps(
                {
                    "message": "Failed to retrieve original message to reply to.",
                    "user_id": user_id,
                    "original_message_id": original_message_id,
                },
                indent=2,
            )

        result = await asyncio.to_thread(
            gmail_service.create_reply,
            original_message=original_message_data,
            reply_body=reply_body,
            send=send,
            cc=cc,
        )

        if result is None:
            logger.warning(
                f"Failed to create reply for user_id: {user_id}, original_message_id: {original_message_id}"
            )
            return json.dumps(
                {
                    "message": "Failed to create reply.",
                    "user_id": user_id,
                    "original_message_id": original_message_id,
                },
                indent=2,
            )

        action = "sent" if send else "drafted"
        logger.info(
            f"Successfully {action} reply for user_id: {user_id}, result_id: {result.get('id')}"
        )
        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(
            f"Error in create_reply for user_id: {user_id}, original_message_id: {original_message_id}. Error: {str(e)}",
            exc_info=True,
        )
        error_message = {"error": f"Failed to create reply for {user_id}: {str(e)}"}
        raise Exception(error_message)
