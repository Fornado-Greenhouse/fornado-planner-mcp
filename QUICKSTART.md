# Quick Start Guide

## Getting Started with Microsoft Planner MCP Server

### Step 1: Azure Setup

Before you can use the MCP server, you need to set up Azure credentials:

```bash
python scripts/setup_azure_app.py
```

This script will guide you through:
1. Creating an Azure AD app registration
2. Configuring required API permissions
3. Generating client secrets
4. Gathering necessary IDs

### Step 2: Configure Environment

Create a `.env` file with your Azure credentials:

```bash
cp .env.example .env
```

Edit `.env` and add:
```
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here
```

### Step 3: Verify Server

The server is already running! Check the console output - you should see:
```
Starting "Microsoft Planner MCP"...
```

Once you add Azure credentials and restart, you'll be able to use all MCP resources and tools.

## Using the MCP Server

### Available Resources

Query these resources through your MCP client:

- `planner://plans/{plan_id}` - Get plan details
- `planner://plans/{plan_id}/tasks` - List all tasks
- `planner://plans/{plan_id}/buckets` - List all buckets

### Available Tools

Call these tools to manage tasks:

- **create_task** - Create new tasks
- **update_task** - Modify existing tasks
- **delete_task** - Remove tasks
- **move_task** - Move tasks between buckets
- **get_task_details** - Get detailed task information

## Testing with CLI

Use the included CLI client to test:

```bash
# List tasks in a plan
python cli/mcp_cli.py list-tasks --plan-id YOUR_PLAN_ID

# Create a new task
python cli/mcp_cli.py create-task --plan-id YOUR_PLAN_ID --title "New Task"
```

## Next Steps

1. Set up your Azure app registration
2. Add credentials to `.env`
3. Restart the MCP server
4. Connect your MCP client application
5. Start managing Planner tasks programmatically!

For detailed documentation, see [README.md](README.md)
