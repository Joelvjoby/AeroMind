from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.mission import MissionStatus
from app.models.task import TaskStatus
from app.schemas.alert import AlertResponse


class WaypointCreate(BaseModel):
    """A point on a mission route.

    `sequence_order` is optional: when omitted, waypoints are numbered by
    their position in the submitted list.
    """

    latitude: float
    longitude: float
    altitude: float
    sequence_order: int | None = None


class WaypointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sequence_order: int
    latitude: float
    longitude: float
    altitude: float


class MissionCreate(BaseModel):
    """Payload for planning a new mission.

    `created_by` is optional until authentication lands; once it does, the
    owner should come from the authenticated session rather than the body.
    """

    name: str = Field(min_length=1)
    description: str | None = None
    waypoints: list[WaypointCreate] = Field(default_factory=list)
    created_by: UUID | None = None


class MissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: MissionStatus
    created_at: datetime | None = None
    # Absent from a bare ORM object (POST /missions, GET /missions/{id}),
    # so it defaults to 0 there; the list endpoint populates it for real.
    task_count: int = 0


class MissionDetailResponse(MissionResponse):
    """A mission together with its ordered route."""

    description: str | None = None
    waypoints: list[WaypointResponse] = Field(default_factory=list)


class TaskSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    drone_id: UUID | None = None
    waypoint_id: UUID | None = None
    status: TaskStatus
    assigned_at: datetime | None = None
    completed_at: datetime | None = None
    planned_path: list[dict[str, float]] | None = None


class MissionReportResponse(BaseModel):
    """Post-mission summary: what was planned, what ran, what went wrong."""

    mission: MissionResponse
    total_waypoints: int
    task_counts: dict[str, int]
    tasks: list[TaskSummary] = Field(default_factory=list)
    alerts: list[AlertResponse] = Field(default_factory=list)
    unread_alerts: int
