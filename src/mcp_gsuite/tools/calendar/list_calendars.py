import json
import asyncio
from typing import List, Dict, Any, Optional  # Added Optional for consistency
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import calendar  # calendar service
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def list_calendars(user_id: str) -> str:
    """
    Lists all calendars accessible by the user.

    Args:
        user_id: {user_id_arg}

    Returns:
        str: JSON string containing a list of calendar objects with their metadata.
    """
    logger.info(f"Listing calendars for user_id: {user_id}")
    try:
        calendar_service = calendar.CalendarService(user_id=user_id)
        logger.debug(
            f"CalendarService initialized for user_id: {user_id} for list_calendars"
        )

        calendars_list = await asyncio.to_thread(calendar_service.list_calendars)

        logger.info(
            f"Successfully listed {len(calendars_list)} calendars for user_id: {user_id}"
        )
        return json.dumps(calendars_list, indent=2)

    except Exception as e:
        logger.error(
            f"Error in list_calendars for user_id: {user_id}. Error: {str(e)}",
            exc_info=True,
        )
        # Return a JSON string with error information
        # It's better to raise an exception that the calling framework can catch and handle
        # For now, adhering to the observed pattern of returning JSON errors from create_reply.py
        # but ideally, this would be a custom exception.
        error_response = {
            "error": f"Failed to list calendars for {user_id}: {str(e)}",
            "user_id": user_id,
        }
        # Instead of returning a JSON string, let's raise an exception as in create_reply
        raise Exception(json.dumps(error_response, indent=2))
