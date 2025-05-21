import json
import asyncio
from typing import Optional, List
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import gmail
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def update_draft(
    user_id: str,
    draft_id: str,
    to: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    cc: Optional[List[str]] = None,
) -> str:
    """
    Update an existing draft email message.
    Only provided fields will be updated; others will retain their existing values.

    Args:
        user_id: {user_id_arg}
        draft_id (str): The ID of the draft to update.
        to (str, optional): New email address of the recipient.
        subject (str, optional): New subject line of the email.
        body (str, optional): New body content of the email.
        cc (list[str], optional): New list of email addresses to CC. If an empty list is provided, CCs will be cleared.
                                 If None, CCs will not be changed.
    """
    log_details = f"draft_id: {draft_id}"
    if to:
        log_details += f", to: {to}"
    if subject:
        log_details += f", subject: '{subject}'"
    if body:
        log_details += ", body: [provided]"
    if cc is not None:
        log_details += f", cc: {cc}"

    logger.info(f"Updating draft for user_id: {user_id}, {log_details}")
    try:
        gmail_service = gmail.GmailService(user_id=user_id)
        logger.debug(f"GmailService initialized for user_id: {user_id}")

        updated_draft_result = await asyncio.to_thread(
            gmail_service.update_draft,
            draft_id=draft_id,
            to=to,
            subject=subject,
            body=body,
            cc=cc,
        )

        if updated_draft_result is None:
            logger.warning(f"Failed to update draft {draft_id} for user_id: {user_id}")
            return json.dumps(
                {
                    "message": f"Failed to update draft {draft_id}.",
                    "user_id": user_id,
                    "draft_id": draft_id,
                },
                indent=2,
            )

        logger.info(
            f"Successfully updated draft {draft_id} for user_id: {user_id}, new draft_id: {updated_draft_result.get('id')}"
        )
        return json.dumps(updated_draft_result, indent=2)

    except Exception as e:
        logger.error(
            f"Error in update_draft for user_id: {user_id}, {log_details}. Error: {str(e)}",
            exc_info=True,
        )
        error_message = {
            "error": f"Failed to update draft {draft_id} for {user_id}: {str(e)}"
        }
        raise Exception(error_message)
