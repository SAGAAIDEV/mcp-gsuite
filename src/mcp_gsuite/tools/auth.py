from mcp_gsuite.lib.auth.google_auth_flow import authenticate


async def auth():
    creds = authenticate()
    if creds:
        return f"Successfully authenticated {creds.email}"
    else:
        return None
