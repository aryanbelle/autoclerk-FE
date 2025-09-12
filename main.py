from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
import os
from dotenv import load_dotenv
from groq import Groq
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel
import shutil
from fastapi import File, UploadFile, HTTPException

# Import agent
from agent import create_agent, AgentManager

# Import OAuth utilities
from agent.tools.google_auth import (
    create_oauth_flow, 
    save_credentials, 
    is_authenticated, 
    ALL_SCOPES,
    get_stored_credentials
)

load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env')

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise RuntimeError("GROQ_API_KEY environment variable is not set")
client = Groq(api_key=groq_api_key)



class ChatRequest(BaseModel):
    prompt: str
    history: List[Dict[str, str]] = []



@app.post("/chat")
async def chat_with_llm(request: ChatRequest):
    try:
        messages = [
            {
                "role": "system",
                "content": "You are Autoclerk, a friendly AI assistant specialized in finance and office automation. "
            }
        ] + request.history + [
            {
                "role": "user",
                "content": request.prompt,
            }
        ]

        chat_completion = client.chat.completions.create(
            messages=messages,
            # model="llama3-70b-8192",  # Still using Llama model but with Autoclerk identity
            model="openai/gpt-oss-20b"
        )
        return {"response": chat_completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Validate file type
        allowed_types = ["text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="File type not supported")

        # Read file content
        content = await file.read()
        
        # For text files, decode directly
        if file.content_type == "text/plain":
            content = content.decode("utf-8")
        # For other types, you would need appropriate parsing logic
        
        # Send the document content to the AI for analysis
        messages = [
            {
                "role": "system",
                "content": "You are Autoclerk, an AI assistant specialized in document analysis. Summarize the provided document."
            },
            {
                "role": "user",
                "content": f"Analyze the following document: {content[:10000]}"  # Limit content size
            }
        ]

        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="openai/gpt-oss-20b"
            )
            return {"response": chat_completion.choices[0].message.content}
        except Exception as ai_e:
            print(f"Error from AI model: {ai_e}")
            raise HTTPException(status_code=500, detail=f"AI model error: {str(ai_e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/agent")
async def agent_chat(request: ChatRequest):
    """
    Endpoint for interacting with the agent that has access to tools.
    """
    try:
        # Check if user is authenticated for Google services
        if not is_authenticated():
            return {
                "response": "To use Google services (Docs, Sheets, Gmail), please authenticate first by visiting: http://localhost:8000/oauth/login",
                "requires_auth": True,
                "auth_url": "http://localhost:8000/oauth/login"
            }
        
        # Create agent if not already created
        agent_manager = AgentManager()
        
        # Run the agent with the user's prompt
        response = agent_manager.run(request.prompt)
        
        # If response is empty, return a message indicating the action was completed
        if not response or response.strip() == "":
            return {"response": "Task completed successfully. The requested operation was performed."}
        
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/oauth/login")
async def oauth_login():
    """
    Initiate OAuth flow for Google services
    """
    try:
        # Create OAuth flow with explicit redirect URI
        flow = create_oauth_flow(ALL_SCOPES, redirect_uri='http://localhost:8000/oauth/callback')
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # In a production app, you'd store the state in a session
        # For now, we'll redirect directly
        return RedirectResponse(url=authorization_url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth initialization failed: {str(e)}")

@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    """
    Handle OAuth callback from Google
    """
    try:
        # Get the authorization code from the callback
        code = request.query_params.get('code')
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not found")
        
        # Create OAuth flow with the same redirect URI used in login
        flow = create_oauth_flow(ALL_SCOPES, redirect_uri='http://localhost:8000/oauth/callback')
        
        # Exchange authorization code for credentials
        flow.fetch_token(code=code)
        
        # Save credentials
        save_credentials(flow.credentials)
        
        # Return success page
        return """
        <html>
            <head><title>Authentication Success</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: green;">✅ Authentication Successful!</h1>
                <p>You can now close this window and use Google services in AutoClerk.</p>
                <script>
                    // Try to close the window after 3 seconds
                    setTimeout(() => {
                        window.close();
                    }, 3000);
                </script>
            </body>
        </html>
        """
        
    except Exception as e:
        return f"""
        <html>
            <head><title>Authentication Error</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">❌ Authentication Failed</h1>
                <p>Error: {str(e)}</p>
                <p>Please try again or contact support.</p>
            </body>
        </html>
        """

@app.get("/oauth/status")
async def oauth_status():
    """
    Check OAuth authentication status
    """
    try:
        authenticated = is_authenticated()
        
        if authenticated:
            # Get some basic info about the stored credentials
            creds = get_stored_credentials(ALL_SCOPES)
            return {
                "authenticated": True,
                "scopes": ALL_SCOPES,
                "expires_at": creds.expiry.isoformat() if creds.expiry else None
            }
        else:
            return {
                "authenticated": False,
                "auth_url": "http://localhost:8000/oauth/login"
            }
            
    except Exception as e:
        return {
            "authenticated": False,
            "error": str(e),
            "auth_url": "http://localhost:8000/oauth/login"
        }

@app.get("/oauth/debug")
async def oauth_debug():
    """
    Debug OAuth configuration
    """
    try:
        from agent.tools.google_auth import get_client_secrets_path
        import json
        
        # Read client secrets
        with open(get_client_secrets_path(), 'r') as f:
            client_config = json.load(f)
        
        return {
            "client_id": client_config['web']['client_id'],
            "project_id": client_config['web']['project_id'],
            "configured_redirect_uris": client_config['web']['redirect_uris'],
            "current_redirect_uri": "http://localhost:8000/oauth/callback",
            "auth_url": "http://localhost:8000/oauth/login",
            "required_scopes": ALL_SCOPES
        }
    except Exception as e:
        return {"error": str(e)}