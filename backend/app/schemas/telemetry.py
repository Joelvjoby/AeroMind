from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TelemetryEntry(BaseModel):
    """One telemetry sample from a drone.

    This is both the websocket stream payload and the write model for
    persisting a sample to `telemetry_logs`.
    """

    model_config = ConfigDict(from_attributes=True)

    drone_id: UUID
    latitude: float
    longitude: float
    altitude: float
    battery_level: float
    fsm_state: str
    speed: float
    timestamp: datetime
