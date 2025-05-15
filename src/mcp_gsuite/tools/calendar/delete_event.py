import json
import asyncio
from typing import (
    Optional,
    List,
    Dict,
    Any,
)  # Added for consistency, though not strictly needed for this file
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import calendar
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def delete_event(
    user_id: str,
    event_id: str,
    calendar_id: str = "primary",
    send_notifications: bool = True,
) -> str:
    """
    Delete a calendar event by its ID.

    Args:
        user_id: {user_id_arg}
        event_id (str): The ID of the event to delete.
        calendar_id (str): Calendar identifier. Defaults to 'primary'.
        send_notifications (bool): Whether to send cancellation notifications to attendees. Defaults to True.

    Returns:
        str: JSON string confirming success or detailing failure.
    """
    logger.info(
        f"Deleting event_id: {event_id} for user_id: {user_id}, calendar_id: {calendar_id}"
    )
    try:
        calendar_service = calendar.CalendarService(user_id=user_id)
        logger.debug(
            f"CalendarService initialized for user_id: {user_id} for delete_event"
        )

        success = await asyncio.to_thread(
            calendar_service.delete_event,
            event_id=event_id,
            send_notifications=send_notifications,
            calendar_id=calendar_id,
        )

        if success:
            logger.info(
                f"Successfully deleted event_id: {event_id} for user_id: {user_id}, calendar_id: {calendar_id}"
            )
            response = {
                "message": f"Successfully deleted event {event_id}",
                "user_id": user_id,
                "event_id": event_id,
                "calendar_id": calendar_id,
            }
            return json.dumps(response, indent=2)
        else:
            logger.warning(
                f"Failed to delete event_id: {event_id} for user_id: {user_id}, calendar_id: {calendar_id}. Service returned False."
            )
            error_response = {
                "message": f"Failed to delete event {event_id}. Service indicated failure.",
                "user_id": user_id,
                "event_id": event_id,
                "calendar_id": calendar_id,
            }
            # Raise an exception with JSON string for consistency
            raise Exception(json.dumps(error_response, indent=2))

    except Exception as e:
        # If the exception is already a JSON string from our manual raise, re-raise it
        # Otherwise, format it.
        if isinstance(e, Exception) and e.args and isinstance(e.args[0], str):
            try:
                json.loads(e.args[0])  # Check if it's a JSON string
                raise  # Re-raise if it is
            except json.JSONDecodeError:
                pass  # Not a JSON string, format below

        logger.error(
            f"Error in delete_event for user_id: {user_id}, event_id: {event_id}. Error: {str(e)}",
            exc_info=True,
        )
        error_response = {
            "error": f"Failed to delete event {event_id} for {user_id}: {str(e)}",
            "user_id": user_id,
            "event_id": event_id,
            "calendar_id": calendar_id,
        }
        raise Exception(json.dumps(error_response, indent=2))
