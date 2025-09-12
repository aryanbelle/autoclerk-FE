# 🔧 Fix OAuth redirect_uri_mismatch Error

## The Problem
You're getting a "redirect_uri_mismatch" error because the redirect URI in our OAuth flow doesn't match what's configured in Google Cloud Console.

## Solution: Update Google Cloud Console

### Step 1: Access Google Cloud Console
1. Go to: https://console.cloud.google.com/
2. Select project: **gm-hackathon-466212**

### Step 2: Navigate to OAuth Settings
1. Click on "APIs & Services" in the left sidebar
2. Click on "Credentials"
3. Find your OAuth 2.0 Client ID with this ID: `528066670140-1r8snos2jjulkt694j60n47o0dfmu1nc`
4. Click on the pencil icon (✏️) to edit it

### Step 3: Add Authorized Redirect URIs
In the "Authorized redirect URIs" section, add these exact URIs:

```
http://localhost:8000/oauth/callback
http://localhost:8080/
```

**Important:** Make sure there are no extra spaces or trailing slashes (except for the localhost:8080/ one)

### Step 4: Save Changes
1. Click "Save" at the bottom
2. Wait a few minutes for changes to propagate

## Test the Fix

After updating the Google Cloud Console:

1. **Start the server:**
   ```bash
   python start_server.py
   ```

2. **Test authentication:**
   - Visit: http://localhost:8000/oauth/login
   - You should be redirected to Google's OAuth page
   - After granting permissions, you should be redirected back successfully

3. **Verify it worked:**
   ```bash
   python test_oauth.py
   ```

## Alternative: Use Existing Redirect URI

If you can't modify the Google Cloud Console, check what redirect URIs are already configured:

1. In Google Cloud Console → APIs & Services → Credentials
2. Click on your OAuth client
3. Look at the "Authorized redirect URIs" section
4. Let me know what URIs are listed there, and I can update our code to match

## Common Issues

- **Still getting the error?** Clear your browser cache and try again
- **Different port?** Make sure the server is running on port 8000
- **Firewall issues?** Ensure localhost:8000 is accessible

## Need Help?

If you're still having issues, please share:
1. What redirect URIs are currently configured in Google Cloud Console
2. The exact error message you're seeing
3. Which URL you're visiting to start the OAuth flow