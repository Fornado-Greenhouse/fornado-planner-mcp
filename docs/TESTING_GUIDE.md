# Testing Guide - Microsoft Planner MCP Server

## Overview

This project includes two servers:
1. **MCP Server** - The main MCP protocol server for integration with MCP clients
2. **HTTP Test Server** - A REST API server for testing with the CLI

## Current Status ✅

Both servers are running and successfully authenticated with your Azure credentials:
- MCP Server: Running on stdio transport
- HTTP Test Server: Running on http://localhost:8080

## Testing with the CLI

### 1. First, Check Server Health

```bash
# Check if the server is running and authenticated
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "running",
  "services_initialized": true,
  "azure_configured": true
}
```

### 2. Finding Your Plan IDs

You need real Plan IDs from your Microsoft Planner. Here's how to find them:

#### Option A: Using Microsoft Graph Explorer

1. Go to https://developer.microsoft.com/en-us/graph/graph-explorer
2. Sign in with your Microsoft 365 account
3. Run this query: `GET https://graph.microsoft.com/v1.0/me/planner/tasks`
4. Look for the `planId` field in any task

#### Option B: Using Microsoft Planner Web

1. Open Microsoft Planner in your browser
2. Open a plan
3. The URL will contain the plan ID after `/plans/`
   Example: `https://tasks.office.com/xxx.onmicrosoft.com/Home/PlanViews/PLAN_ID_HERE`

#### Option C: List Plans for a Group

If you know a Microsoft 365 Group ID:
```bash
# Replace GROUP_ID with your actual group ID
curl http://localhost:8080/planner/groups/GROUP_ID/plans
```

### 3. Testing with Real Plan IDs

Once you have a valid plan ID, test the CLI:

```bash
# Replace REAL_PLAN_ID with your actual plan ID
python cli/mcp_cli.py list-tasks --plan-id REAL_PLAN_ID

# Get plan details
python cli/mcp_cli.py get-plan --plan-id REAL_PLAN_ID

# Create a test task
python cli/mcp_cli.py create-task --plan-id REAL_PLAN_ID --title "Test Task from MCP"
```

## Common Issues and Solutions

### Error: "Resource not found"
**Cause:** Invalid plan ID
**Solution:** Use a real plan ID from your Microsoft Planner

### Error: "Connection refused"
**Cause:** HTTP test server not running
**Solution:** Check that the HTTP Test Server workflow is running

### Error: "Authentication failed"
**Cause:** Invalid or expired Azure credentials
**Solution:** Check your `.env` file and ensure credentials are correct

## Quick Test Commands

```bash
# 1. Health check
curl http://localhost:8080/health

# 2. Test with a real plan (replace PLAN_ID)
curl http://localhost:8080/planner/plans/PLAN_ID

# 3. List tasks (replace PLAN_ID)
curl http://localhost:8080/planner/plans/PLAN_ID/tasks

# 4. List buckets (replace PLAN_ID)
curl http://localhost:8080/planner/plans/PLAN_ID/buckets
```

## Using the MCP Server

The MCP server is designed to be used with MCP-compatible clients, not directly via HTTP. To use it:

1. Connect your MCP client to the stdio transport
2. Use the available resources:
   - `planner://plans/{plan_id}`
   - `planner://plans/{plan_id}/tasks`
   - `planner://plans/{plan_id}/buckets`
3. Call the available tools:
   - `create_task`
   - `update_task`
   - `delete_task`
   - `move_task`
   - `get_task_details`

## Next Steps

1. Find a valid plan ID from your Microsoft Planner
2. Test the CLI with real data
3. Integrate the MCP server with your MCP client application
4. Start managing Planner tasks programmatically!