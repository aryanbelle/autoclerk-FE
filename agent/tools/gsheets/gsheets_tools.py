# Google Sheets Tools

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type, List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import the authentication module
from ..google_auth import authenticate_google_api, SHEETS_SCOPES

# Google Sheets services will be initialized per request
sheets_service = None
drive_service = None

def get_sheets_service():
    """Get Google Sheets service with current credentials"""
    try:
        creds = authenticate_google_api(SHEETS_SCOPES)
        if creds:
            return build('sheets', 'v4', credentials=creds)
        return None
    except Exception as e:
        print(f"❌ Failed to initialize Google Sheets service: {str(e)}")
        return None

def get_drive_service():
    """Get Google Drive service with current credentials"""
    try:
        creds = authenticate_google_api(SHEETS_SCOPES)
        if creds:
            return build('drive', 'v3', credentials=creds)
        return None
    except Exception as e:
        print(f"❌ Failed to initialize Google Drive service: {str(e)}")
        return None

# Tool Input Schemas
class CreateSheetInput(BaseModel):
    title: str = Field(description="Title of the new spreadsheet")
    headers: Optional[List[str]] = Field(None, description="Column headers for the first sheet")

class ReadSheetInput(BaseModel):
    spreadsheet_id: str = Field(description="ID of the Google Spreadsheet to read")
    range: str = Field(description="Range to read in A1 notation, e.g., 'Sheet1!A1:D10'")
    include_headers: bool = Field(True, description="Whether to include headers in the response")

class UpdateSheetInput(BaseModel):
    spreadsheet_id: str = Field(description="ID of the Google Spreadsheet to update")
    range: str = Field(description="Range to update in A1 notation, e.g., 'Sheet1!A1'")
    values: List[List[Any]] = Field(description="Values to update in the spreadsheet as a 2D array")
    raw_input: bool = Field(False, description="Whether the input should be parsed as raw user input")

class AddRowInput(BaseModel):
    spreadsheet_id: str = Field(description="ID of the Google Spreadsheet to update")
    sheet_name: str = Field(description="Name of the sheet to add a row to")
    values: List[Any] = Field(description="Values to add as a new row")

class SearchSheetsInput(BaseModel):
    query: str = Field(description="Search query to find spreadsheets")
    max_results: int = Field(10, description="Maximum number of results to return")

# Create Spreadsheet tool
class CreateGoogleSheetTool(BaseTool):
    name: str = "create_google_sheet"
    description: str = "Creates a new Google Spreadsheet"
    args_schema: Type[BaseModel] = CreateSheetInput

    def _run(self, title: str, headers: Optional[List[str]] = None):
        try:
            # Get sheets service with current credentials
            sheets_service = get_sheets_service()
            if sheets_service is None:
                error_message = "Google Sheets service is not available. Please authenticate first by visiting /oauth/login"
                print(f"❌ {error_message}")
                return error_message
                
            # Create the spreadsheet
            spreadsheet_body = {
                "properties": {"title": title},
                "sheets": [{
                    "properties": {"title": "Sheet1"}
                }]
            }
            spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
            spreadsheet_id = spreadsheet['spreadsheetId']

            # Add headers if provided
            if headers:
                values = [headers]
                body = {
                    'values': values
                }
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range="Sheet1!A1",
                    valueInputOption="RAW",
                    body=body
                ).execute()
            
            print(f"📊 Created spreadsheet: {title} (ID: {spreadsheet_id})")
            return f"Spreadsheet created successfully. ID: {spreadsheet_id}, Title: {title}"
        except HttpError as error:
            error_message = f"An error occurred while creating the spreadsheet: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, title: str, headers: Optional[List[str]] = None):
        return self._run(title, headers)


# Read Spreadsheet tool
class ReadGoogleSheetTool(BaseTool):
    name: str = "read_google_sheet"
    description: str = "Reads content from an existing Google Spreadsheet"
    args_schema: Type[BaseModel] = ReadSheetInput

    def _run(self, spreadsheet_id: str, range: str, include_headers: bool = True):
        try:
            # Get sheets service with current credentials
            sheets_service = get_sheets_service()
            if sheets_service is None:
                error_message = "Google Sheets service is not available. Please authenticate first by visiting /oauth/login"
                print(f"❌ {error_message}")
                return error_message
                
            # Get the spreadsheet content
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return "No data found in the specified range."
            
            # Format the data for better readability
            formatted_data = ""
            
            # Get spreadsheet info
            spreadsheet = sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            spreadsheet_title = spreadsheet.get('properties', {}).get('title', 'Untitled')
            formatted_data += f"Spreadsheet: {spreadsheet_title}\n"
            formatted_data += f"Range: {range}\n\n"
            
            # Format as a table
            if include_headers and len(values) > 1:
                headers = values[0]
                data_rows = values[1:]
                
                # Calculate column widths
                col_widths = [max(len(str(row[i])) if i < len(row) else 0 for row in values) 
                             for i in range(max(len(row) for row in values))]
                
                # Print headers
                header_row = " | ".join(str(headers[i]).ljust(col_widths[i]) if i < len(headers) else "".ljust(col_widths[i]) 
                                      for i in range(len(col_widths)))
                formatted_data += header_row + "\n"
                formatted_data += "-" * len(header_row) + "\n"
                
                # Print data rows
                for row in data_rows:
                    formatted_data += " | ".join(str(row[i]).ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i]) 
                                              for i in range(len(col_widths))) + "\n"
            else:
                # Just print all rows
                for row in values:
                    formatted_data += " | ".join(str(cell) for cell in row) + "\n"
            
            return formatted_data
        except HttpError as error:
            error_message = f"An error occurred while reading the spreadsheet: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, spreadsheet_id: str, range: str, include_headers: bool = True):
        return self._run(spreadsheet_id, range, include_headers)


