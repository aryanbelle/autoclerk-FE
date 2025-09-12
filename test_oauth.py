#!/usr/bin/env python3
"""
Test script to verify OAuth setup is working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agent.tools.google_auth import is_authenticated, ALL_SCOPES, get_stored_credentials

def test_oauth_status():
    """Test the current OAuth authentication status"""
    print("🔍 Testing OAuth Authentication Status...")
    print(f"📋 Required scopes: {ALL_SCOPES}")
    
    # Check if authenticated
    authenticated = is_authenticated()
    print(f"✅ Authenticated: {authenticated}")
    
    if authenticated:
        # Get credential details
        creds = get_stored_credentials(ALL_SCOPES)
        if creds:
            print(f"🔑 Token expires at: {creds.expiry}")
            print(f"🔄 Has refresh token: {bool(creds.refresh_token)}")
            print(f"📊 Scopes: {creds.scopes}")
        else:
            print("❌ Could not retrieve credential details")
    else:
        print("🚨 Not authenticated. Please visit http://localhost:8000/oauth/login to authenticate.")
    
    return authenticated

if __name__ == "__main__":
    test_oauth_status()