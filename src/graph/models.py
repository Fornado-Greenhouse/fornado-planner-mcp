from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class PlannerPlan(BaseModel):
    id: str
    title: str
    owner: Optional[str] = None
    created_date_time: Optional[datetime] = None
    container: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlannerPlan":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            owner=data.get("owner"),
            created_date_time=data.get("createdDateTime"),
            container=data.get("container")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "owner": self.owner,
            "createdDateTime": self.created_date_time.isoformat() if self.created_date_time else None,
            "container": self.container
        }


class PlannerBucket(BaseModel):
    id: str
    name: str
    plan_id: str
    order_hint: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlannerBucket":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            plan_id=data.get("planId", ""),
            order_hint=data.get("orderHint")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "planId": self.plan_id,
            "orderHint": self.order_hint
        }


class PlannerTask(BaseModel):
    model_config = {"populate_by_name": True}
    
    id: str
    title: str
    plan_id: str
    bucket_id: Optional[str] = None
    percent_complete: int = 0
    priority: Optional[int] = None
    start_date_time: Optional[datetime] = None
    due_date_time: Optional[datetime] = None
    assignments: Optional[Dict[str, Any]] = None
    odata_etag: Optional[str] = Field(None, alias="@odata.etag")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlannerTask":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            plan_id=data.get("planId", ""),
            bucket_id=data.get("bucketId"),
            percent_complete=data.get("percentComplete", 0),
            priority=data.get("priority"),
            start_date_time=data.get("startDateTime"),
            due_date_time=data.get("dueDateTime"),
            assignments=data.get("assignments"),
            odata_etag=data.get("@odata.etag")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "title": self.title,
            "planId": self.plan_id,
            "percentComplete": self.percent_complete
        }
        if self.bucket_id:
            result["bucketId"] = self.bucket_id
        if self.priority is not None:
            result["priority"] = self.priority
        if self.start_date_time:
            result["startDateTime"] = self.start_date_time.isoformat() if isinstance(self.start_date_time, datetime) else self.start_date_time
        if self.due_date_time:
            result["dueDateTime"] = self.due_date_time.isoformat() if isinstance(self.due_date_time, datetime) else self.due_date_time
        if self.assignments:
            result["assignments"] = self.assignments
        return result