# Update Spreadsheet tool
class UpdateGoogleSheetTool(BaseTool):
    name: str = "update_google_sheet"
    description: str = "Updates content in an existing Google Spreadsheet"
    args_schema: Type[BaseModel] = UpdateSheetInput

    def _run(self, spreadsheet_id: str, range: str, values: List[List[Any]], raw_input: bool = False):
        try:
            # Get sheets service with current credentials
            sheets_service = get_sheets_service()
            if sheets_service is None:
                error_message = "Google Sheets service is not available. Please authenticate first by visiting /oauth/login"
                print(f"❌ {error_message}")
                return error_message
            
            # Process raw input if needed
            if raw_input and isinstance(values, list) and len(values) == 1 and isinstance(values[0], list) and len(values[0]) == 1:
                # This is likely a raw text input that needs to be parsed
                raw_text = values[0][0]
                if isinstance(raw_text, str):
                    # Split by newlines and then by commas or tabs
                    processed_values = []
                    for line in raw_text.strip().split('\n'):
                        if ',' in line:
                            processed_values.append(line.split(','))
                        elif '\t' in line:
                            processed_values.append(line.split('\t'))
                        else:
                            processed_values.append([line])
                    values = processed_values
            
            body = {
                'values': values
            }
            
            result = sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueInputOption="USER_ENTERED",  # Interpret strings as formulas if they start with =
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            print(f"📝 Updated {updated_cells} cells in spreadsheet {spreadsheet_id}")
            return f"Successfully updated {updated_cells} cells in range {range}."
        except HttpError as error:
            error_message = f"An error occurred while updating the spreadsheet: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, spreadsheet_id: str, range: str, values: List[List[Any]], raw_input: bool = False):
        return self._run(spreadsheet_id, range, values, raw_input)


# Add Row to Spreadsheet tool
class AddRowGoogleSheetTool(BaseTool):
    name: str = "add_row_google_sheet"
    description: str = "Adds a new row to an existing Google Spreadsheet"
    args_schema: Type[BaseModel] = AddRowInput

    def _run(self, spreadsheet_id: str, sheet_name: str, values: List[Any]):
        try:
            # Get sheets service with current credentials
            sheets_service = get_sheets_service()
            if sheets_service is None:
                error_message = "Google Sheets service is not available. Please authenticate first by visiting /oauth/login"
                print(f"❌ {error_message}")
                return error_message
            
            # Get the current data to determine where to add the new row
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}"
            ).execute()
            
            current_values = result.get('values', [])
            next_row = len(current_values) + 1  # Add to the next available row
            
            # Prepare the values for the new row
            body = {
                'values': [values]  # Wrap in a list to make it a row
            }
            
            # Update the spreadsheet with the new row
            result = sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A{next_row}",
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            print(f"➕ Added new row to spreadsheet {spreadsheet_id}, sheet {sheet_name}")
            return f"Successfully added a new row with {updated_cells} cells to sheet {sheet_name}."
        except HttpError as error:
            error_message = f"An error occurred while adding a row to the spreadsheet: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, spreadsheet_id: str, sheet_name: str, values: List[Any]):
        return self._run(spreadsheet_id, sheet_name, values)


# Search Google Sheets tool
class SearchGoogleSheetsTool(BaseTool):
    name: str = "search_google_sheets"
    description: str = "Searches for Google Spreadsheets by name"
    args_schema: Type[BaseModel] = SearchSheetsInput

    def _run(self, query: str, max_results: int = 10):
        try:
            # Get drive service with current credentials
            drive_service = get_drive_service()
            if drive_service is None:
                error_message = "Google Drive service is not available. Please authenticate first by visiting /oauth/login"
                print(f"❌ {error_message}")
                return error_message
            
            # Search for spreadsheets
            query = f"name contains '{query}' and mimeType='application/vnd.google-apps.spreadsheet'"
            results = drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, createdTime, modifiedTime, webViewLink)',
                pageSize=max_results
            ).execute()
            
            items = results.get('files', [])
            
            if not items:
                return f"No spreadsheets found matching '{query}'."
            
            # Format the results
            formatted_results = f"Found {len(items)} spreadsheet(s) matching '{query}':\n\n"
            
            for item in items:
                formatted_results += f"Title: {item['name']}\n"
                formatted_results += f"ID: {item['id']}\n"
                formatted_results += f"Created: {item.get('createdTime', 'Unknown')}\n"
                formatted_results += f"Last Modified: {item.get('modifiedTime', 'Unknown')}\n"
                formatted_results += f"Link: {item.get('webViewLink', 'Not available')}\n\n"
            
            return formatted_results
        except HttpError as error:
            error_message = f"An error occurred while searching for spreadsheets: {error}"
            print(f"❌ {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            print(f"❌ {error_message}")
            return error_message

    async def _arun(self, query: str, max_results: int = 10):
        return self._run(query, max_results)