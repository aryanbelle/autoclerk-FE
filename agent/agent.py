# Agent Setup Module

from langchain_groq import ChatGroq
from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from typing import List, Optional
import os
from dotenv import load_dotenv

# Import tools
from .tools.gdocs import (
    CreateGoogleDocTool,
    ReadGoogleDocTool,
    UpdateGoogleDocTool,
    AddCommentGoogleDocTool,
    SearchGoogleDocsTool
)

from .tools.gsheets import (
    CreateGoogleSheetTool,
    ReadGoogleSheetTool,
    UpdateGoogleSheetTool,
    AddRowGoogleSheetTool,
    SearchGoogleSheetsTool
)

from .tools.gmail import (
    SendGmailTool,
    ReadGmailTool,
    SearchGmailTool,
    ListGmailTool
)

# Load environment variables
load_dotenv()

class AgentManager:
    """
    Manages the setup and configuration of the LLM agent and its tools.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "llama-3.3-70b-versatile"):
        """
        Initialize the agent manager.
        
        Args:
            api_key: Groq API key (if not provided, will look for GROQ_API_KEY in environment)
            model_name: Model name to use for the LLM
        """
        # Get API key from environment if not provided
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not provided and GROQ_API_KEY not found in environment")
            
        # Initialize LLM
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=model_name
        )
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize agent
        self.agent = self._initialize_agent()
    
    # Import statements are already at the top of the file
    
    # Then in the _initialize_tools method, add the new tool
    def _initialize_tools(self) -> List[BaseTool]:
        """
        Initialize all available tools.
        
        Returns:
            List of initialized tools
        """
        tools = [
            # Google Docs tools
            CreateGoogleDocTool(),
            ReadGoogleDocTool(),
            UpdateGoogleDocTool(),
            AddCommentGoogleDocTool(),
            SearchGoogleDocsTool(),
            
            # Google Sheets tools
            CreateGoogleSheetTool(),
            ReadGoogleSheetTool(),
            UpdateGoogleSheetTool(),
            AddRowGoogleSheetTool(),
            SearchGoogleSheetsTool(),
            
            # Gmail tools
            SendGmailTool(),
            ReadGmailTool(),
            SearchGmailTool(),
            ListGmailTool(),
        ]
        
        return tools
    
    def _initialize_agent(self):
        """
        Initialize the agent with the LLM and tools.
        
        Returns:
            Initialized agent
        """
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
    
    def run(self, input_text: str):
        """
        Run the agent with the given input.
        
        Args:
            input_text: User input text
            
        Returns:
            Agent response
        """
        return self.agent.run(input_text)

# Create a default agent instance
def create_agent(api_key: Optional[str] = None, model_name: str = "llama-3.3-70b-versatile"):
    """
    Create and return a configured agent.
    
    Args:
        api_key: Groq API key (if not provided, will look for GROQ_API_KEY in environment)
        model_name: Model name to use for the LLM
        
    Returns:
        Initialized agent
    """
    agent_manager = AgentManager(api_key=api_key, model_name=model_name)
    return agent_manager.agent