import json
import asyncio
from typing import Optional, List
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import gmail
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def set_email_labels(
    user_id: str,
    message_id: str,
    label_names_to_add: Optional[List[str]] = None,
    label_names_to_remove: Optional[List[str]] = None,
) -> str:
    """
    Add or remove labels from an email message using label names.
    The service will attempt to map these names to their respective IDs.

    Args:
        user_id: {user_id_arg}
        message_id (str): The ID of the message to modify.
        label_names_to_add (list[str], optional): List of label names to add.
        label_names_to_remove (list[str], optional): List of label names to remove.
    """
    logger.info(
        f"Tool set_email_labels called for message {message_id}, user_id: {user_id}. "
        f"Add Names: {label_names_to_add}, Remove Names: {label_names_to_remove}"
    )
    try:
        gmail_service = gmail.GmailService(user_id=user_id)
        logger.debug(
            f"GmailService initialized for user_id: {user_id} in tool set_email_labels."
        )

        if not label_names_to_add and not label_names_to_remove:
            logger.info(
                f"No label names provided to add or remove for message {message_id}."
            )
            # Consistent with Gmail API, if no changes, often the current state is returned or a specific no-op status.
            # Fetching current state to provide a meaningful response.
            current_message_state = await asyncio.to_thread(
                gmail_service.service.users()
                .messages()
                .get(userId="me", id=message_id)
                .execute
            )
            return json.dumps(current_message_state, indent=2)

        updated_message = await asyncio.to_thread(
            gmail_service.set_email_labels,  # This now expects names
            message_id=message_id,
            label_names_to_add=label_names_to_add,
            label_names_to_remove=label_names_to_remove,
        )

        if updated_message is None:
            # This implies an issue within GmailService.set_email_labels,
            # possibly label name resolution failure or API error.
            logger.warning(
                f"Failed to set labels for message {message_id} (user: {user_id}) via GmailService."
            )
            # The GmailService.set_email_labels should ideally log details of why it returned None.
            # The tool should return a clear error message.
            return json.dumps(
                {
                    "error": f"Failed to set labels for message {message_id}. Label names might be invalid or an API error occurred.",
                    "user_id": user_id,
                    "message_id": message_id,
                    "label_names_to_add": label_names_to_add,
                    "label_names_to_remove": label_names_to_remove,
                },
                indent=2,
            )

        logger.info(
            f"Successfully set labels for message {message_id} (user: {user_id}). Result: {json.dumps(updated_message)} "
        )
        return json.dumps(updated_message, indent=2)

    except Exception as e:
        logger.error(
            f"Unhandled error in tool set_email_labels for user_id: {user_id}, message_id: {message_id}. Error: {str(e)}",
            exc_info=True,
        )
        return json.dumps(
            {
                "error": f"An unexpected error occurred while setting labels for message {message_id}: {str(e)}",
                "user_id": user_id,
                "message_id": message_id,
            },
            indent=2,
        )
