from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    """An operator-facing notification raised during a mission."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mission_id: UUID | None = None
    drone_id: UUID | None = None
    alert_type: str
    message: str
    is_read: bool
    created_at: datetime | None = None
