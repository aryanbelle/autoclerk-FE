# AutoClerk Backend

Backend server for the AutoClerk application with Google Workspace integration (Docs, Sheets, Gmail) and Groq LLM for intelligent document processing.

## Features

- 🤖 AI-powered chat with Groq LLM
- 📄 Google Docs integration (create, read, update, comment, search)
- 📊 Google Sheets integration (create, read, update, add rows, search)
- 📧 Gmail integration (coming soon)
- 🔐 OAuth 2.0 authentication for Google services
- 🛠️ Agent-based tool system for complex workflows

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Add your Groq API key to the .env file
   ```

3. **Start the server:**
   ```bash
   python start_server.py
   ```

4. **Authenticate with Google:**
   - Visit: http://localhost:8000/oauth/login
   - Complete the Google OAuth flow
   - Check status: http://localhost:8000/oauth/status

## OAuth Setup (Already Configured)

The OAuth setup is already configured with the necessary credentials. The system will:

1. **Automatically handle authentication** when you visit `/oauth/login`
2. **Store credentials securely** in `token.json` for future use
3. **Refresh tokens automatically** when they expire
4. **Support all required scopes** for Docs, Sheets, and Gmail

### Required Google APIs

The following APIs are enabled for this project:
- Google Docs API
- Google Sheets API
- Google Drive API (for file operations)
- Gmail API (for future email features)

## API Endpoints

### Core Endpoints
- `POST /chat` - Basic chat with Groq LLM
- `POST /agent` - Agent chat with Google tools access
- `POST /upload-document` - Document analysis

### OAuth Endpoints
- `GET /oauth/login` - Initiate Google OAuth flow
- `GET /oauth/callback` - OAuth callback handler
- `GET /oauth/status` - Check authentication status

## Available Agent Tools

### Google Docs Tools
- `create_google_doc` - Create new documents
- `read_google_doc` - Read document content
- `update_google_doc` - Update document content
- `add_comment_google_doc` - Add comments to documents
- `search_google_docs` - Search for documents

### Google Sheets Tools
- `create_google_sheet` - Create new spreadsheets
- `read_google_sheet` - Read spreadsheet data
- `update_google_sheet` - Update spreadsheet content
- `add_row_google_sheet` - Add new rows
- `search_google_sheets` - Search for spreadsheets

## Testing OAuth

Run the test script to check your authentication status:
```bash
python test_oauth.py
```

## Features

- Create Google Docs through the API
- More features coming soon

## Troubleshooting

### OAuth Authentication Issues

- **CSRF Warning / Mismatching State Error**: If you encounter a "CSRF Warning! State not equal in request and response" error, try the following:
  - Clear your browser cookies for localhost
  - Delete the `token.json` file in the `agent` directory and try again
  - Ensure you're using the correct port (8080) for the redirect
  - Check that your system time is accurate

- **Invalid Client Secret**: Ensure your `client_secret.json` file is correctly formatted and placed in the `agent` directory

- **API Not Enabled**: If you see an error like "Google Docs API has not been used in project ... before or it is disabled", follow these steps:
  - Click on the link provided in the error message, or go to the [Google Cloud Console](https://console.cloud.google.com/)
  - Navigate to APIs & Services > Library
  - Search for "Google Docs API"
  - Select the API and click "Enable"
  - Wait a few minutes for the changes to propagate before trying again# autoclerk-FE
# autoclerk-FE
