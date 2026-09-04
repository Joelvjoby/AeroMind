import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drone_id = Column(UUID(as_uuid=True), ForeignKey("drones.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    battery_level = Column(Float)
    fsm_state = Column(String)
    speed = Column(Float)
