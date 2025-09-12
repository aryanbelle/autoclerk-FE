#!/usr/bin/env python3
"""
Startup script for AutoClerk backend with OAuth setup instructions
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

def print_startup_info():
    """Print startup information and OAuth setup instructions"""
    print("🚀 Starting AutoClerk Backend Server...")
    print("=" * 60)
    print("📋 OAuth Setup Instructions:")
    print("1. Server will start on http://localhost:8000")
    print("2. To authenticate with Google services:")
    print("   - Visit: http://localhost:8000/oauth/login")
    print("   - Complete the Google OAuth flow")
    print("   - Check status: http://localhost:8000/oauth/status")
    print("3. Once authenticated, you can use all Google tools!")
    print("=" * 60)
    print()

if __name__ == "__main__":
    print_startup_info()
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )