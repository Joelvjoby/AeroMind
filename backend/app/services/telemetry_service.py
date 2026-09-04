"""Telemetry persistence and simulated sample generation."""

import random
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID, uuid4

from obstacle_awareness.sensor import DEFAULT_BEAM_DIRECTIONS, MockLidarSensor

from app.models.telemetry_log import TelemetryLog
from app.schemas.telemetry import TelemetryEntry
from app.services import fsm_service

# Arbitrary starting point for simulated flights; replace once missions
# carry a real launch position.
BASE_LATITUDE = 12.9716
BASE_LONGITUDE = 77.5946

# Demo tuning. The drain is far faster than a real airframe so a stream
# walks the whole NORMAL -> ... -> LOW_BATTERY_RETURN lifecycle in about a
# minute instead of an hour.
BATTERY_START_RANGE = (0.5, 1.0)
BATTERY_DRAIN_RANGE = (0.005, 0.02)
LOW_BATTERY_THRESHOLD = 0.2
OBSTACLE_PROBABILITY = 0.25

_sensors = {}
_sensor_lock = Lock()


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


def get_sensor(drone_id):
    """Return this drone's simulated LiDAR, creating it on first sight."""
    key = str(drone_id)
    with _sensor_lock:
        sensor = _sensors.get(key)
        if sensor is None:
            sensor = MockLidarSensor()
            _sensors[key] = sensor
        return sensor


def generate_mock_telemetry(drone_id=None, previous=None):
    """Build a synthetic telemetry sample and advance the drone's FSM.

    Passing the `previous` entry makes the drone drift and drain from where
    it was, so a stream reads as one continuous flight. The returned
    `fsm_state` is the real state machine's verdict on this sample, not a
    random label.
    """
    if drone_id is None:
        drone_id = previous.drone_id if previous else uuid4()
    elif not isinstance(drone_id, UUID):
        drone_id = UUID(str(drone_id))

    if previous is None:
        latitude = BASE_LATITUDE + random.uniform(-0.001, 0.001)
        longitude = BASE_LONGITUDE + random.uniform(-0.001, 0.001)
        altitude = random.uniform(30.0, 120.0)
        battery_level = random.uniform(*BATTERY_START_RANGE)
    else:
        latitude = previous.latitude + random.uniform(-0.0002, 0.0002)
        longitude = previous.longitude + random.uniform(-0.0002, 0.0002)
        altitude = max(0.0, previous.altitude + random.uniform(-2.0, 2.0))
        battery_level = max(
            0.0, previous.battery_level - random.uniform(*BATTERY_DRAIN_RANGE)
        )

    reading = _sense(drone_id, battery_level)
    status = fsm_service.process_telemetry(drone_id, battery_level, reading)

    return TelemetryEntry(
        drone_id=drone_id,
        latitude=round(latitude, 6),
        longitude=round(longitude, 6),
        altitude=round(altitude, 2),
        battery_level=round(battery_level, 4),
        fsm_state=status["current_state"],
        speed=round(random.uniform(0.0, 18.0), 2),
        timestamp=datetime.now(timezone.utc),
    )


def _sense(drone_id, battery_level):
    """Take a simulated sweep, seeding obstacles for the drone to react to.

    A low battery always plants something close, so the low-power path is
    exercised; otherwise obstacles appear at random to drive the replanning
    and hold cycles.
    """
    sensor = get_sensor(drone_id)
    sensor.clear_obstacles()

    bearing = random.choice(DEFAULT_BEAM_DIRECTIONS)
    if battery_level < LOW_BATTERY_THRESHOLD:
        sensor.inject_obstacle(bearing, random.uniform(1.0, 4.0))
    elif random.random() < OBSTACLE_PROBABILITY:
        sensor.inject_obstacle(bearing, random.uniform(1.0, 9.0))

    return sensor.get_reading(str(drone_id))
