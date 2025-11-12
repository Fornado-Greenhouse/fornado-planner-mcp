# Microsoft Planner MCP Server - Replit Project

## Overview
Production-ready MCP (Model Context Protocol) server integrating Microsoft Planner with FastMCP. Enables programmatic management of planning boards and backlogs through the Microsoft Graph API.

## Current State
MVP implementation with core features:
- Microsoft OAuth 2.0 authentication with MSAL
- Graph API client with retry logic and error handling
- FastMCP server with resource handlers for plans, tasks, and buckets
- MCP tools for task CRUD operations
- In-memory caching layer
- CLI client for testing
- HTTP test server for API testing
- Comprehensive documentation

**Status:** ✅ Fully functional! Authentication working with device code flow for single-user M365 instances.

## Project Structure
```
src/
├── server.py              # FastMCP server entry point
├── config.py              # Pydantic settings
├── auth/
│   ├── microsoft.py       # MSAL authentication
│   └── __init__.py
├── graph/
│   ├── client.py          # Graph API client
│   ├── models.py          # Pydantic models
│   ├── exceptions.py      # Custom exceptions
│   └── __init__.py
├── cache/
│   ├── interface.py       # Cache interface
│   ├── memory.py          # In-memory cache
│   └── __init__.py
├── tools/
│   ├── task_tools.py      # Task management tools
│   └── __init__.py
└── utils/
    ├── logger.py          # Structured logging
    └── __init__.py

cli/
└── mcp_cli.py             # CLI client

scripts/
└── setup_azure_app.py     # Azure setup guide
```

## Azure Configuration Required
Before running the server, you must:
1. Create an Azure AD app registration
2. Configure Microsoft Graph API permissions:
   - Tasks.ReadWrite (Delegated)
   - Tasks.ReadWrite.Shared (Delegated)
   - Group.Read.All (Application)
   - User.Read.All (Application)
3. Create a client secret
4. Add credentials to `.env` file

Run `python scripts/setup_azure_app.py` for detailed instructions.

## Environment Variables
Required in `.env`:
- `AZURE_TENANT_ID` - Azure AD tenant ID
- `AZURE_CLIENT_ID` - Application client ID
- `AZURE_CLIENT_SECRET` - Client secret value
- `USE_DEVICE_CODE_AUTH` - Set to `true` for interactive user login (recommended)
- `USE_GRAPH_EXPLORER_CLIENT` - Set to `false` to use your own Azure app (recommended after enabling public client flows)

## MCP Resources
- `planner://plans/{plan_id}` - Get plan details
- `planner://plans/{plan_id}/tasks` - List tasks
- `planner://plans/{plan_id}/buckets` - List buckets

## MCP Tools
- `create_task` - Create new task in a plan
- `update_task` - Update existing task
- `delete_task` - Delete a task
- `move_task` - Move task to different bucket
- `get_task_details` - Get detailed task information

## Recent Changes
- **2025-11-12:** Successfully configured device code authentication for user login
  - Fixed "invalid_client" error by enabling public client flows in Azure Portal
  - Implemented delegated user authentication (not app-only)
  - Added environment variables for authentication mode control
  - Verified working with user's Planner data (alex@fornado.onmicrosoft.com)
- Initial MVP implementation (2025-01-12)
- Core authentication and Graph API client
- FastMCP server with resources and tools
- In-memory caching layer
- CLI client for testing
- HTTP test server added for API testing
- Fixed client lifecycle issues in HTTP server
- Added group and plan discovery endpoints
- Created Azure permissions fix guide
- Documentation and setup scripts

## Dependencies
- fastmcp==0.3.0 (MCP framework)
- msal==1.31.1 (Microsoft authentication)
- httpx==0.27.2 (Async HTTP)
- pydantic==2.10.3 (Data validation)
- structlog==24.4.0 (Logging)
- tenacity==9.0.0 (Retry logic)
- rich==13.9.4 (CLI formatting)

## Next Phase Features
- Bulk operations for batch task updates
- Redis caching for production scalability
- GitLab CI/CD integration
- Comprehensive test suite
- Advanced query capabilities
- Report generation tools
- Prometheus metrics

## Notes
- Server gracefully handles missing Azure credentials
- All API calls include retry logic for transient failures
- Cache invalidation on task updates
- Structured JSON logging for debugging
