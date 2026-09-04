from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.drone import DroneStatus


class DroneResponse(BaseModel):
    """A drone's identity and last known state."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    mavlink_id: int
    status: DroneStatus
    battery_level: float | None = None
    current_lat: float | None = None
    current_lon: float | None = None
    # Live decision-making state, read from the in-memory FSM registry
    # rather than the drones table.
    fsm_state: str | None = None
