from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field

from app.models import NodeStatus, Priority


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserRead"


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = {"from_attributes": True}


class ClusterBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    region: str = Field(min_length=1, max_length=120)
    description: str = ""


class ClusterCreate(ClusterBase):
    pass


class ClusterRead(ClusterBase):
    id: int

    model_config = {"from_attributes": True}


class NodeBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    cpu_cores: float = Field(gt=0)
    memory_gb: float = Field(gt=0)
    storage_gb: float = Field(gt=0)
    status: NodeStatus = NodeStatus.active


class NodeCreate(NodeBase):
    cluster_id: int


class NodeRead(NodeBase):
    id: int
    cluster_id: int

    model_config = {"from_attributes": True}


class WorkloadBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    cpu_required: float = Field(gt=0)
    memory_required: float = Field(gt=0)
    storage_required: float = Field(gt=0)
    priority: Priority = Priority.medium


class WorkloadCreate(WorkloadBase):
    cluster_id: int


class WorkloadRead(WorkloadBase):
    id: int
    cluster_id: int

    model_config = {"from_attributes": True}


Algorithm = Literal["Best Fit", "Least Loaded", "Weighted Resource Scoring"]
TrafficPattern = Literal["Low", "Medium", "High", "Spike"]


class SimulationRun(BaseModel):
    cluster_id: int
    algorithm: Algorithm = "Weighted Resource Scoring"
    traffic_pattern: TrafficPattern = "Medium"
    duration_hours: int = Field(default=24, ge=1, le=720)


class FailoverRun(BaseModel):
    cluster_id: int
    failed_node_ids: list[int]
    algorithm: Algorithm = "Weighted Resource Scoring"


class SimulationRead(BaseModel):
    id: int
    cluster_id: int
    algorithm: str
    traffic_pattern: str
    duration_hours: int
    results: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardRead(BaseModel):
    total_clusters: int
    active_nodes: int
    active_workloads: int
    utilization: dict[str, float]
    health: str
    recent_simulations: list[SimulationRead]


class ForecastRead(BaseModel):
    cluster_id: int
    exhaustion_dates: dict[str, str]
    future_needs: dict[str, float]
    recommendations: list[str]
