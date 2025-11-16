# FastMCP Azure OAuth Transformation Plan

## Overview

This plan transforms the Microsoft Planner MCP Server from custom MSAL device code authentication to FastMCP's built-in Azure OAuth integration using the OAuth Proxy pattern.

**Why this transformation:**
- Eliminates ~200 lines of custom authentication code (`src/auth/microsoft.py`)
- Better user experience: Browser-based OAuth instead of console device code flow
- Enterprise-ready token management with automatic refresh
- Built-in security features (PKCE, token encryption, consent screens)
- Maintained by FastMCP team

---

## Phase 1: Azure App Registration Updates

### Prerequisites
- Access to Azure Portal with admin rights
- Your existing Azure App Registration
- Tenant ID: (found in Azure Portal → Microsoft Entra ID → Overview)

### Step 1.1: Configure Application Platform

**Current Setup:** Public client application for device code flow
**Target Setup:** Web application for OAuth Proxy pattern

1. Navigate to [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations**
2. Select your existing app (or create new registration)
3. Go to **Authentication** in the sidebar
4. Under **Platform configurations**:
   - If "Mobile and desktop applications" exists, you can leave it or remove it
   - Click **Add a platform** → Select **Web**
   - **Redirect URI**: `http://localhost:8080/auth/callback` (for development)
   - For production: `https://your-domain.com/auth/callback`
   - ⚠️ **Important**: The redirect URI must match exactly

### Step 1.2: Configure Access Token Version

**Critical for FastMCP compatibility**

1. Go to **Manifest** in your app registration sidebar
2. Find the `api` section and set `requestedAccessTokenVersion` to `2`:

```json
"api": {
    "requestedAccessTokenVersion": 2
}
```

3. Click **Save** at the top

⚠️ **Without this setting, authentication will fail!**

### Step 1.3: Expose an API and Create Scopes

FastMCP's Azure integration requires at least one custom scope.

1. Go to **Expose an API** in the sidebar
2. Click **Set** next to "Application ID URI"
   - Keep default: `api://{client_id}` (recommended)
   - Or use custom format following [identifier URI restrictions](https://learn.microsoft.com/en-us/entra/identity-platform/identifier-uri-restrictions)
3. Click **Add a scope** to create your first scope:
   - **Scope name**: `planner.access` (or `read`, `write`, etc.)
   - **Who can consent**: Admins and users (or Admins only for enterprise)
   - **Admin consent display name**: "Access Microsoft Planner via MCP"
   - **Admin consent description**: "Allows the application to access Microsoft Planner on your behalf"
   - **User consent display name**: "Access your Planner data"
   - **User consent description**: "Allow this application to read and write your Planner tasks"
   - **State**: Enabled
4. Click **Add scope**

**Note:** You can create multiple scopes (e.g., `planner.read`, `planner.write`) for granular permissions.

### Step 1.4: Verify Client Secret

1. Go to **Certificates & secrets**
2. Verify you have an active client secret
3. If creating new secret:
   - Click **New client secret**
   - Description: "FastMCP OAuth Integration"
   - Expiration: Choose based on your security policy
   - ⚠️ **Copy the value immediately** - it won't be shown again

### Step 1.5: Note Your Credentials

From the **Overview** page, record:
- **Application (client) ID**: `your-client-id`
- **Directory (tenant) ID**: `your-tenant-id`
- **Client Secret**: `your-client-secret` (from previous step)
- **Application ID URI**: `api://{client_id}` (from Expose an API)
- **Scopes created**: `planner.access` (or your chosen scope names)

---

## Phase 2: Code Transformation

### Step 2.1: Update Dependencies

**File**: `requirements.txt`

```diff
- fastmcp==0.3.0
+ fastmcp>=2.13.0
  msal==1.31.1  # Can be removed after migration is complete
  httpx==0.27.2
  pydantic==2.10.3
  pydantic-settings==2.7.0
  python-dotenv==1.0.1
  structlog==24.4.0
  click==8.1.8
  tenacity==9.0.0
  rich==13.9.4
  pytest==8.3.4
  pytest-asyncio==0.24.0
- fastapi  # Remove if not used elsewhere
- uvicorn  # Remove if not used elsewhere
```

### Step 2.2: Update Configuration

**File**: `src/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Azure OAuth Configuration
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""

    # FastMCP Azure OAuth Settings
    azure_base_url: str = "http://localhost:8080"
    azure_redirect_path: str = "/auth/callback"
    azure_identifier_uri: str = ""  # Defaults to api://{client_id} if empty

    # Required scopes - unprefixed names that will be auto-prefixed with identifier_uri
    # These must match the scopes you created under "Expose an API"
    azure_required_scopes: List[str] = ["planner.access"]

    # Optional: Additional Microsoft Graph scopes (User.Read, Mail.Read, etc.)
    azure_additional_scopes: List[str] = []

    # Production: JWT signing key and storage encryption
    jwt_signing_key: Optional[str] = None
    storage_encryption_key: Optional[str] = None

    # MCP Server Settings
    mcp_server_name: str = "Microsoft Planner MCP"
    mcp_server_version: str = "1.0.0"
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8080

    # Microsoft Graph API
    graph_api_version: str = "v1.0"
    graph_api_timeout: int = 30

    # Cache Configuration
    cache_type: str = "memory"
    cache_ttl_seconds: int = 300

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Deprecated settings (kept for backward compatibility during migration)
    use_device_code_auth: bool = False  # No longer used
    use_graph_explorer_client: bool = False  # No longer used
    graph_explorer_client_id: str = ""  # No longer used
```

### Step 2.3: Transform Main Server

**File**: `src/server.py`

Replace the entire file with the FastMCP Azure OAuth implementation:

```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers.azure import AzureProvider
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from src.config import Settings as AppSettings
from src.utils.logger import configure_logging
from src.graph.client import GraphAPIClient
from src.cache.memory import MemoryCache
from src.tools.task_tools import TaskTools
import structlog
import os

load_dotenv()

settings = AppSettings()
logger = configure_logging(settings.log_level, settings.log_format)

# Configure Azure OAuth Provider
auth_provider = None
if settings.azure_tenant_id and settings.azure_client_id and settings.azure_client_secret:
    logger.info("initializing_azure_oauth_provider")

    # Build configuration
    provider_config = {
        "client_id": settings.azure_client_id,
        "client_secret": settings.azure_client_secret,
        "tenant_id": settings.azure_tenant_id,
        "base_url": settings.azure_base_url,
        "required_scopes": settings.azure_required_scopes,
        "redirect_path": settings.azure_redirect_path,
    }

    # Optional: Custom identifier URI
    if settings.azure_identifier_uri:
        provider_config["identifier_uri"] = settings.azure_identifier_uri

    # Optional: Additional Microsoft Graph scopes
    if settings.azure_additional_scopes:
        provider_config["additional_authorize_scopes"] = settings.azure_additional_scopes

    # Production: JWT signing key
    if settings.jwt_signing_key:
        provider_config["jwt_signing_key"] = settings.jwt_signing_key
        logger.info("using_custom_jwt_signing_key")

    # Production: Encrypted persistent storage
    if settings.storage_encryption_key:
        from key_value.aio.stores.redis import RedisStore
        from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
        from cryptography.fernet import Fernet

        # Example with Redis - adjust based on your infrastructure
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))

        provider_config["client_storage"] = FernetEncryptionWrapper(
            key_value=RedisStore(host=redis_host, port=redis_port),
            fernet=Fernet(settings.storage_encryption_key.encode())
        )
        logger.info("using_encrypted_redis_storage")

    auth_provider = AzureProvider(**provider_config)
    logger.info("azure_oauth_provider_initialized")
else:
    logger.warning("azure_credentials_not_configured")

# Create FastMCP instance with auth
mcp = FastMCP(
    settings.mcp_server_name,
    auth=auth_provider if auth_provider else None
)

# Initialize global services
graph_client = None
cache_manager = None
task_tools = None


def initialize_services():
    """Initialize Graph API client and related services."""
    global graph_client, cache_manager, task_tools

    if not auth_provider:
        logger.warning("services_not_initialized_missing_auth")
        return False

    # Initialize Graph API client with auth provider
    graph_client = GraphAPIClient(auth_provider)
    cache_manager = MemoryCache(settings.cache_ttl_seconds)
    task_tools = TaskTools(graph_client, cache_manager)

    logger.info("services_initialized")
    return True


# MCP Resources

@mcp.resource("planner://plans/{plan_id}")
async def get_plan(plan_id: str) -> str:
    """Get details for a specific plan."""
    if not graph_client:
        return "MCP server not configured. Please set Azure credentials in .env file."

    cache_key = f"plan:{plan_id}"
    cached = await cache_manager.get(cache_key)

    if cached:
        return str(cached)

    plan = await graph_client.get_plan(plan_id)
    result = plan.to_dict()
    await cache_manager.set(cache_key, result)

    return str(result)


@mcp.resource("planner://plans/{plan_id}/tasks")
async def list_plan_tasks(plan_id: str) -> str:
    """List all tasks in a plan."""
    if not graph_client:
        return "MCP server not configured. Please set Azure credentials in .env file."

    cache_key = f"plan_tasks:{plan_id}"
    cached = await cache_manager.get(cache_key)

    if cached:
        return str(cached)

    tasks = await graph_client.get_plan_tasks(plan_id)
    result = [task.to_dict() for task in tasks]
    await cache_manager.set(cache_key, result)

    return str(result)


@mcp.resource("planner://plans/{plan_id}/buckets")
async def list_plan_buckets(plan_id: str) -> str:
    """List all buckets in a plan."""
    if not graph_client:
        return "MCP server not configured. Please set Azure credentials in .env file."

    cache_key = f"plan_buckets:{plan_id}"
    cached = await cache_manager.get(cache_key)

    if cached:
        return str(cached)

    buckets = await graph_client.get_plan_buckets(plan_id)
    result = [bucket.to_dict() for bucket in buckets]
    await cache_manager.set(cache_key, result)

    return str(result)


# MCP Tools

@mcp.tool()
async def create_task(
    plan_id: str,
    title: str,
    bucket_id: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None,
    assignee_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create a new task in Microsoft Planner."""
    if not task_tools:
        return {"error": "MCP server not configured. Please set Azure credentials in .env file."}

    return await task_tools.create_task(
        plan_id=plan_id,
        title=title,
        bucket_id=bucket_id,
        due_date=due_date,
        priority=priority,
        assignee_ids=assignee_ids
    )


@mcp.tool()
async def update_task(
    task_id: str,
    title: Optional[str] = None,
    bucket_id: Optional[str] = None,
    percent_complete: Optional[int] = None,
    priority: Optional[int] = None,
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing task."""
    if not task_tools:
        return {"error": "MCP server not configured. Please set Azure credentials in .env file."}

    updates = {}
    if title:
        updates["title"] = title
    if bucket_id:
        updates["bucketId"] = bucket_id
    if percent_complete is not None:
        updates["percentComplete"] = percent_complete
    if priority is not None:
        updates["priority"] = priority
    if due_date:
        updates["dueDateTime"] = due_date

    return await task_tools.update_task(task_id, updates)


@mcp.tool()
async def delete_task(task_id: str) -> Dict[str, Any]:
    """Delete a task."""
    if not task_tools:
        return {"error": "MCP server not configured. Please set Azure credentials in .env file."}

    return await task_tools.delete_task(task_id)


@mcp.tool()
async def move_task(task_id: str, target_bucket_id: str) -> Dict[str, Any]:
    """Move a task to a different bucket."""
    if not task_tools:
        return {"error": "MCP server not configured. Please set Azure credentials in .env file."}

    return await task_tools.move_task(task_id, target_bucket_id)


@mcp.tool()
async def get_task_details(task_id: str) -> Dict[str, Any]:
    """Get detailed information about a task."""
    if not graph_client:
        return {"error": "MCP server not configured. Please set Azure credentials in .env file."}

    cache_key = f"task:{task_id}"
    cached = await cache_manager.get(cache_key)

    if cached:
        return cached

    task = await graph_client.get_task(task_id)
    result = task.to_dict()
    await cache_manager.set(cache_key, result)

    return result


@mcp.tool()
async def get_user_info() -> Dict[str, Any]:
    """Get information about the authenticated Azure user."""
    from fastmcp.server.dependencies import get_access_token

    try:
        token = get_access_token()
        return {
            "azure_id": token.claims.get("sub"),
            "email": token.claims.get("email"),
            "name": token.claims.get("name"),
            "preferred_username": token.claims.get("preferred_username"),
        }
    except Exception as e:
        return {"error": f"Not authenticated or token unavailable: {str(e)}"}


# Initialize services on startup
initialize_services()

if __name__ == "__main__":
    # Run with HTTP transport for OAuth support
    mcp.run(
        transport="http",
        port=settings.mcp_server_port,
        host=settings.mcp_server_host
    )
```

### Step 2.4: Update Graph API Client

**File**: `src/graph/client.py`

The Graph API client needs to work with FastMCP's auth provider instead of the custom MSAL manager:

```python
import httpx
from typing import List, Optional, Dict, Any
from src.graph.models import Plan, Task, Bucket
from src.graph.exceptions import GraphAPIError
import structlog

logger = structlog.get_logger()


class GraphAPIClient:
    """Client for Microsoft Graph API with FastMCP Azure OAuth integration."""

    def __init__(self, auth_provider):
        """
        Initialize Graph API client.

        Args:
            auth_provider: FastMCP AzureProvider instance
        """
        self.auth_provider = auth_provider
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.timeout = 30

    async def _get_token(self) -> str:
        """
        Get access token from FastMCP auth context.

        For now, we'll use the upstream token from the auth provider.
        In a production setup, you'd use FastMCP's get_access_token()
        dependency within tool/resource handlers.
        """
        # This is a simplified approach - in production you'd want to
        # integrate more tightly with FastMCP's token management
        from fastmcp.server.dependencies import get_access_token

        try:
            token = get_access_token()
            # FastMCP tokens need to be exchanged for upstream Microsoft tokens
            # For now, we'll use a workaround
            return await self._get_upstream_token()
        except Exception:
            # Fallback to getting upstream token directly
            return await self._get_upstream_token()

    async def _get_upstream_token(self) -> str:
        """
        Get the upstream Microsoft Graph token.

        Note: This is a temporary solution. In production, FastMCP's
        OAuth proxy should handle token management through the proper
        dependency injection system.
        """
        # The AzureProvider stores upstream tokens internally
        # We need to access them through the proper channels
        # For now, this is a placeholder that needs proper implementation
        raise NotImplementedError(
            "Token management needs to be integrated with FastMCP's OAuth system. "
            "See FastMCP documentation for proper token handling in tools/resources."
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Graph API."""
        token = await self._get_token()

        request_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        if headers:
            request_headers.update(headers)

        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=json,
                    params=params
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(
                    "graph_api_error",
                    status_code=e.response.status_code,
                    response=e.response.text
                )
                raise GraphAPIError(
                    f"Graph API request failed: {e.response.status_code} - {e.response.text}"
                )
            except Exception as e:
                logger.error("graph_api_request_failed", error=str(e))
                raise GraphAPIError(f"Graph API request failed: {str(e)}")

    # ... rest of the methods (get_plan, get_plan_tasks, etc.) remain the same
```

**Important Note**: The Graph API client integration needs further work to properly handle FastMCP's token management. The OAuth Proxy pattern means FastMCP issues its own JWTs to clients, but you need the upstream Microsoft token to call Graph API. This requires deeper integration with FastMCP's internal token storage.

---

## Phase 3: Environment Configuration

### Step 3.1: Update .env.example

**File**: `.env.example`

```env
# Azure OAuth Configuration
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here

# FastMCP Azure OAuth Settings
AZURE_BASE_URL=http://localhost:8080
AZURE_REDIRECT_PATH=/auth/callback
# AZURE_IDENTIFIER_URI=api://your-custom-uri  # Optional: defaults to api://{client_id}

# Azure Scopes (unprefixed names from "Expose an API")
AZURE_REQUIRED_SCOPES=["planner.access"]
# AZURE_ADDITIONAL_SCOPES=["User.Read","Mail.Read"]  # Optional: Microsoft Graph scopes

# Production: Security Keys (generate random strings)
# JWT_SIGNING_KEY=your-random-secret-key-here
# STORAGE_ENCRYPTION_KEY=your-32-byte-base64-key-here

# Production: Redis (if using encrypted storage)
# REDIS_HOST=localhost
# REDIS_PORT=6379

# MCP Server Settings
MCP_SERVER_NAME=Microsoft Planner MCP
MCP_SERVER_VERSION=1.0.0
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8080

# Microsoft Graph API
GRAPH_API_VERSION=v1.0
GRAPH_API_TIMEOUT=30

# Cache Configuration
CACHE_TYPE=memory
CACHE_TTL_SECONDS=300

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Step 3.2: Alternative: Environment Variable Auto-Configuration

FastMCP supports automatic provider configuration via environment variables:

```env
# Auto-configure Azure provider
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.azure.AzureProvider

# Azure credentials
FASTMCP_SERVER_AUTH_AZURE_CLIENT_ID=your-client-id
FASTMCP_SERVER_AUTH_AZURE_CLIENT_SECRET=your-client-secret
FASTMCP_SERVER_AUTH_AZURE_TENANT_ID=your-tenant-id
FASTMCP_SERVER_AUTH_AZURE_BASE_URL=http://localhost:8080
FASTMCP_SERVER_AUTH_AZURE_REQUIRED_SCOPES=planner.access
# FASTMCP_SERVER_AUTH_AZURE_ADDITIONAL_AUTHORIZE_SCOPES=User.Read,Mail.Read
```

With this approach, your server code simplifies to just:

```python
from fastmcp import FastMCP

# Auth automatically configured from environment
mcp = FastMCP("Microsoft Planner MCP")
```

---

## Phase 4: Documentation Updates

### Step 4.1: Update README.md

Replace the authentication section with:

````markdown
## Authentication

This server uses **FastMCP Azure OAuth** for secure authentication with Microsoft Planner.

### Azure App Registration Setup

1. **Navigate to Azure Portal**
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to **Microsoft Entra ID** → **App registrations**
   - Select your app or create new registration

2. **Configure Web Platform**
   - Go to **Authentication** → **Add a platform** → **Web**
   - Redirect URI: `http://localhost:8080/auth/callback` (development)
   - Production: Use HTTPS URL (e.g., `https://yourdomain.com/auth/callback`)

3. **Set Access Token Version**
   - Go to **Manifest**
   - Set `"api": { "requestedAccessTokenVersion": 2 }`
   - Click **Save**

4. **Create API Scope**
   - Go to **Expose an API** → **Set** Application ID URI
   - Use default: `api://{client_id}`
   - Click **Add a scope**:
     - Scope name: `planner.access`
     - Admin consent display name: "Access Microsoft Planner via MCP"
     - Description: "Allows the application to access Microsoft Planner on your behalf"
     - State: Enabled

5. **Create Client Secret**
   - Go to **Certificates & secrets** → **New client secret**
   - Copy the value immediately (won't be shown again!)

6. **Note Your Credentials**
   - From **Overview**: Application (client) ID, Directory (tenant) ID
   - Client secret from previous step

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/fornado-planner-mcp.git
cd fornado-planner-mcp

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure credentials
```

### Configuration

Edit `.env` with your Azure credentials:

```env
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_REQUIRED_SCOPES=["planner.access"]
```

### Running the Server

```bash
python src/server.py
```

The server runs on `http://localhost:8080` with OAuth authentication enabled.

### First-Time Authentication

When you first connect an MCP client:

1. The client redirects you to Microsoft's login page
2. Sign in with your Microsoft account
3. Consent to the requested permissions
4. You'll see a FastMCP consent screen showing the client details
5. Approve the client connection
6. You're redirected back and authenticated!

Subsequent connections use cached tokens - no need to re-authenticate.

### Testing with a Client

```python
from fastmcp import Client
import asyncio

async def main():
    async with Client("http://localhost:8080/mcp", auth="oauth") as client:
        # First-time connection opens browser for authentication
        result = await client.call_tool("get_user_info")
        print(f"Authenticated as: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```
````

### Step 4.2: Create Migration Guide

**File**: `docs/MIGRATION_FROM_DEVICE_CODE.md`

````markdown
# Migration Guide: Device Code Flow → FastMCP Azure OAuth

This guide helps existing users migrate from the custom MSAL device code flow to FastMCP's Azure OAuth integration.

## What's Changing

### Before (Device Code Flow)
- Console-based authentication with manual code entry
- Custom token caching in `.token_cache.json`
- Manual MSAL configuration

### After (FastMCP OAuth)
- Automatic browser-based OAuth flow
- Built-in token management by FastMCP
- Simpler configuration

## Migration Steps

### 1. Update Azure App Registration

Your existing app registration needs updates:

1. **Add Web Platform Redirect**
   - Go to Authentication → Add platform → Web
   - Redirect URI: `http://localhost:8080/auth/callback`

2. **Set Token Version to 2**
   - Manifest → `"api": { "requestedAccessTokenVersion": 2 }`

3. **Create API Scope**
   - Expose an API → Add scope: `planner.access`

4. **Keep Existing Permissions**
   - Your existing API permissions remain the same

### 2. Update Your .env File

```diff
# Same credentials
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret

+ # New: OAuth configuration
+ AZURE_REQUIRED_SCOPES=["planner.access"]
+ AZURE_BASE_URL=http://localhost:8080

- # Removed: No longer needed
- USE_DEVICE_CODE_AUTH=True
```

### 3. Update Dependencies

```bash
pip install --upgrade 'fastmcp>=2.13.0'
```

### 4. First Run

1. Start the server: `python src/server.py`
2. Connect your MCP client
3. Browser opens automatically for authentication
4. Sign in and approve consent screen
5. Done! Tokens are managed automatically

### Troubleshooting

**Issue**: Browser doesn't open
**Solution**: Check that `base_url` is correct and server is running on HTTP transport

**Issue**: "Invalid redirect URI" error
**Solution**: Verify redirect URI in Azure matches exactly: `http://localhost:8080/auth/callback`

**Issue**: "Invalid token version" error
**Solution**: Check app manifest has `requestedAccessTokenVersion: 2`

**Issue**: "Missing required scopes" error
**Solution**: Ensure scope exists under "Expose an API" in your Azure app
````

---

## Phase 5: Testing & Validation

### Step 5.1: Local Testing Checklist

```bash
# 1. Install updated dependencies
pip install -r requirements.txt

# 2. Verify environment configuration
cat .env  # Check all Azure credentials are set

# 3. Start server
python src/server.py

# Expected output:
# - Server starts on http://0.0.0.0:8080
# - OAuth endpoints registered
# - No authentication errors
```

### Step 5.2: Authentication Flow Test

Create a test client:

**File**: `tests/test_oauth_flow.py`

```python
"""Test FastMCP Azure OAuth authentication flow."""
import asyncio
from fastmcp import Client


async def test_authentication():
    """Test OAuth authentication and tool access."""
    print("🔐 Testing FastMCP Azure OAuth authentication...")

    async with Client("http://localhost:8080/mcp", auth="oauth") as client:
        print("✅ Authentication successful!")

        # Test get_user_info tool
        user_info = await client.call_tool("get_user_info")
        print(f"👤 Authenticated as: {user_info.get('email')}")
        print(f"📛 Name: {user_info.get('name')}")

        return True


if __name__ == "__main__":
    success = asyncio.run(test_authentication())
    if success:
        print("\n✨ All tests passed!")
    else:
        print("\n❌ Tests failed")
```

Run the test:
```bash
python tests/test_oauth_flow.py
```

Expected behavior:
1. Browser opens to Microsoft login
2. You sign in
3. Consent screen shows client details
4. After approval, authentication completes
5. User info is displayed

### Step 5.3: Verify Token Caching

```bash
# First run: Should open browser
python tests/test_oauth_flow.py

# Second run: Should use cached tokens (no browser)
python tests/test_oauth_flow.py
```

---

## Phase 6: Production Deployment

### Step 6.1: Generate Production Keys

```bash
# Generate JWT signing key (any random string works)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate storage encryption key (must be base64-encoded 32 bytes)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add to production environment:
```env
JWT_SIGNING_KEY=<output-from-first-command>
STORAGE_ENCRYPTION_KEY=<output-from-second-command>
```

### Step 6.2: Configure Persistent Storage

For production with multiple server instances, use Redis:

```bash
# Install Redis storage dependency
pip install redis
```

Update `.env`:
```env
REDIS_HOST=your-redis-host
REDIS_PORT=6379
STORAGE_ENCRYPTION_KEY=<your-fernet-key>
```

### Step 6.3: Update Azure Redirect URI for Production

1. Go to Azure Portal → Your app → Authentication
2. Add production redirect URI:
   - `https://your-domain.com/auth/callback`
3. Update `.env`:
   ```env
   AZURE_BASE_URL=https://your-domain.com
   ```

---

## Phase 7: Cleanup

### Step 7.1: Remove Deprecated Code

After verifying the new authentication works:

```bash
# Remove custom MSAL authentication manager
rm src/auth/microsoft.py

# Remove old token cache files
rm .token_cache.json .token_cache.json.backup

# Optional: Remove MSAL dependency if not used elsewhere
# Edit requirements.txt and remove: msal==1.31.1
```

### Step 7.2: Update .gitignore

```gitignore
# FastMCP OAuth storage (if using local disk storage)
.fastmcp/

# Old token cache (legacy)
.token_cache.json
.token_cache.json.backup
```

---

## Important Implementation Note

### Graph API Token Access Challenge

The current plan has one critical limitation that needs addressing:

**The Problem**: FastMCP's OAuth Proxy pattern issues its own JWT tokens to MCP clients, but the Graph API requires the upstream Microsoft access token. The proxy stores upstream tokens internally, but we need a way to access them from within tool/resource handlers.

**Potential Solutions**:

1. **Use FastMCP's token storage directly** (requires understanding FastMCP internals)
2. **Implement a custom token exchange mechanism**
3. **Contact FastMCP team for guidance** on accessing upstream tokens
4. **Store upstream tokens in a separate cache** keyed by user ID

This is a known limitation that requires further investigation of FastMCP's architecture or consultation with the FastMCP team.

---

## Summary

### Files Modified
- ✏️ `src/server.py` - Integrate AzureProvider
- ✏️ `src/config.py` - Add OAuth settings
- ✏️ `src/graph/client.py` - Update token handling (needs work)
- ✏️ `requirements.txt` - Upgrade FastMCP
- ✏️ `.env.example` - Add OAuth configuration
- ✏️ `README.md` - Update authentication docs

### Files Removed
- ❌ `src/auth/microsoft.py` - Custom MSAL manager (after migration)
- ❌ `.token_cache.json` - Old token cache

### New Files
- ➕ `docs/MIGRATION_FROM_DEVICE_CODE.md` - Migration guide
- ➕ `tests/test_oauth_flow.py` - OAuth testing

### Azure Changes Required
1. Add Web platform redirect URI
2. Set access token version to 2
3. Create API scope under "Expose an API"
4. Verify client secret is active

### Benefits
- ✅ Eliminate ~200 lines of custom auth code
- ✅ Better UX: Browser-based OAuth
- ✅ Automatic token management and refresh
- ✅ Built-in security (PKCE, consent screens, token encryption)
- ✅ Production-ready with persistent storage
- ✅ Maintained by FastMCP team

### Risks
- ⚠️ Breaking change for existing users
- ⚠️ Graph API token access needs further work
- ⚠️ Azure app reconfiguration required
- ⚠️ Different authentication flow may affect automation

---

## Next Steps

1. ✅ Review this transformation plan
2. 🔄 Update Azure App Registration
3. 🔄 Implement code changes
4. 🔄 Test locally with development credentials
5. 🔄 Create migration documentation
6. 🔄 Deploy to production
7. 🔄 Communicate changes to users

