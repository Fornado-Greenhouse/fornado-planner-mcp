# Azure Permissions Fix Guide for Microsoft Planner MCP

## Current Issue

Your Azure app registration is missing the required permissions to access Planner data using application-only authentication.

### Error: 404 Not Found
This occurs because the app doesn't have permission to access Planner resources, even though it's authenticated.

## Required Permissions

For **Application-Only Authentication** (what we're using), you need:

| Permission | Type | Description |
|------------|------|-------------|
| `Tasks.Read.All` | Application | Read all Planner tasks in the organization |
| `Tasks.ReadWrite.All` | Application | Read and write all Planner tasks |
| `Group.Read.All` | Application | Read all groups (already configured) |

## Step-by-Step Fix

### 1. Open Azure Portal
Go to https://portal.azure.com

### 2. Navigate to Your App Registration
- Search for "App registrations"
- Find your application

### 3. Add the Required Permissions
1. Click on **"API permissions"** in the left menu
2. Click **"Add a permission"**
3. Select **"Microsoft Graph"**
4. Choose **"Application permissions"**
5. Search for and add:
   - `Tasks.Read.All` (under Tasks)
   - `Tasks.ReadWrite.All` (under Tasks)
6. Click **"Add permissions"**

### 4. Grant Admin Consent
**IMPORTANT:** After adding permissions:
1. Click the **"Grant admin consent for [Your Organization]"** button
2. Confirm the action

### 5. Verify Permissions
Your API permissions should now show:
- ✅ Group.Read.All (Application) - Status: Granted
- ✅ Tasks.Read.All (Application) - Status: Granted  
- ✅ Tasks.ReadWrite.All (Application) - Status: Granted

## Alternative: Use Delegated Authentication

If you can't get application permissions approved, you can switch to delegated (user) authentication:

### Required Delegated Permissions
| Permission | Description |
|------------|-------------|
| `Tasks.ReadWrite` | Read and write user's tasks |
| `Tasks.ReadWrite.Shared` | Read and write shared tasks |
| `Group.Read.All` | Read all groups |

### Code Changes Needed
This would require modifying the authentication to use OAuth 2.0 authorization code flow instead of client credentials.

## Testing After Fix

Once permissions are granted:

1. Restart the server:
   ```bash
   # Restart both servers to pick up new permissions
   ```

2. Test with your plan ID:
   ```bash
   python cli/mcp_cli.py list-tasks --plan-id sjb7tRkv80mTqCHuvLvoLmUADN9o
   ```

## Troubleshooting

### Still Getting 404?
- The plan ID might be incorrect
- Try discovering plans through groups:
  ```bash
  python cli/mcp_cli.py list-groups
  python cli/mcp_cli.py list-group-plans --group-id <GROUP_ID>
  ```

### Getting 403 Forbidden?
- Admin consent wasn't granted
- Permissions haven't propagated (wait 5-10 minutes)

### No Groups Showing?
- Your organization might not have Microsoft 365 Groups with Planner
- The app might need to be added to specific groups

## Important Notes

1. **Planner Application Permissions are New**: These were added in 2023 and may not be available in all tenants
2. **Admin Consent Required**: All Planner permissions require admin consent
3. **Propagation Time**: After granting permissions, it may take 5-10 minutes to take effect

## Next Steps

After fixing permissions:
1. Your server will be able to access all Planner data in your organization
2. You can list groups, plans, tasks, and create/update tasks
3. The MCP server will work with any MCP-compatible client