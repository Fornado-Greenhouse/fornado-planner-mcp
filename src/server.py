from fastmcp import FastMCP
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from src.config import Settings
from src.utils.logger import configure_logging
from src.auth.microsoft import MicrosoftAuthManager
from src.graph.client import GraphAPIClient
from src.cache.memory import MemoryCache
from src.tools.task_tools import TaskTools
import structlog

load_dotenv()

settings = Settings()
logger = configure_logging(settings.log_level, settings.log_format)

mcp = FastMCP(
    name=settings.mcp_server_name,
    version=settings.mcp_server_version
)

auth_manager = None
graph_client = None
cache_manager = None
task_tools = None


def initialize_services():
    global auth_manager, graph_client, cache_manager, task_tools
    
    if not settings.azure_tenant_id or not settings.azure_client_id or not settings.azure_client_secret:
        logger.warning("azure_credentials_not_configured")
        return False
    
    auth_manager = MicrosoftAuthManager(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret
    )
    
    graph_client = GraphAPIClient(auth_manager)
    cache_manager = MemoryCache(settings.cache_ttl_seconds)
    task_tools = TaskTools(graph_client, cache_manager)
    
    logger.info("services_initialized")
    return True


@mcp.resource("planner://plans/{plan_id}")
async def get_plan(plan_id: str) -> str:
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


@mcp.tool()
async def create_task(
    plan_id: str,
    title: str,
    bucket_id: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None,
    assignee_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
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
    if not task_tools:
        return {"error": "MCP server not configured. Please set Azure credentials in .env file."}
    
    return await task_tools.delete_task(task_id)


@mcp.tool()
async def move_task(task_id: str, target_bucket_id: str) -> Dict[str, Any]:
    if not task_tools:
        return {"error": "MCP server not configured. Please set Azure credentials in .env file."}
    
    return await task_tools.move_task(task_id, target_bucket_id)


@mcp.tool()
async def get_task_details(task_id: str) -> Dict[str, Any]:
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


initialize_services()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        mcp,
        host=settings.mcp_server_host,
        port=settings.mcp_server_port
    )
