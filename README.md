# mcp-gsuite MCP server

[![smithery badge](https://smithery.ai/badge/mcp-gsuite)](https://smithery.ai/server/mcp-gsuite)
MCP server to interact with Google produts.

## Example prompts

Right now, this MCP server supports Gmail and Calendar integration with the following capabilities:

1. General
* Multiple google accounts

2. Gmail
* Get your Gmail user information
* Query emails with flexible search (e.g., unread, from specific senders, date ranges, with attachments)
* Retrieve complete email content by ID
* Create new draft emails with recipients, subject, body and CC options
* Delete draft emails
* Reply to existing emails (can either send immediately or save as draft)
* Retrieve multiple emails at once by their IDs.
* Save multiple attachments from emails to your local system.

3. Calendar
* Manage multiple calendars
* Get calendar events within specified time ranges
* Create calendar events with:
  + Title, start/end times
  + Optional location and description
  + Optional attendees
  + Custom timezone support
  + Notification preferences
* Delete calendar events

Example prompts you can try:

* Retrieve my latest unread messages
* Search my emails from the Scrum Master
* Retrieve all emails from accounting
* Take the email about ABC and summarize it
* Write a nice response to Alice's last email and upload a draft.
* Reply to Bob's email with a Thank you note. Store it as draft

* What do I have on my agenda tomorrow?
* Check my private account's Family agenda for next week
* I need to plan an event with Tim for 2hrs next week. Suggest some time slots.

## Quickstart

### Install

### Installing via Smithery

To install mcp-gsuite for Claude Desktop automatically via [Smithery](https://smithery.ai/server/mcp-gsuite):

```bash
npx -y @smithery/cli install mcp-gsuite --client claude
```

#### Oauth 2

Google Workspace (G Suite) APIs require OAuth2 authorization. Follow these steps to set up authentication:

1. Create OAuth2 Credentials:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Gmail API and Google Calendar API for your project
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Select "Desktop app" or "Web application" as the application type
   - Configure the OAuth consent screen with required information
   - Add authorized redirect URIs (include `http://localhost:4100/code` for local development)

2. Required OAuth2 Scopes:
   

```json
   [
     "openid",
     "https://mail.google.com/",
     "https://www.googleapis.com/auth/calendar",
     "https://www.googleapis.com/auth/userinfo.email"
   ]
```

3. Then create a `.gauth.json` in your working directory with client

```json
{
    "web": {
        "client_id": "$your_client_id",
        "client_secret": "$your_client_secret",
        "redirect_uris": ["http://localhost:4100/code"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}
```

4. Create a `.accounts.json` file with account information

```json
{
    "accounts": [
        {
            "email": "alice@bob.com",
            "account_type": "personal",
            "extra_info": "Additional info that you want to tell Claude: E.g. 'Contains Family Calendar'"
        }
    ]
}
```

You can specifiy multiple accounts. Make sure they have access in your Google Auth app. The `extra_info` field is especially interesting as you can add info here that you want to tell the AI about the account (e.g. whether it has a specific agenda)

Note: When you first execute one of the tools for a specific account, a browser will open, redirect you to Google and ask for your credentials, scope, etc. After a successful login, it stores the credentials in a local file called `.oauth.{email}.json` . Once you are authorized, the refresh token will be used.

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`

On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  

```json
{
  "mcpServers": {
    "mcp-gsuite": {
      "command": "uv",
      "args": [
        "--directory",
        "<dir_to>/mcp-gsuite",
        "run",
        "mcp-gsuite"
      ]
    }
  }
}
```

</details>

<details>
  <summary>Published Servers Configuration</summary>
  

```json
{
  "mcpServers": {
    "mcp-gsuite": {
      "command": "uvx",
      "args": [
        "mcp-gsuite"
      ]
    }
  }
}
```

</details>

### Configuration Options

The MCP server can be configured with several command-line options to specify custom paths for authentication and account information:

* `--gauth-file`: Specifies the path to the `.gauth.json` file containing OAuth2 client configuration. Default is `./.gauth.json`.
* `--accounts-file`: Specifies the path to the `.accounts.json` file containing information about the Google accounts. Default is `./.accounts.json`.
* `--credentials-dir`: Specifies the directory where OAuth credentials are stored after successful authentication. Default is the current working directory with a subdirectory for each account as `.oauth.{email}.json`.

These options allow for flexibility in managing different environments or multiple sets of credentials and accounts, especially useful in development and testing scenarios.

Example usage:

```bash
uv run mcp-gsuite --gauth-file /path/to/custom/.gauth.json --accounts-file /path/to/custom/.accounts.json --credentials-dir /path/to/custom/credentials
```

This configuration is particularly useful when you have multiple instances of the server running with different configurations or when deploying to environments where the default paths are not suitable.

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:

```bash
uv sync
```

2. Build package distributions:

```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:

```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
* Token: `--token` or `UV_PUBLISH_TOKEN`
* Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [ `npm` ](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp-gsuite run mcp-gsuite
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

You can also watch the server logs with this command:

```bash
tail -n 20 -f ~/Library/Logs/Claude/mcp-server-mcp-gsuite.log
```

# Google OAuth 2.0 Authentication Flow Application

This Python application demonstrates how to perform a Google OAuth 2.0 authorization flow for an installed application. It authenticates a user, opens a browser window for consent, and then saves the obtained credentials (token) to a local file for future use.

## Prerequisites

1.  **Python 3.7+**
2.  **Google Cloud Project**:
    *   Create a new project or use an existing one in the [Google Cloud Console](https://console.cloud.google.com/).
    *   **Enable necessary APIs**: For the default scopes (`userinfo.email`, `userinfo.profile`), you generally don't need to enable a specific API, but if you change the scopes (e.g., to access Google Drive), you must enable the corresponding API (e.g., Google Drive API) for your project.
    *   **Configure OAuth Consent Screen**:
        *   Go to "APIs & Services" -> "OAuth consent screen".
        *   Choose "External" or "Internal" user type.
        *   Fill in the application name, user support email, and developer contact information.
        *   You can skip scopes configuration here if you define them in your code, or add them if you prefer.
        *   Add test users if your app is in testing mode and not yet published.
    *   **Create OAuth 2.0 Client ID**:
        *   Go to "APIs & Services" -> "Credentials".
        *   Click "+ CREATE CREDENTIALS" -> "OAuth client ID".
        *   Select "Desktop app" as the Application type.
        *   Give it a name (e.g., "Desktop Client 1").
        *   Click "Create".
        *   A dialog will appear showing your "Client ID" and "Client Secret". **Download the JSON** file by clicking the download icon next to the client ID. This is your `client_secret.json` file.

## Setup

1.  **Clone or Download the Code**:
    Get the `google_auth_flow.py` and `requirements.txt` files.

2.  **Create a Virtual Environment (Recommended)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Environment Variables**:
    You need to set two environment variables before running the script:

    *   `CLIENT_SECRET_FILE`: The **absolute path** to your downloaded `client_secret.json` file.
        ```bash
        # Example for macOS/Linux
        export CLIENT_SECRET_FILE="/path/to/your/client_secret.json"

        # Example for Windows (Command Prompt)
        set CLIENT_SECRET_FILE="C:\path\to\your\client_secret.json"

        # Example for Windows (PowerShell)
        $env:CLIENT_SECRET_FILE="C:\path\to\your\client_secret.json"
        ```

    *   `CREDENTIALS_STORAGE_DIR`: The **absolute path** to a directory where the script will save the `token.json` file (user's credentials). The script will create this directory if it doesn't exist.
        ```bash
        # Example for macOS/Linux
        export CREDENTIALS_STORAGE_DIR="/path/to/your/credentials_storage_dir"

        # Example for Windows (Command Prompt)
        set CREDENTIALS_STORAGE_DIR="C:\path\to\your\credentials_storage_dir"

        # Example for Windows (PowerShell)
        $env:CREDENTIALS_STORAGE_DIR="C:\path\to\your\credentials_storage_dir"
        ```
        Ensure this directory is writable by the user running the script.

## Running the Application

Once the setup is complete and environment variables are set, run the Python script:

```bash
python google_auth_flow.py
```

**First Run**:
*   The script will print a message indicating that it needs to perform authentication.
*   It will attempt to open a new tab in your default web browser.
*   You will be prompted to choose a Google account and grant the requested permissions (scopes) to your application.
*   After you grant permission, the browser tab may close automatically, or show an "Authentication successful" message. Control will return to the script.
*   The script will then save the obtained credentials (access token and refresh token) into a file named `token.json` inside the directory specified by `CREDENTIALS_STORAGE_DIR`.

**Subsequent Runs**:
*   The script will first try to load the saved credentials from `token.json`.
*   If the credentials are valid and not expired, it will use them directly, and you won't need to go through the browser authentication flow again.
*   If the credentials have expired but a refresh token is available, the script will attempt to refresh them automatically.
*   If credentials are not found, invalid, or cannot be refreshed, the browser-based authentication flow will be initiated again.

## Customizing Scopes

The default scopes requested are for user email and profile information:
```python
DEFAULT_SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]
```
To request different permissions, modify the `DEFAULT_SCOPES` list in `google_auth_flow.py` or pass a custom list of scopes to the `authenticate()` function.

Example for read-only access to Google Drive:
```python
custom_scopes = ['https://www.googleapis.com/auth/drive.readonly']
credentials = authenticate(scopes=custom_scopes)
```
Make sure that the APIs corresponding to your requested scopes are enabled in your Google Cloud Project.

## Troubleshooting

*   **`Error: Environment variable CLIENT_SECRET_FILE is not set.`**: Ensure you have set this environment variable to the correct path of your `client_secret.json` file.
*   **`Error: Environment variable CREDENTIALS_STORAGE_DIR is not set.`**: Ensure you have set this environment variable to the desired directory path for storing `token.json`.
*   **`Error: Client secret file not found at ...`**: Double-check the path provided in `CLIENT_SECRET_FILE`.
*   **`Error during authentication flow: ...`**: This can have various causes:
    *   The API for the requested scope might not be enabled in your Google Cloud project.
    *   The OAuth consent screen might not be configured correctly.
    *   Issues with redirect URIs (though `InstalledAppFlow` usually handles this well for desktop apps).
    *   Network issues.
*   **Permissions errors when saving `token.json`**: Ensure the directory specified by `CREDENTIALS_STORAGE_DIR` is writable.

Refer to the [Google Cloud Console](https://console.cloud.google.com/) and the [Google API Client Libraries documentation](https://developers.google.com/api-client-library) for more detailed help.
