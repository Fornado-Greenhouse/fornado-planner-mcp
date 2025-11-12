import httpx
from typing import Dict, List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from src.graph.models import PlannerTask, PlannerPlan, PlannerBucket
from src.graph.exceptions import (
    GraphAPIError, 
    RateLimitError, 
    NotFoundError,
    AuthenticationError
)

logger = structlog.get_logger()


class GraphAPIClient:
    BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, auth_manager):
        self.auth = auth_manager
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=10)
        )
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        token = self.auth.get_app_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        
        logger.debug("making_graph_request", method=method, endpoint=endpoint)
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "60"))
                raise RateLimitError(f"Rate limited. Retry after {retry_after} seconds")
            
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed")
            
            if response.status_code == 404:
                raise NotFoundError(f"Resource not found: {endpoint}")
            
            response.raise_for_status()
            
            return response
            
        except httpx.HTTPStatusError as e:
            logger.error("graph_api_error", status=e.response.status_code)
            raise GraphAPIError(f"Graph API error: {e}")
        except Exception as e:
            logger.error("unexpected_error", error=str(e))
            raise
    
    async def get_plan(self, plan_id: str) -> PlannerPlan:
        response = await self._make_request("GET", f"/planner/plans/{plan_id}")
        return PlannerPlan.from_dict(response.json())
    
    async def get_group_plans(self, group_id: str) -> List[PlannerPlan]:
        response = await self._make_request("GET", f"/groups/{group_id}/planner/plans")
        data = response.json()
        return [PlannerPlan.from_dict(p) for p in data.get("value", [])]
    
    async def get_task(self, task_id: str) -> PlannerTask:
        response = await self._make_request("GET", f"/planner/tasks/{task_id}")
        return PlannerTask.from_dict(response.json())
    
    async def get_plan_tasks(self, plan_id: str) -> List[PlannerTask]:
        response = await self._make_request("GET", f"/planner/plans/{plan_id}/tasks")
        data = response.json()
        return [PlannerTask.from_dict(t) for t in data.get("value", [])]
    
    async def create_task(self, task_data: Dict[str, Any]) -> PlannerTask:
        response = await self._make_request(
            "POST",
            "/planner/tasks",
            json=task_data
        )
        return PlannerTask.from_dict(response.json())
    
    async def update_task(
        self,
        task_id: str,
        updates: Dict[str, Any],
        etag: str
    ) -> PlannerTask:
        response = await self._make_request(
            "PATCH",
            f"/planner/tasks/{task_id}",
            json=updates,
            headers={"If-Match": etag}
        )
        return PlannerTask.from_dict(response.json())
    
    async def delete_task(self, task_id: str, etag: str) -> bool:
        response = await self._make_request(
            "DELETE",
            f"/planner/tasks/{task_id}",
            headers={"If-Match": etag}
        )
        return response.status_code == 204
    
    async def get_plan_buckets(self, plan_id: str) -> List[PlannerBucket]:
        response = await self._make_request(
            "GET",
            f"/planner/plans/{plan_id}/buckets"
        )
        data = response.json()
        return [PlannerBucket.from_dict(b) for b in data.get("value", [])]
    
    async def batch_request(self, requests: List[Dict[str, Any]]) -> List[Dict]:
        batch_payload = {"requests": requests}
        response = await self._make_request(
            "POST",
            "/$batch",
            json=batch_payload
        )
        return response.json().get("responses", [])
