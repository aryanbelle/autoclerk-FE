# Google Docs Tools

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, List, Dict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import the authentication module
from ..google_auth import authenticate_google_api, DOCS_SCOPES

# Initialize Google Docs service
try:
    # Get credentials and build service
    creds = authenticate_google_api(DOCS_SCOPES)
    docs_service = build('docs', 'v1', credentials=creds)
    print("✅ Google Docs service ready!")
except Exception as e:
    print(f"❌ Failed to initialize Google Docs service: {str(e)}")
    docs_service = None

# Tool Input Schemas
class CreateDocInput(BaseModel):
    title: str = Field(description="Title of the new document")
    content: Optional[str] = Field(None, description="Initial content for the doc")

class ReadDocInput(BaseModel):
    document_id: str = Field(description="ID of the Google Document to read")
    include_formatting: bool = Field(False, description="Whether to include formatting information in the response")

class UpdateDocInput(BaseModel):
    document_id: str = Field(description="ID of the Google Document to update")
    content: str = Field(description="Content to append or replace in the document")
    replace_all: bool = Field(False, description="Whether to replace all content or append to the end")

# Input schema for AddCommentGoogleDocTool
class AddCommentInput(BaseModel):
    document_id: str = Field(description="The ID of the Google Document to add a comment to")
    content: str = Field(description="The comment text to add")
    start_index: int = Field(description="The start index of the text to comment on")
    end_index: int = Field(description="The end index of the text to comment on")

# Create Document tool
class CreateGoogleDocTool(BaseTool):
    name: str = "create_google_doc"
    description: str = "Creates a new Google Document"
    args_schema: Type[BaseModel] = CreateDocInput

    def _run(self, title: str, content: Optional[str] = None):
        try:
            # Check if docs_service is available
            if docs_service is None:
                error_message = "Google Docs service is not initialized. Please check authentication."
                print(f"❌ {error_message}")
                return error_message
                
            # Create the document
            doc_body = {"title": title}
            doc = docs_service.documents().create(body=doc_body).execute()
            doc_id = doc['documentId']

            # Add content if provided
            if content:
                requests = [{"insertText": {"location": {"index": 1}, "text": content}}]
                docs_service.documents().batchUpdate(
                    documentId=doc_id, 
                    body={"requests": requests}
                ).execute()
            
            print(f"📄 Created document: {title} (ID: {doc_id})")
            return f"Document created successfully. ID: {doc_id}, Title: {title}"
        except HttpError as error:
            error_message = f"An error occurred while creating the document: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, title: str, content: Optional[str] = None):
        return self._run(title, content)


# Read Document tool
class ReadGoogleDocTool(BaseTool):
    name: str = "read_google_doc"
    description: str = "Reads content from an existing Google Document"
    args_schema: Type[BaseModel] = ReadDocInput

    def _run(self, document_id: str, include_formatting: bool = False):
        try:
            # Check if docs_service is available
            if docs_service is None:
                error_message = "Google Docs service is not initialized. Please check authentication."
                print(f"❌ {error_message}")
                return error_message
                
            # Get the document content
            document = docs_service.documents().get(documentId=document_id).execute()
            
            # Extract the document content
            doc_content = ""
            for content in document.get('body').get('content'):
                if 'paragraph' in content:
                    for element in content.get('paragraph').get('elements'):
                        if 'textRun' in element:
                            doc_content += element.get('textRun').get('content')
            
            # If include_formatting is True, return the raw document object
            if include_formatting:
                return {"content": doc_content, "raw_document": document}
            
            print(f"📄 Read document: {document['title']} (ID: {document_id})")
            return doc_content
        except HttpError as error:
            # Check if this is an API disabled error
            if "SERVICE_DISABLED" in str(error) or "has not been used in project" in str(error):
                error_message = ("The Google Docs API is not enabled for this project. Please enable it by visiting "
                               "the Google Cloud Console (https://console.cloud.google.com/apis/library), "
                               "searching for 'Google Docs API', and clicking 'Enable'. "
                               "After enabling, wait a few minutes before trying again.")
            else:
                error_message = f"An error occurred while reading the document: {error}"
            
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, document_id: str, include_formatting: bool = False):
        return self._run(document_id, include_formatting)


