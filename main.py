from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
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
        # Create agent if not already created
        agent_manager = AgentManager()
        
        # Run the agent with the user's prompt
        response = agent_manager.run(request.prompt)
        
        # If response is empty, return a message indicating the action was completed
        if not response or response.strip() == "":
            return {"response": "Task completed successfully. The requested Google Docs operation was performed."}
        
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))