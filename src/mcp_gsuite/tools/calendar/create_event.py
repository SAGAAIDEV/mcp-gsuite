import json
import asyncio
from typing import Optional, List, Dict, Any
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import calendar
from saaga_mcp_base import logger


# TODO: Add support for zoom meetings
@format_docstring_with_user_id_arg
async def create_event(
    user_id: str,
    summary: str,
    start_time: str,
    end_time: str,
    calendar_id: str = "primary",
    location: Optional[str] = None,
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    send_notifications: bool = True,
    timezone: Optional[str] = None,  # Already in CalendarService, adding here
) -> str:
    """
    Create a new calendar event.

    Args:
        user_id: {user_id_arg}
        summary (str): Title of the event.
        start_time (str): Start time in RFC3339 format.
        end_time (str): End time in RFC3339 format.
        calendar_id (str): Calendar identifier. Defaults to 'primary'.
        location (str, optional): Location of the event.
        description (str, optional): Description of the event.
        attendees (list, optional): List of attendee email addresses.
        send_notifications (bool): Whether to send notifications to attendees. Defaults to True.
        timezone (str, optional): Timezone for the event (e.g., 'America/New_York'). Defaults to 'UTC' in service.

    Returns:
        str: JSON string containing the created event data or None if creation fails.
    """
    logger.info(
        f"Creating event for user_id: {user_id}, summary: {summary}, calendar_id: {calendar_id}"
    )
    try:
        calendar_service = calendar.CalendarService(user_id=user_id)
        logger.debug(
            f"CalendarService initialized for user_id: {user_id} for create_event"
        )

        created_event_data = await asyncio.to_thread(
            calendar_service.create_event,
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            location=location,
            description=description,
            attendees=attendees,
            send_notifications=send_notifications,
            timezone=timezone,
            calendar_id=calendar_id,
        )

        if created_event_data is None:
            logger.warning(
                f"Failed to create event for user_id: {user_id}, summary: {summary}, calendar_id: {calendar_id}"
            )
            # Consistent error response structure
            error_response = {
                "message": "Failed to create event.",
                "user_id": user_id,
                "summary": summary,
                "calendar_id": calendar_id,
            }
            # Raise exception with JSON string as per create_reply.py pattern
            raise Exception(json.dumps(error_response, indent=2))

        logger.info(
            f"Successfully created event with id: {created_event_data.get('id')} for user_id: {user_id}, calendar_id: {calendar_id}"
        )
        return json.dumps(created_event_data, indent=2)

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
            f"Error in create_event for user_id: {user_id}, summary: {summary}. Error: {str(e)}",
            exc_info=True,
        )
        error_response = {
            "error": f"Failed to create event for {user_id}, summary '{summary}': {str(e)}",
            "user_id": user_id,
            "summary": summary,
            "calendar_id": calendar_id,
        }
        raise Exception(json.dumps(error_response, indent=2))
