import json
import asyncio
from typing import Optional
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import gmail
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def create_label(
    user_id: str,
    label_name: str,
    label_list_visibility: Optional[str] = "labelShow",
    message_list_visibility: Optional[str] = "show",
) -> str:
    """
    Create a new label in Gmail.

    Args:
        user_id: {user_id_arg}
        label_name (str): The name of the new label.
        label_list_visibility (str, optional): Visibility of the label in the label list (e.g., "labelShow", "labelHide"). Defaults to "labelShow".
        message_list_visibility (str, optional): Visibility of messages with this label (e.g., "show", "hide"). Defaults to "show".
    """
    logger.info(
        f"Creating label '{label_name}' for user_id: {user_id} with visibility: label_list='{label_list_visibility}', message_list='{message_list_visibility}'"
    )
    try:
        gmail_service = gmail.GmailService(user_id=user_id)
        logger.debug(f"GmailService initialized for user_id: {user_id}")

        created_label = await asyncio.to_thread(
            gmail_service.create_label,
            label_name=label_name,
            label_list_visibility=label_list_visibility,
            message_list_visibility=message_list_visibility,
        )

        if created_label is None:
            logger.warning(
                f"Failed to create label '{label_name}' for user_id: {user_id}"
            )
            return json.dumps(
                {
                    "message": f"Failed to create label '{label_name}'.",
                    "user_id": user_id,
                    "label_name": label_name,
                },
                indent=2,
            )

        logger.info(
            f"Successfully created label '{label_name}' for user_id: {user_id}, label_id: {created_label.get('id')}"
        )
        return json.dumps(created_label, indent=2)

    except Exception as e:
        logger.error(
            f"Error in create_label for user_id: {user_id}, label_name: '{label_name}'. Error: {str(e)}",
            exc_info=True,
        )
        error_message = {
            "error": f"Failed to create label '{label_name}' for {user_id}: {str(e)}"
        }
        raise Exception(error_message)
