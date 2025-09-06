# Google Authentication Module

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import json

# Define scopes for different Google services
DOCS_SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive.readonly']
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.readonly']

def authenticate_google_api(scopes):
    """
    Authenticate with Google API using OAuth2
    
    Args:
        scopes: List of API scopes to request access for
        
    Returns:
        Google OAuth credentials object
    """
    try:
        # Check if we have a token.json file with credentials
        token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'token.json')
        creds = None
        
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_info(
                json.loads(open(token_path).read()), scopes)
        
        # If credentials don't exist or are invalid, run the flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), "client_secret.json"),
                    scopes=scopes
                )
                # Use localhost with a specific port for the redirect
                creds = flow.run_local_server(
                    port=8080, 
                    open_browser=False,
                    success_message="Authentication successful! You may close this window."
                )
            
            # Save the credentials for future runs
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        raise