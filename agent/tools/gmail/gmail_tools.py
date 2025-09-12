# Gmail Tools

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import json
from datetime import datetime

# Import the authentication module
from ..google_auth import authenticate_google_api, GMAIL_SCOPES

# Gmail service will be initialized per request
gmail_service = None

def get_gmail_service():
    """Get Gmail service with current credentials"""
    try:
        creds = authenticate_google_api(GMAIL_SCOPES)
        if creds:
            return build('gmail', 'v1', credentials=creds)
        return None
    except Exception as e:
        print(f"❌ Failed to initialize Gmail service: {str(e)}")
        return None

# Tool Input Schemas
class SendEmailInput(BaseModel):
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body content")
    cc: Optional[str] = Field(None, description="CC email addresses (comma-separated)")
    bcc: Optional[str] = Field(None, description="BCC email addresses (comma-separated)")
    html: bool = Field(False, description="Whether the body is HTML content")

class ReadEmailInput(BaseModel):
    email_id: str = Field(description="Gmail message ID to read")
    format: str = Field("full", description="Message format: 'full', 'metadata', 'minimal', or 'raw'")

class SearchEmailInput(BaseModel):
    query: str = Field(description="Gmail search query (e.g., 'from:example@gmail.com', 'subject:meeting')")
    max_results: int = Field(10, description="Maximum number of emails to return")
    include_spam_trash: bool = Field(False, description="Whether to include spam and trash emails")

class ListEmailsInput(BaseModel):
    max_results: int = Field(10, description="Maximum number of emails to return")
    label_ids: Optional[List[str]] = Field(None, description="Label IDs to filter by (e.g., ['INBOX', 'UNREAD'])")
    query: Optional[str] = Field(None, description="Search query to filter emails")

# Helper functions
def create_message(to, subject, body, cc=None, bcc=None, html=False):
    """Create a message for an email."""
    if html:
        message = MIMEMultipart('alternative')
        text_part = MIMEText(body, 'html')
    else:
        message = MIMEText(body)
        
    if isinstance(message, MIMEMultipart):
        message.attach(text_part)
    
    message['to'] = to
    message['subject'] = subject
    
    if cc:
        message['cc'] = cc
    if bcc:
        message['bcc'] = bcc
    
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def parse_email_headers(headers):
    """Parse email headers into a readable format"""
    header_dict = {}
    for header in headers:
        header_dict[header['name']] = header['value']
    return header_dict

def extract_email_body(payload):
    """Extract email body from Gmail API payload"""
    body = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
            elif part['mimeType'] == 'text/html' and not body:
                if 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    else:
        if payload['mimeType'] == 'text/plain' or payload['mimeType'] == 'text/html':
            if 'data' in payload['body']:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    
    return body

# Gmail Tools Implementation

class SendGmailTool(BaseTool):
    name: str = "send_gmail"
    description: str = "Send an email via Gmail"
    args_schema: Type[BaseModel] = SendEmailInput

    def _run(self, to: str, subject: str, body: str, cc: Optional[str] = None, 
             bcc: Optional[str] = None, html: bool = False):
        try:
            # Get Gmail service with current credentials
            gmail_service = get_gmail_service()
            if gmail_service is None:
                error_message = "Gmail service is not available. Please authenticate first by visiting /oauth/login"
                print(f"❌ {error_message}")
                return error_message
            
            # Create the email message
            message = create_message(to, subject, body, cc, bcc, html)
            
            # Send the email
            result = gmail_service.users().messages().send(
                userId='me', 
                body=message
            ).execute()
            
            message_id = result['id']
            print(f"📧 Email sent successfully. Message ID: {message_id}")
            return f"Email sent successfully to {to}. Subject: '{subject}'. Message ID: {message_id}"
            
        except HttpError as error:
            error_message = f"An error occurred while sending email: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, to: str, subject: str, body: str, cc: Optional[str] = None, 
                    bcc: Optional[str] = None, html: bool = False):
        return self._run(to, subject, body, cc, bcc, html)


