"""
HTTP Test Server for Microsoft Planner MCP
This provides an HTTP interface for testing the MCP server functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import asyncio

from src.config import Settings as AppSettings
from src.auth.microsoft import MicrosoftAuthManager
from src.graph.client import GraphAPIClient
from src.cache.memory import MemoryCache
from src.tools.task_tools import TaskTools
from src.utils.logger import configure_logging

# Load environment
load_dotenv()

# Initialize settings and logging
settings = AppSettings()
logger = configure_logging(settings.log_level, "console")

# Create FastAPI app
app = FastAPI(title="Planner MCP Test Server")

# Global services
auth_manager = None
graph_client = None
cache_manager = None
task_tools = None
services_initialized = False


def initialize_services():
    """Initialize all services"""
    global auth_manager, graph_client, cache_manager, task_tools, services_initialized
    
    if not settings.azure_tenant_id or not settings.azure_client_id or not settings.azure_client_secret:
        logger.warning("Azure credentials not configured")
        return False
    
    try:
        auth_manager = MicrosoftAuthManager(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret
        )
        
        graph_client = GraphAPIClient(auth_manager)
        cache_manager = MemoryCache(settings.cache_ttl_seconds)
        task_tools = TaskTools(graph_client, cache_manager)
        
        services_initialized = True
        logger.info("Services initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return False


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    initialize_services()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "running",
        "services_initialized": services_initialized,
        "azure_configured": bool(settings.azure_tenant_id)
    }


@app.get("/planner/plans/{plan_id}")
async def get_plan(plan_id: str):
    """Get plan details"""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Services not initialized. Check Azure credentials.")
    
    try:
        cache_key = f"plan:{plan_id}"
        cached = await cache_manager.get(cache_key)
        
        if cached:
            return cached
        
        async with graph_client:
            plan = await graph_client.get_plan(plan_id)
            result = plan.to_dict()
            await cache_manager.set(cache_key, result)
            return result
    except Exception as e:
        logger.error(f"Error getting plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/planner/plans/{plan_id}/tasks")
async def list_plan_tasks(plan_id: str):
    """List all tasks in a plan"""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Services not initialized. Check Azure credentials.")
    
    try:
        cache_key = f"plan_tasks:{plan_id}"
        cached = await cache_manager.get(cache_key)
        
        if cached:
            return cached
        
        async with graph_client:
            tasks = await graph_client.get_plan_tasks(plan_id)
            result = [task.to_dict() for task in tasks]
            await cache_manager.set(cache_key, result)
            return result
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/planner/plans/{plan_id}/buckets")
async def list_plan_buckets(plan_id: str):
    """List all buckets in a plan"""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Services not initialized. Check Azure credentials.")
    
    try:
        cache_key = f"plan_buckets:{plan_id}"
        cached = await cache_manager.get(cache_key)
        
        if cached:
            return cached
        
        async with graph_client:
            buckets = await graph_client.get_plan_buckets(plan_id)
            result = [bucket.to_dict() for bucket in buckets]
            await cache_manager.set(cache_key, result)
            return result
    except Exception as e:
        logger.error(f"Error listing buckets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/create_task")
async def create_task(
    plan_id: str,
    title: str,
    bucket_id: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[int] = None,
    assignee_ids: Optional[List[str]] = None
):
    """Create a new task"""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Services not initialized. Check Azure credentials.")
    
    try:
        async with graph_client:
            return await task_tools.create_task(
                plan_id=plan_id,
                title=title,
                bucket_id=bucket_id,
                due_date=due_date,
                priority=priority,
                assignee_ids=assignee_ids
            )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/tools/update_task/{task_id}")
async def update_task(
    task_id: str,
    title: Optional[str] = None,
    bucket_id: Optional[str] = None,
    percent_complete: Optional[int] = None,
    priority: Optional[int] = None,
    due_date: Optional[str] = None
):
    """Update an existing task"""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Services not initialized. Check Azure credentials.")
    
    try:
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
        
        async with graph_client:
            return await task_tools.update_task(task_id, updates)
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tools/delete_task/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Services not initialized. Check Azure credentials.")
    
    try:
        async with graph_client:
            return await task_tools.delete_task(task_id)
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.mcp_server_host,
        port=settings.mcp_server_port
    )