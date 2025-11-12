# Fixing "invalid_client" Error for Device Code Authentication

## The Problem

When using device code flow (user authentication), you're getting this error:
```
user_token_acquisition_failed error=invalid_client
```

This happens because your Azure app is configured as a **confidential client** (for app-only auth with secrets) but device code flow requires a **public client** configuration.

## Solution 1: Configure Your Azure App (Recommended for Production)

### Steps:

1. **Open Azure Portal**: https://portal.azure.com

2. **Navigate to Your App Registration**:
   - Search for "App registrations"
   - Find and click on your app

3. **Enable Public Client Flow**:
   - Click **Authentication** in the left menu
   - Scroll down to **Advanced settings**
   - Find **"Allow public client flows"**
   - Toggle it to **Yes**
   - Click **Save** at the top

4. **Add Platform Configuration** (if needed):
   - Still in **Authentication**
   - Click **Add a platform**
   - Choose **Mobile and desktop applications**
   - Check **https://login.microsoftonline.com/common/oauth2/nativeclient**
   - Click **Configure**

5. **Verify API Permissions**:
   - Click **API permissions** in left menu
   - You should have these **delegated** permissions:
     - Microsoft Graph → `User.Read`
     - Microsoft Graph → `Tasks.ReadWrite`
     - Microsoft Graph → `Tasks.ReadWrite.Shared`
     - Microsoft Graph → `Group.Read.All`
   - Click **"Grant admin consent"** if needed

6. **Restart the Server**:
   ```bash
   # The server will automatically restart
   ```

## Solution 2: Use Microsoft Graph Explorer Client (Quick Fix)

Microsoft provides a pre-configured public client that works immediately. This is perfect for development and testing.

### Steps:

1. **Update your `.env` file**:
   ```env
   # Your organization's tenant ID (keep this)
   AZURE_TENANT_ID=your-tenant-id
   
   # Use Microsoft's public client
   USE_GRAPH_EXPLORER_CLIENT=true
   
   # Authentication mode
   USE_DEVICE_CODE_AUTH=true
   ```

2. **Restart the server** - it will now use Microsoft's pre-configured public client

3. **Complete authentication** when prompted

### What This Does:
- Uses Microsoft Graph Explorer's client ID: `de8bc8b5-d9f9-48b1-a8ad-b748da725064`
- This is a well-known public client that Microsoft provides for developers
- Works immediately with any Microsoft 365 account
- Perfect for development and personal use

### Limitations:
- The consent screen will show "Microsoft Graph Explorer" as the app name
- Not suitable for production deployments
- Fine for personal projects and development

## Solution 3: Create a New Public Client App

If you want a fresh start:

1. **Create New App Registration**:
   - Azure Portal → App registrations → New registration
   - Name: "Planner MCP Public Client"
   - Supported account types: "Accounts in this organizational directory only"
   - **Don't** add a redirect URI (not needed for device code)
   - Click **Register**

2. **Configure as Public Client**:
   - Go to **Authentication**
   - **Allow public client flows**: **Yes**
   - Click **Save**

3. **Add API Permissions** (Delegated):
   - API permissions → Add a permission → Microsoft Graph
   - Choose **Delegated permissions**
   - Add:
     - User.Read
     - Tasks.ReadWrite
     - Tasks.ReadWrite.Shared
     - Group.Read.All
   - **Grant admin consent**

4. **Copy Application (client) ID**:
   - Overview page → Application (client) ID
   - Copy this value

5. **Update `.env`**:
   ```env
   AZURE_TENANT_ID=your-tenant-id
   AZURE_CLIENT_ID=<new-client-id>
   USE_DEVICE_CODE_AUTH=true
   USE_GRAPH_EXPLORER_CLIENT=false
   ```

## Recommended Approach

**For your use case (single-user M365 account):**

✅ **Use Solution 2** (Microsoft Graph Explorer client)
- Fastest to set up
- Works immediately
- Perfect for personal use

**For production or team use:**

✅ **Use Solution 1 or 3** (your own Azure app)
- Professional app name in consent screens
- Better control over permissions
- Suitable for distribution

## Testing After Fix

1. **Clear any cached tokens**:
   ```bash
   rm .token_cache.json
   ```

2. **Make a test request**:
   ```bash
   python cli/mcp_cli.py health
   ```

3. **Check the logs** for the device code

4. **Complete authentication** at https://microsoft.com/devicelogin

5. **Verify success**:
   ```bash
   python cli/mcp_cli.py list-tasks --plan-id YOUR_PLAN_ID
   ```

## Common Issues

### Still Getting invalid_client
- Make sure you saved changes in Azure Portal
- Wait 5 minutes for Azure changes to propagate
- Clear browser cache and try again
- Verify tenant ID is correct

### Wrong Tenant Error
- Verify `AZURE_TENANT_ID` matches your M365 organization
- Check tenant ID in Azure Portal → Azure Active Directory → Overview

### Permission Denied
- Grant admin consent for the delegated permissions
- Make sure you're signing in with the correct account

## Environment Variables Summary

### Using Your Own App:
```env
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-app-client-id
USE_DEVICE_CODE_AUTH=true
USE_GRAPH_EXPLORER_CLIENT=false
```

### Using Microsoft Graph Explorer Client:
```env
AZURE_TENANT_ID=your-tenant-id
USE_DEVICE_CODE_AUTH=true
USE_GRAPH_EXPLORER_CLIENT=true
```

### Using App-Only Authentication (requires client secret):
```env
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-app-client-id
AZURE_CLIENT_SECRET=your-client-secret
USE_DEVICE_CODE_AUTH=false
```