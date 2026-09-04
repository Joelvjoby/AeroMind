import uuid
import enum
from sqlalchemy import Column, String, Integer, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class DroneStatus(str, enum.Enum):
    IDLE = "IDLE"
    ASSIGNED = "ASSIGNED"
    IN_FLIGHT = "IN_FLIGHT"
    LOW_BATTERY = "LOW_BATTERY"
    LOST = "LOST"


class Drone(Base):
    __tablename__ = "drones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    mavlink_id = Column(Integer, unique=True, nullable=False)
    status = Column(Enum(DroneStatus), default=DroneStatus.IDLE, nullable=False)
    battery_level = Column(Float)
    current_lat = Column(Float)
    current_lon = Column(Float)
    current_alt = Column(Float)
