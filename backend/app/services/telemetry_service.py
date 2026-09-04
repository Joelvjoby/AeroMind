"""Telemetry persistence and simulated sample generation."""

import random
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.telemetry_log import TelemetryLog
from app.schemas.telemetry import TelemetryEntry

# Arbitrary starting point for simulated flights; replace once missions
# carry a real launch position.
BASE_LATITUDE = 12.9716
BASE_LONGITUDE = 77.5946

# Mirrors DroneState in ai/fsm/states.py. The two live in separate
# containers, so the values are duplicated rather than imported.
MOCK_FSM_STATES = ("NORMAL", "REPLANNING", "LOW_BATTERY_RETURN", "BLOCKED_HOLD")


def save_telemetry_entry(db, entry):
    """Persist one telemetry sample.

    `entry.drone_id` must reference an existing drone — `telemetry_logs`
    carries a NOT NULL foreign key to `drones`.
    """
    log = TelemetryLog(
        drone_id=entry.drone_id,
        timestamp=entry.timestamp,
        latitude=entry.latitude,
        longitude=entry.longitude,
        altitude=entry.altitude,
        battery_level=entry.battery_level,
        fsm_state=entry.fsm_state,
        speed=entry.speed,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def generate_mock_telemetry(drone_id=None, previous=None):
    """Build a synthetic telemetry sample.

    Passing the `previous` entry makes the drone drift and drain from where
    it was, so a stream reads as one continuous flight instead of a drone
    teleporting each second. Stands in until MAVLink telemetry is wired up.
    """
    if drone_id is None:
        drone_id = previous.drone_id if previous else uuid4()
    elif not isinstance(drone_id, UUID):
        drone_id = UUID(str(drone_id))

    if previous is None:
        latitude = BASE_LATITUDE + random.uniform(-0.001, 0.001)
        longitude = BASE_LONGITUDE + random.uniform(-0.001, 0.001)
        altitude = random.uniform(30.0, 120.0)
        battery_level = random.uniform(0.7, 1.0)
    else:
        latitude = previous.latitude + random.uniform(-0.0002, 0.0002)
        longitude = previous.longitude + random.uniform(-0.0002, 0.0002)
        altitude = max(0.0, previous.altitude + random.uniform(-2.0, 2.0))
        battery_level = max(0.0, previous.battery_level - random.uniform(0.0, 0.002))

    return TelemetryEntry(
        drone_id=drone_id,
        latitude=round(latitude, 6),
        longitude=round(longitude, 6),
        altitude=round(altitude, 2),
        battery_level=round(battery_level, 4),
        fsm_state=random.choice(MOCK_FSM_STATES),
        speed=round(random.uniform(0.0, 18.0), 2),
        timestamp=datetime.now(timezone.utc),
    )
