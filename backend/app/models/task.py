import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id"), nullable=False)
    drone_id = Column(UUID(as_uuid=True), ForeignKey("drones.id"), nullable=False)
    waypoint_id = Column(UUID(as_uuid=True), ForeignKey("waypoints.id"))
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
