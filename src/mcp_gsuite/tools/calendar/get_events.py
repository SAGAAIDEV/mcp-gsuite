import json
import asyncio
from typing import Optional, List, Dict, Any
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import calendar
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def get_events(
    user_id: str,
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 250,
    show_deleted: bool = False,
) -> str:
    """
    Retrieve calendar events within a specified time range.

    Args:
        user_id: {user_id_arg}
        calendar_id (str): Calendar identifier. Defaults to 'primary'.
        time_min (str, optional): Start time in RFC3339 format. Defaults to current time if not provided by service.
        time_max (str, optional): End time in RFC3339 format.
        max_results (int): Maximum number of events to return (1-2500). Defaults to 250.
        show_deleted (bool): Whether to include deleted events. Defaults to False.

    Returns:
        str: JSON string containing a list of calendar events.
    """
    logger.info(f"Getting events for user_id: {user_id}, calendar_id: {calendar_id}")
    try:
        calendar_service = calendar.CalendarService(user_id=user_id)
        logger.debug(
            f"CalendarService initialized for user_id: {user_id} for get_events"
        )

        events_list = await asyncio.to_thread(
            calendar_service.get_events,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
            show_deleted=show_deleted,
            calendar_id=calendar_id,
        )

        logger.info(
            f"Successfully retrieved {len(events_list)} events for user_id: {user_id}, calendar_id: {calendar_id}"
        )
        return json.dumps(events_list, indent=2)

    except Exception as e:
        logger.error(
            f"Error in get_events for user_id: {user_id}, calendar_id: {calendar_id}. Error: {str(e)}",
            exc_info=True,
        )
        error_response = {
            "error": f"Failed to get events for {user_id}, calendar_id {calendar_id}: {str(e)}",
            "user_id": user_id,
            "calendar_id": calendar_id,
        }
        raise Exception(json.dumps(error_response, indent=2))
