from mcp_gsuite.lib.auth.google_auth_flow import authenticate
from mcp_gsuite.lib.auth.utils import get_email_from_credentials


async def auth():
    creds = authenticate()
    if creds:
        email = get_email_from_credentials(creds)
        if email:
            return f"Successfully authenticated {email}"
        else:
            return "Authentication successful, but failed to retrieve email."
    else:
        return None
