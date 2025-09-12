# Google Authentication Module

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import json
from typing import Optional, List

# Define scopes for different Google services
DOCS_SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive.readonly']
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.readonly']

# Combined scopes for all services
ALL_SCOPES = list(set(DOCS_SCOPES + GMAIL_SCOPES + SHEETS_SCOPES))

def get_credentials_path():
    """Get the path to the credentials file"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'token.json')

def get_client_secrets_path():
    """Get the path to the client secrets file"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'client_secret.json')

def get_stored_credentials(scopes: List[str]) -> Optional[Credentials]:
    """
    Get stored credentials if they exist and are valid
    
    Args:
        scopes: List of API scopes to check
        
    Returns:
        Valid credentials or None
    """
    token_path = get_credentials_path()
    
    if not os.path.exists(token_path):
        return None
        
    try:
        with open(token_path, 'r') as token_file:
            creds_data = json.load(token_file)
            creds = Credentials.from_authorized_user_info(creds_data, scopes)
            
        # Check if credentials are valid
        if creds and creds.valid:
            return creds
            
        # Try to refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed credentials
                save_credentials(creds)
                return creds
            except Exception as e:
                print(f"Failed to refresh credentials: {e}")
                return None
                
    except Exception as e:
        print(f"Error loading stored credentials: {e}")
        return None
    
    return None

def save_credentials(creds: Credentials):
    """Save credentials to file"""
    token_path = get_credentials_path()
    with open(token_path, 'w') as token_file:
        token_file.write(creds.to_json())

def create_oauth_flow(scopes: List[str], redirect_uri: str = 'http://localhost:8080/'):
    """
    Create OAuth flow for web application
    
    Args:
        scopes: List of API scopes to request
        redirect_uri: OAuth redirect URI
        
    Returns:
        OAuth flow object
    """
    client_secrets_path = get_client_secrets_path()
    
    flow = Flow.from_client_secrets_file(
        client_secrets_path,
        scopes=scopes
    )
    flow.redirect_uri = redirect_uri
    
    return flow

def authenticate_google_api(scopes: List[str]) -> Optional[Credentials]:
    """
    Get Google API credentials, checking stored credentials first
    
    Args:
        scopes: List of API scopes to request access for
        
    Returns:
        Google OAuth credentials object or None if not authenticated
    """
    try:
        # First, try to get stored credentials
        creds = get_stored_credentials(scopes)
        if creds:
            return creds
            
        # If no valid stored credentials, return None
        # The frontend will need to initiate the OAuth flow
        print("No valid credentials found. OAuth flow needs to be initiated.")
        return None
        
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return None

def is_authenticated(scopes: List[str] = None) -> bool:
    """
    Check if user is authenticated for the given scopes
    
    Args:
        scopes: List of API scopes to check (defaults to ALL_SCOPES)
        
    Returns:
        True if authenticated, False otherwise
    """
    if scopes is None:
        scopes = ALL_SCOPES
        
    creds = get_stored_credentials(scopes)
    return creds is not None