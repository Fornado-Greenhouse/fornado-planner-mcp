# User Authentication Guide

## Overview

The Microsoft Planner MCP Server now uses **delegated user authentication** via OAuth 2.0 Device Code Flow. This allows you to access your personal Planner data without needing Azure app permissions.

## Why Device Code Authentication?

- ✅ Works for **single-user** Microsoft 365 accounts
- ✅ No need for complex Azure permission setup
- ✅ Access your **personal** Planner tasks and plans
- ✅ Perfect for personal projects and development

## How It Works

### First Time Setup

1. **Start the server** (it starts automatically in Replit)
2. **Make any CLI request** - this triggers authentication:
   ```bash
   python cli/mcp_cli.py health
   ```

3. **Check the HTTP Test Server logs** in Replit
   - You'll see a message like:
   ```
   ============================================================
   MICROSOFT AUTHENTICATION REQUIRED
   ============================================================
   To sign in, use a web browser to open the page 
   https://microsoft.com/devicelogin 
   and enter the code ABC123XYZ to authenticate.
   ============================================================
   ```

4. **Complete Authentication:**
   - Open https://microsoft.com/devicelogin in your browser
   - Enter the code shown in the logs
   - Sign in with your Microsoft account (alex@fornado.onmicrosoft.com)
   - Approve the requested permissions
   - Wait for confirmation

5. **Authentication Complete!**
   - The server receives your token
   - Token is cached in `.token_cache.json` (git-ignored)
   - Future requests use the cached token
   - No re-authentication needed until token expires

### Cached Authentication

After first authentication:
- Tokens are cached for **1 hour**
- The server automatically refreshes tokens
- You won't see the device code prompt again
- Re-authentication only needed when cache expires or is cleared

### Required Permissions

The app requests these delegated permissions:
- `Tasks.ReadWrite` - Read and write your Planner tasks
- `Tasks.ReadWrite.Shared` - Access shared Planner tasks
- `Group.Read.All` - Read Microsoft 365 Groups
- `User.Read` - Read your basic profile

These are **user permissions** - they only access data you already have access to.

## Configuration

In your `.env` file:

```env
# Azure AD Configuration
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-app-client-id

# Authentication Mode
USE_DEVICE_CODE_AUTH=true  # Use user authentication (default)

# Optional: For app-only authentication (requires permissions)
# USE_DEVICE_CODE_AUTH=false
# AZURE_CLIENT_SECRET=your-client-secret
```

## Troubleshooting

### "Authentication Required" Every Time
**Cause:** Token cache is being cleared or not saving
**Solution:** 
- Check file permissions on `.token_cache.json`
- Ensure `.token_cache.json` is in `.gitignore`
- Check server logs for cache errors

### "Invalid Client" Error
**Cause:** App not registered properly in Azure
**Solution:**
- Verify `AZURE_TENANT_ID` matches your M365 organization
- Verify `AZURE_CLIENT_ID` is correct
- Ensure app is registered as a "Public client" in Azure Portal

### Device Code Expired
**Cause:** Took too long to complete authentication
**Solution:**
- Device codes expire in 15 minutes
- Make another request to get a new code
- Complete authentication promptly

### Permission Denied
**Cause:** App doesn't have required API permissions configured
**Solution:**
- Go to Azure Portal → App Registration
- Add Microsoft Graph delegated permissions:
  - Tasks.ReadWrite
  - Tasks.ReadWrite.Shared
  - Group.Read.All
  - User.Read

## Testing Authentication

```bash
# Check if server is authenticated
python cli/mcp_cli.py health

# This should show:
# ✅ Server is running and authenticated!
```

## Clearing Authentication

To sign in with a different account or force re-authentication:

```bash
# Delete the token cache
rm .token_cache.json

# Next request will prompt for authentication again
python cli/mcp_cli.py health
```

## For Production Use

For production deployments:
1. Use a service account with application permissions (not device code)
2. Set `USE_DEVICE_CODE_AUTH=false`
3. Provide `AZURE_CLIENT_SECRET`
4. Grant admin consent for application permissions

Device code flow is intended for:
- Development and testing
- Personal projects
- Single-user scenarios
- Interactive CLI tools