class ReadGmailTool(BaseTool):
    name: str = "read_gmail"
    description: str = "Read a specific email by its Gmail message ID"
    args_schema: Type[BaseModel] = ReadEmailInput

    def _run(self, email_id: str, format: str = "full"):
        try:
            # Get Gmail service with current credentials
            gmail_service = get_gmail_service()
            if gmail_service is None:
                error_message = "Gmail service is not available. Please authenticate first by visiting /oauth/login"
                print(f"❌ {error_message}")
                return error_message
            
            # Get the email message
            message = gmail_service.users().messages().get(
                userId='me', 
                id=email_id, 
                format=format
            ).execute()
            
            # Parse the message
            if format == "full":
                headers = parse_email_headers(message['payload']['headers'])
                body = extract_email_body(message['payload'])
                
                formatted_email = f"""
Email ID: {email_id}
From: {headers.get('From', 'Unknown')}
To: {headers.get('To', 'Unknown')}
Subject: {headers.get('Subject', 'No Subject')}
Date: {headers.get('Date', 'Unknown')}

Body:
{body}
                """.strip()
                
                return formatted_email
            else:
                return json.dumps(message, indent=2)
            
        except HttpError as error:
            error_message = f"An error occurred while reading email: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, email_id: str, format: str = "full"):
        return self._run(email_id, format)


class SearchGmailTool(BaseTool):
    name: str = "search_gmail"
    description: str = "Search for emails in Gmail using Gmail search syntax"
    args_schema: Type[BaseModel] = SearchEmailInput

    def _run(self, query: str, max_results: int = 10, include_spam_trash: bool = False):
        try:
            # Get Gmail service with current credentials
            gmail_service = get_gmail_service()
            if gmail_service is None:
                error_message = "Gmail service is not available. Please authenticate first by visiting /oauth/login"
                print(f"❌ {error_message}")
                return error_message
            
            # Search for messages
            results = gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                includeSpamTrash=include_spam_trash
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return f"No emails found matching query: '{query}'"
            
            # Get details for each message
            email_list = []
            for msg in messages:
                message = gmail_service.users().messages().get(
                    userId='me', 
                    id=msg['id'], 
                    format='metadata'
                ).execute()
                
                headers = parse_email_headers(message['payload']['headers'])
                
                email_info = {
                    "id": msg['id'],
                    "from": headers.get('From', 'Unknown'),
                    "subject": headers.get('Subject', 'No Subject'),
                    "date": headers.get('Date', 'Unknown')
                }
                email_list.append(email_info)
            
            # Format the results
            formatted_results = f"Found {len(email_list)} emails matching '{query}':\n\n"
            for i, email in enumerate(email_list, 1):
                formatted_results += f"{i}. ID: {email['id']}\n"
                formatted_results += f"   From: {email['from']}\n"
                formatted_results += f"   Subject: {email['subject']}\n"
                formatted_results += f"   Date: {email['date']}\n\n"
            
            return formatted_results
            
        except HttpError as error:
            error_message = f"An error occurred while searching emails: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, query: str, max_results: int = 10, include_spam_trash: bool = False):
        return self._run(query, max_results, include_spam_trash)


class ListGmailTool(BaseTool):
    name: str = "list_gmail"
    description: str = "List recent emails from Gmail inbox"
    args_schema: Type[BaseModel] = ListEmailsInput

    def _run(self, max_results: int = 10, label_ids: Optional[List[str]] = None, 
             query: Optional[str] = None):
        try:
            # Get Gmail service with current credentials
            gmail_service = get_gmail_service()
            if gmail_service is None:
                error_message = "Gmail service is not available. Please authenticate first by visiting /oauth/login"
                print(f"❌ {error_message}")
                return error_message
            
            # Set default label to INBOX if none provided
            if label_ids is None:
                label_ids = ['INBOX']
            
            # List messages
            results = gmail_service.users().messages().list(
                userId='me',
                labelIds=label_ids,
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return "No emails found in the specified criteria."
            
            # Get details for each message
            email_list = []
            for msg in messages:
                message = gmail_service.users().messages().get(
                    userId='me', 
                    id=msg['id'], 
                    format='metadata'
                ).execute()
                
                headers = parse_email_headers(message['payload']['headers'])
                
                email_info = {
                    "id": msg['id'],
                    "from": headers.get('From', 'Unknown'),
                    "subject": headers.get('Subject', 'No Subject'),
                    "date": headers.get('Date', 'Unknown')
                }
                email_list.append(email_info)
            
            # Format the results
            formatted_results = f"Recent {len(email_list)} emails:\n\n"
            for i, email in enumerate(email_list, 1):
                formatted_results += f"{i}. ID: {email['id']}\n"
                formatted_results += f"   From: {email['from']}\n"
                formatted_results += f"   Subject: {email['subject']}\n"
                formatted_results += f"   Date: {email['date']}\n\n"
            
            return formatted_results
            
        except HttpError as error:
            error_message = f"An error occurred while listing emails: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, max_results: int = 10, label_ids: Optional[List[str]] = None, 
                    query: Optional[str] = None):
        return self._run(max_results, label_ids, query)