# Update Document tool
class UpdateGoogleDocTool(BaseTool):
    name: str = "update_google_doc"
    description: str = "Updates content in an existing Google Document"
    args_schema: Type[BaseModel] = UpdateDocInput

    def _run(self, document_id: str, content: str, replace_all: bool = False):
        try:
            # Check if docs_service is available
            if docs_service is None:
                error_message = "Google Docs service is not initialized. Please check authentication."
                print(f"❌ {error_message}")
                return error_message
                
            if replace_all:
                # First, get the document to find its current content
                document = docs_service.documents().get(documentId=document_id).execute()
                
                # Calculate the end index (excluding the final newline)
                end_index = 1  # Start at 1 (after the initial position)
                for content_item in document.get('body').get('content'):
                    if 'paragraph' in content_item:
                        for element in content_item.get('paragraph').get('elements'):
                            if 'textRun' in element:
                                end_index += len(element.get('textRun').get('content'))
                
                # Delete all content and then insert new content
                # Make sure we don't include the final newline character in the deletion range
                if end_index > 1:
                    # Adjust end_index to avoid including the final newline character
                    safe_end_index = end_index - 1 if end_index > 1 else 1
                    
                    requests = [
                        # Delete all existing content
                        {"deleteContentRange": {
                            "range": {
                                "startIndex": 1,
                                "endIndex": safe_end_index
                            }
                        }},
                        # Insert new content
                        {"insertText": {
                            "location": {"index": 1},
                            "text": content
                        }}
                    ]
                else:
                    # If document is empty, just insert content
                    requests = [
                        # Insert new content
                        {"insertText": {
                            "location": {"index": 1},
                            "text": content
                        }}
                    ]
            else:
                # Append to the end of the document
                document = docs_service.documents().get(documentId=document_id).execute()
                
                # Get the last content item
                content_items = document.get('body').get('content')
                if content_items and len(content_items) > 0:
                    # Get the end index from the last content item
                    end_index = content_items[-1].get('endIndex', 1)
                    # Make sure we don't go beyond document boundaries
                    safe_index = max(1, end_index - 1)
                else:
                    # If document is empty or has no content items
                    safe_index = 1
                
                requests = [{
                    "insertText": {
                        "location": {"index": safe_index},
                        "text": content
                    }
                }]
            
            # Execute the update
            docs_service.documents().batchUpdate(
                documentId=document_id,
                body={"requests": requests}
            ).execute()
            
            print(f"📄 Updated document (ID: {document_id})")
            return f"Document updated successfully. ID: {document_id}"
        except HttpError as error:
            error_message = f"An error occurred while updating the document: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, document_id: str, content: str, replace_all: bool = False):
        return self._run(document_id, content, replace_all)


# Add Comment tool
class AddCommentGoogleDocTool(BaseTool):
    name: str = "add_comment_google_doc"
    description: str = "Adds a comment to a specific section of text in a Google Document"
    args_schema: Type[BaseModel] = AddCommentInput

    def _run(self, document_id: str, content: str, start_index: int, end_index: int):
        try:
            # Check if docs_service is available
            if docs_service is None:
                error_message = "Google Docs service is not initialized. Please check authentication."
                print(f"❌ {error_message}")
                return error_message
                
            # Create a comment with the given content at the specified range
            requests = [{
                "createComment": {
                    "commentText": content,
                    "range": {
                        "startIndex": start_index,
                        "endIndex": end_index
                    }
                }
            }]
            
            # Execute the update
            result = docs_service.documents().batchUpdate(
                documentId=document_id,
                body={"requests": requests}
            ).execute()
            
            print(f"💬 Added comment to document (ID: {document_id})")
            return f"Comment added successfully to document ID: {document_id}"
        except HttpError as error:
            error_message = f"An error occurred while adding the comment: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, document_id: str, content: str, start_index: int, end_index: int):
        return self._run(document_id, content, start_index, end_index)


# Add this to your imports
from typing import Optional, Type, List, Dict

# Add this input schema class
class SearchDocsInput(BaseModel):
    query: str = Field(description="Search query to find documents by title or content")
    max_results: int = Field(10, description="Maximum number of results to return")

# Add this new tool class
class SearchGoogleDocsTool(BaseTool):
    name: str = "search_google_docs"
    description: str = "Searches for Google Documents by title or content"
    args_schema: Type[BaseModel] = SearchDocsInput

    def _run(self, query: str, max_results: int = 10):
        try:
            # Check if docs_service is available
            if docs_service is None:
                error_message = "Google Docs service is not initialized. Please check authentication."
                print(f"❌ {error_message}")
                return error_message
                
            # Initialize Drive service using the same credentials
            drive_service = build('drive', 'v3', credentials=creds)
            
            # Search for documents
            results = []
            page_token = None
            
            # Format query to search only for Google Docs
            formatted_query = f"name contains '{query}' and mimeType='application/vnd.google-apps.document'"
            
            while True:
                response = drive_service.files().list(
                    q=formatted_query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, createdTime, modifiedTime)',
                    pageToken=page_token,
                    pageSize=min(max_results, 100)  # API limit is 100 per page
                ).execute()
                
                items = response.get('files', [])
                results.extend(items)
                
                # Check if we've reached max_results or end of pages
                if len(results) >= max_results or 'nextPageToken' not in response:
                    break
                    
                page_token = response.get('nextPageToken')
            
            # Limit to max_results
            results = results[:max_results]
            
            if not results:
                return "No documents found matching your search criteria."
            
            # Format results
            formatted_results = []
            for doc in results:
                formatted_results.append({
                    "id": doc['id'],
                    "title": doc['name'],
                    "created": doc.get('createdTime', 'Unknown'),
                    "modified": doc.get('modifiedTime', 'Unknown')
                })
            
            return formatted_results
        except HttpError as error:
            error_message = f"An error occurred while searching for documents: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, query: str, max_results: int = 10):
        return self._run(query, max_results)