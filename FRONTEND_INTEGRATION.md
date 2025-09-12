# Frontend Integration Guide

This guide explains how to integrate the AutoClerk backend OAuth system with your frontend application.

## OAuth Flow Integration

### 1. Check Authentication Status

Before making agent requests, check if the user is authenticated:

```javascript
async function checkAuthStatus() {
  try {
    const response = await fetch('http://localhost:8000/oauth/status');
    const data = await response.json();
    return data.authenticated;
  } catch (error) {
    console.error('Error checking auth status:', error);
    return false;
  }
}
```

### 2. Initiate Authentication

If not authenticated, redirect user to OAuth login:

```javascript
function initiateAuth() {
  // Open OAuth login in a new window or redirect
  window.open('http://localhost:8000/oauth/login', '_blank');
  // Or redirect in same window:
  // window.location.href = 'http://localhost:8000/oauth/login';
}
```

### 3. Handle Agent Requests

The agent endpoint will return authentication requirements if needed:

```javascript
async function sendAgentRequest(prompt) {
  try {
    const response = await fetch('http://localhost:8000/agent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: prompt,
        history: [] // Optional conversation history
      })
    });
    
    const data = await response.json();
    
    // Check if authentication is required
    if (data.requires_auth) {
      // Show authentication prompt to user
      const shouldAuth = confirm(
        'Google services authentication required. Would you like to authenticate now?'
      );
      if (shouldAuth) {
        initiateAuth();
      }
      return data;
    }
    
    return data;
  } catch (error) {
    console.error('Error sending agent request:', error);
    throw error;
  }
}
```

### 4. Complete Frontend Example

```javascript
class AutoClerkClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }
  
  async checkAuth() {
    const response = await fetch(`${this.baseUrl}/oauth/status`);
    return await response.json();
  }
  
  initiateAuth() {
    window.open(`${this.baseUrl}/oauth/login`, '_blank');
  }
  
  async sendMessage(prompt, history = []) {
    const response = await fetch(`${this.baseUrl}/agent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, history })
    });
    
    const data = await response.json();
    
    if (data.requires_auth) {
      throw new Error('Authentication required');
    }
    
    return data.response;
  }
  
  async basicChat(prompt, history = []) {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, history })
    });
    
    const data = await response.json();
    return data.response;
  }
}

// Usage example
const client = new AutoClerkClient();

// Check if authenticated
client.checkAuth().then(status => {
  if (!status.authenticated) {
    console.log('Not authenticated. Auth URL:', status.auth_url);
  }
});

// Send agent message
client.sendMessage('Create a new Google Doc titled "Meeting Notes"')
  .then(response => console.log(response))
  .catch(error => {
    if (error.message === 'Authentication required') {
      client.initiateAuth();
    }
  });
```

## Available Agent Commands

Users can ask the agent to perform various Google Workspace operations:

### Google Docs
- "Create a new Google Doc titled 'Project Plan'"
- "Read the content of document ID: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
- "Update the document with ID xyz to include this content: [content]"
- "Add a comment to document xyz from index 10 to 20 saying 'Please review this section'"
- "Search for documents containing 'budget'"

### Google Sheets
- "Create a new spreadsheet called 'Sales Data' with headers: Date, Product, Amount"
- "Read data from spreadsheet ID xyz, range A1:D10"
- "Update spreadsheet xyz range A1:B2 with values: [['Name', 'Age'], ['John', '25']]"
- "Add a new row to spreadsheet xyz with values: ['2024-01-15', 'Product A', '100']"
- "Search for spreadsheets containing 'budget'"

## Error Handling

The backend provides clear error messages for common issues:

- **Authentication required**: `requires_auth: true` in response
- **API not enabled**: Instructions to enable Google APIs
- **Invalid credentials**: OAuth re-authentication needed
- **Rate limits**: Retry after specified time

## CORS Configuration

The backend is configured to accept requests from any origin during development. For production, update the CORS settings in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```