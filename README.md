# AutoClerk Backend

Backend server for the AutoClerk application, which integrates with Google Docs and uses Groq LLM for document processing.

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your Groq API key to the `.env` file

4. Set up Google API credentials:
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Google Docs API for your project:
     - Go to [Google Cloud Console API Library](https://console.cloud.google.com/apis/library)
     - Search for "Google Docs API"
     - Select the API and click "Enable"
     - Wait a few minutes for the changes to propagate
   - Create OAuth 2.0 credentials (OAuth client ID)
     - Application type: Desktop application
     - Name: AutoClerk (or any name you prefer)
   - Download the credentials as JSON
   - Rename the downloaded file to `client_secret.json` and place it in the `agent` directory
   - When running the application for the first time, you'll be prompted to authorize access
   - After successful authorization, a `token.json` file will be created in the `agent` directory for future use

## Running the Server

```
python main.py
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
