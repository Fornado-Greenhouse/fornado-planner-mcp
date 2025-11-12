# Microsoft Planner MCP Server

A production-ready MCP (Model Context Protocol) server that integrates Microsoft Planner with your applications, enabling programmatic management of planning boards and backlogs.

## Features

- **Microsoft OAuth 2.0 Authentication** - Secure authentication with MSAL and token caching
- **Graph API Integration** - Full access to Microsoft Planner via Graph API
- **FastMCP Server** - Resource handlers for plans, tasks, and buckets
- **Task Management Tools** - Create, read, update, delete, and move tasks
- **Intelligent Caching** - In-memory caching for improved performance
- **CLI Client** - Command-line interface for testing and interaction
- **Structured Logging** - JSON logging with context tracking

## Prerequisites

- Python 3.11+
- Microsoft Azure account with admin access
- Microsoft 365 organization with Planner enabled
- Azure app registration with required permissions

## Quick Start

### 1. Azure App Registration

Run the setup script to get step-by-step instructions:

```bash
python scripts/setup_azure_app.py
```

This will guide you through:
- Creating an Azure AD app registration
- Configuring API permissions
- Creating client secrets
- Gathering required credentials

### 2. Environment Configuration

Copy the example environment file and fill in your Azure credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your Azure credentials:

```env
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-app-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
python src/server.py
```

The server will start on `http://0.0.0.0:8080`

## MCP Resources

The server exposes these MCP resources:

- `planner://plans/{plan_id}` - Get plan details
- `planner://plans/{plan_id}/tasks` - List all tasks in a plan
- `planner://plans/{plan_id}/buckets` - List all buckets in a plan

## MCP Tools

Available tools for task management:

### create_task
Create a new task in Microsoft Planner.

**Parameters:**
- `plan_id` (required): Plan ID
- `title` (required): Task title
- `bucket_id` (optional): Bucket ID
- `due_date` (optional): Due date (ISO 8601 format)
- `priority` (optional): Priority (0-10)
- `assignee_ids` (optional): List of user IDs to assign

### update_task
Update an existing task.

**Parameters:**
- `task_id` (required): Task ID
- `title` (optional): New title
- `bucket_id` (optional): New bucket ID
- `percent_complete` (optional): Progress percentage (0-100)
- `priority` (optional): New priority
- `due_date` (optional): New due date

### delete_task
Delete a task.

**Parameters:**
- `task_id` (required): Task ID

### move_task
Move a task to a different bucket.

**Parameters:**
- `task_id` (required): Task ID
- `target_bucket_id` (required): Target bucket ID

### get_task_details
Get detailed information about a task.

**Parameters:**
- `task_id` (required): Task ID

## CLI Usage

The project includes a CLI client for testing:

```bash
# Get plan details
python cli/mcp_cli.py get-plan --plan-id YOUR_PLAN_ID

# List tasks in a plan
python cli/mcp_cli.py list-tasks --plan-id YOUR_PLAN_ID

# Create a new task
python cli/mcp_cli.py create-task --plan-id YOUR_PLAN_ID --title "New Task" --priority 5
```

## Architecture

```
src/
├── server.py           # FastMCP server entry point
├── config.py           # Configuration management
├── auth/               # Microsoft authentication
├── graph/              # Graph API client
├── cache/              # Caching layer
├── tools/              # MCP tools
└── utils/              # Utilities and logging
```

## Configuration

All configuration is managed through environment variables or the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_TENANT_ID` | Azure AD tenant ID | Required |
| `AZURE_CLIENT_ID` | App client ID | Required |
| `AZURE_CLIENT_SECRET` | App client secret | Required |
| `MCP_SERVER_NAME` | Server name | "Microsoft Planner MCP" |
| `MCP_SERVER_PORT` | Server port | 8080 |
| `CACHE_TTL_SECONDS` | Cache TTL | 300 |
| `LOG_LEVEL` | Logging level | INFO |

## Security

- Never commit `.env` file or secrets to version control
- Rotate client secrets regularly
- Use minimum required API permissions
- Enable audit logging in Azure AD

## Troubleshooting

### Authentication Errors
- Verify Azure credentials in `.env`
- Check app registration permissions
- Ensure admin consent is granted

### API Errors
- Check network connectivity
- Verify plan/task IDs are correct
- Review server logs for details

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
