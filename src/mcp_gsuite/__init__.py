from saaga_mcp_base import logger
from saaga_mcp_base.lib.logging import logger

from mcp_gsuite.tools.gmail.query_emails import query_gmail_emails
from mcp_gsuite.tools.gmail.create_reply import create_reply
from mcp_gsuite.tools.gmail.get_email_by_id_with_attachments import (
    get_email_by_id_with_attachments,
)
from mcp_gsuite.tools.gmail.create_draft import create_draft
from mcp_gsuite.tools.gmail.get_attachment import get_attachment

from mcp_gsuite.tools.calendar.list_calendars import list_calendars
from mcp_gsuite.tools.calendar.get_events import get_events
from mcp_gsuite.tools.calendar.create_event import create_event
from mcp_gsuite.tools.calendar.delete_event import delete_event
from mcp_gsuite.tools.calendar.update_event import update_event
from saaga_mcp_base.base.base_mcp import create_mcp


def main():

    all_tools = [
        query_gmail_emails,
        create_reply,
        get_email_by_id_with_attachments,
        create_draft,
        get_attachment,
        list_calendars,
        get_events,
        create_event,
        delete_event,
        update_event,
    ]

    mcp = create_mcp("mcp_gsuite", tools=all_tools)
    mcp.run(transport="stdio")


# Optionally expose other important items at package level
__all__ = ["main"]
