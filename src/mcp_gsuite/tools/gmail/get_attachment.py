import json
import asyncio
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from mcp_gsuite.lib import gmail
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def get_attachment(user_id: str, message_id: str, attachment_id: str) -> str:
    """
    Retrieves a Gmail attachment by its ID.

    Args:
        user_id: {user_id_arg}
        message_id (str): The ID of the Gmail message containing the attachment
        attachment_id (str): The ID of the attachment to retrieve
    """
    logger.info(
        f"Retrieving attachment for user_id: {user_id}, message_id: {message_id}, attachment_id: {attachment_id}"
    )
    try:
        gmail_service = gmail.GmailService(user_id=user_id)
        logger.debug(f"GmailService initialized for user_id: {user_id}")

        attachment_data = await asyncio.to_thread(
            gmail_service.get_attachment,
            message_id=message_id,
            attachment_id=attachment_id,
        )

        if attachment_data is None:
            logger.warning(
                f"Failed to retrieve attachment for user_id: {user_id}, message_id: {message_id}, attachment_id: {attachment_id}"
            )
            return json.dumps(
                {
                    "message": "Failed to retrieve attachment.",
                    "user_id": user_id,
                    "message_id": message_id,
                    "attachment_id": attachment_id,
                },
                indent=2,
            )

        # Attachment data can be large, consider how to handle it.
        # For now, returning it as part of JSON. If it's binary, it's base64 encoded by Gmail API.
        logger.info(
            f"Successfully retrieved attachment for user_id: {user_id}, message_id: {message_id}, attachment_id: {attachment_id}"
        )
        return json.dumps(attachment_data, indent=2)

    except Exception as e:
        logger.error(
            f"Error in get_attachment for user_id: {user_id}, message_id: {message_id}, attachment_id: {attachment_id}. Error: {str(e)}",
            exc_info=True,
        )
        error_message = {"error": f"Failed to get attachment for {user_id}: {str(e)}"}
        raise Exception(error_message)
