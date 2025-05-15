import json
import asyncio
from typing import Optional, List, Dict, Any
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import calendar
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def update_event(
    user_id: str,
    event_id: str,
    calendar_id: str = "primary",
    summary: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    send_notifications: bool = True,
    timezone: Optional[str] = None,
) -> str:
    """
    Update an existing calendar event.

    Args:
        user_id: {user_id_arg}
        event_id (str): The ID of the event to update.
        calendar_id (str): Calendar identifier. Defaults to 'primary'.
        summary (str, optional): New title of the event.
        start_time (str, optional): New start time in RFC3339 format.
        end_time (str, optional): New end time in RFC3339 format.
        location (str, optional): New location of the event.
        description (str, optional): New description of the event.
        attendees (list, optional): New list of attendee email addresses.
        send_notifications (bool): Whether to send notifications to attendees. Defaults to True.
        timezone (str, optional): New timezone for the event (e.g., 'America/New_York').

    Returns:
        str: JSON string containing the updated event data or an error message if update fails.
    """
    logger.info(
        f"Updating event for user_id: {user_id}, event_id: {event_id}, calendar_id: {calendar_id}"
    )
    try:
        calendar_service = calendar.CalendarService(user_id=user_id)
        logger.debug(
            f"CalendarService initialized for user_id: {user_id} for update_event"
        )

        updated_event_data = await asyncio.to_thread(
            calendar_service.update_event,
            event_id=event_id,
            calendar_id=calendar_id,
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            location=location,
            description=description,
            attendees=attendees,
            send_notifications=send_notifications,
            timezone=timezone,
        )

        if updated_event_data is None:
            logger.warning(
                f"Failed to update event for user_id: {user_id}, event_id: {event_id}, calendar_id: {calendar_id}"
            )
            error_response = {
                "message": "Failed to update event.",
                "user_id": user_id,
                "event_id": event_id,
                "calendar_id": calendar_id,
            }
            raise Exception(json.dumps(error_response, indent=2))

        logger.info(
            f"Successfully updated event with id: {updated_event_data.get('id')} for user_id: {user_id}, calendar_id: {calendar_id}"
        )
        return json.dumps(updated_event_data, indent=2)

    except Exception as e:
        if isinstance(e, Exception) and e.args and isinstance(e.args[0], str):
            try:
                json.loads(e.args[0])
                raise
            except json.JSONDecodeError:
                pass

        logger.error(
            f"Error in update_event for user_id: {user_id}, event_id: {event_id}. Error: {str(e)}",
            exc_info=True,
        )
        error_response = {
            "error": f"Failed to update event for {user_id}, event_id '{event_id}': {str(e)}",
            "user_id": user_id,
            "event_id": event_id,
            "calendar_id": calendar_id,
        }
        raise Exception(json.dumps(error_response, indent=2))
