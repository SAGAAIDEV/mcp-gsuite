import json
import asyncio
from typing import Optional
from mcp_gsuite.lib.accounts import format_docstring_with_user_id_arg
from ...lib import gmail
from saaga_mcp_base import logger


@format_docstring_with_user_id_arg
async def query_gmail_emails(
    user_id: str,
    query: Optional[str] = None,  # Or str | None for Python 3.10+
    max_results: int = 100,
) -> str:
    """
    Query Gmail emails based on an optional search query.
    Returns emails in reverse chronological order (newest first).
    Includes metadata like subject and a short summary of the content.

    Args:
        user_id: {user_id_arg}
        query: Gmail search query (optional). Examples:
            - "is:unread"
            - "from:example@gmail.com"
            - "newer_than:2d"
            - "has:attachment"
            If omitted, recent emails are returned.
        max_results: Maximum number of emails to retrieve (1-500, default 100).
    """
    logger.info(
        f"Querying Gmail emails for user_id: {user_id} with query: '{query}' and max_results: {max_results}"
    )
    try:
        gmail_service = gmail.GmailService(user_id=user_id)
        logger.debug(f"GmailService initialized for user_id: {user_id}")

        emails = await asyncio.to_thread(
            gmail_service.query_emails, query=query, max_results=max_results
        )

        if emails is None:
            logger.warning(
                f"No emails found or failed to retrieve for user_id: {user_id}, query: '{query}'"
            )
            return json.dumps(
                {
                    "message": "No emails found or failed to retrieve.",
                    "user_id": user_id,
                    "query": query,
                },
                indent=2,
            )

        logger.info(
            f"Successfully retrieved {len(emails)} emails for user_id: {user_id}, query: '{query}'"
        )
        return json.dumps(emails, indent=2)

    except Exception as e:
        logger.error(
            f"Error in query_gmail_emails for user_id: {user_id}, query: '{query}'. Error: {str(e)}",
            exc_info=True,
        )
        error_message = {"error": f"Failed to query emails for {user_id}: {str(e)}"}
        raise Exception(error_message)
