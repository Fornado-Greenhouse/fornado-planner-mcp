from typing import Dict, Any, Optional, List
import structlog
from src.graph.client import GraphAPIClient
from src.cache.memory import MemoryCache

logger = structlog.get_logger()


class TaskTools:
    def __init__(self, graph_client: GraphAPIClient, cache: MemoryCache):
        self.graph = graph_client
        self.cache = cache
    
    async def create_task(
        self,
        plan_id: str,
        title: str,
        bucket_id: Optional[str] = None,
        description: Optional[str] = None,
        assignee_ids: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        task_data: Dict[str, Any] = {
            "planId": plan_id,
            "title": title
        }
        
        if bucket_id:
            task_data["bucketId"] = bucket_id
        if due_date:
            task_data["dueDateTime"] = due_date
        if priority is not None:
            task_data["priority"] = priority
        if assignee_ids:
            task_data["assignments"] = {
                user_id: {"@odata.type": "#microsoft.graph.plannerAssignment", "orderHint": " !"}
                for user_id in assignee_ids
            }
        
        task = await self.graph.create_task(task_data)
        
        await self.cache.delete(f"plan_tasks:{plan_id}")
        
        logger.info("task_created", task_id=task.id, plan_id=plan_id)
        return task.to_dict()
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        task = await self.graph.get_task(task_id)
        
        if not task.odata_etag:
            raise ValueError("Task etag not found")
        
        updated_task = await self.graph.update_task(task_id, updates, task.odata_etag)
        
        await self.cache.delete(f"task:{task_id}")
        await self.cache.delete(f"plan_tasks:{updated_task.plan_id}")
        
        logger.info("task_updated", task_id=task_id)
        return updated_task.to_dict()
    
    async def move_task(self, task_id: str, target_bucket_id: str) -> Dict[str, Any]:
        return await self.update_task(task_id, {"bucketId": target_bucket_id})
    
    async def delete_task(self, task_id: str) -> Dict[str, Any]:
        task = await self.graph.get_task(task_id)
        
        if not task.odata_etag:
            raise ValueError("Task etag not found")
        
        success = await self.graph.delete_task(task_id, task.odata_etag)
        
        await self.cache.delete(f"task:{task_id}")
        await self.cache.delete(f"plan_tasks:{task.plan_id}")
        
        logger.info("task_deleted", task_id=task_id)
        return {"success": success, "task_id": task_id}
