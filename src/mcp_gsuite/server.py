import logging
import asyncio
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


from . import gauth

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-gsuite")

# Initialize FastMCP server
mcp = FastMCP(
    "mcp-gsuite",
    title="GSuite Tools",
    description="Provides tools to interact with GMail and Google Calendar.",
    version="1.0.0",
)

# Import tool modules AFTER mcp instance is created so they can use @mcp.tool()
# These imports will trigger tool registration if tools are decorated correctly in those files.
from . import tools_gmail
from . import tools_calendar

if __name__ == "__main__":
    logger.info("Starting MCP GSuite Server...")

    accounts = gauth.get_account_info()
    if not accounts:
        logger.warning(
            "No accounts configured in .gauth.json. Users will need to be added there for tools to function correctly."
        )
    else:
        logger.info(
            f"Pre-flight check: Found {len(accounts)} GSuite account(s) configured."
        )
        for account in accounts:
            creds = gauth.get_stored_credentials(user_id=account.email)
            if creds:
                logger.debug(f"Stored credentials found for {account.email}.")
                # Further checks like token expiry could be done here if non-blocking
            else:
                logger.info(
                    f"No stored credentials for {account.email}. OAuth flow may be triggered on first tool use for this account."
                )

    # Run the FastMCP server
    # This is a blocking call that starts the server and listens for requests.
    mcp.run(transport="stdio")
