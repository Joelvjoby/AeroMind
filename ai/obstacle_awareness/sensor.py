"""Simulated LiDAR sensor standing in for Gazebo depth data."""

from dataclasses import dataclass
from datetime import datetime, timezone

# Eight beams at 45-degree intervals, clockwise from the drone's nose.
DEFAULT_BEAM_DIRECTIONS = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)
DEFAULT_MAX_RANGE = 20.0


@dataclass(frozen=True)
class SensorReading:
    """One sweep of the sensor.

    `distances[i]` is the range returned by the beam pointing at
    `directions[i]`. A beam that hits nothing reports the sensor's maximum
    range rather than infinity.
    """

    drone_id: str
    timestamp: datetime
    distances: list
    directions: list

    def __post_init__(self):
        if len(self.distances) != len(self.directions):
            raise ValueError(
                f"got {len(self.distances)} distances for "
                f"{len(self.directions)} beam directions"
            )

    def beams(self):
        """Iterate (direction_deg, distance_m) pairs."""
        return zip(self.directions, self.distances)


class MockLidarSensor:
    """Produces synthetic readings with obstacles injected by hand.

    Stands in for the Gazebo sensor bridge so detection logic can be
    exercised deterministically, without a simulator running.

    Args:
        max_range: distance reported by a beam that hits nothing
        beam_directions: bearings of each beam, in degrees
    """

    def __init__(self, max_range=DEFAULT_MAX_RANGE, beam_directions=None):
        if max_range <= 0:
            raise ValueError("max_range must be positive")

        self.max_range = max_range
        self.beam_directions = tuple(
            DEFAULT_BEAM_DIRECTIONS if beam_directions is None else beam_directions
        )
        self._obstacles = {}

    def get_reading(self, drone_id):
        """Take a sweep, folding in any injected obstacles."""
        distances = [
            self._obstacles.get(direction, self.max_range)
            for direction in self.beam_directions
        ]
        return SensorReading(
            drone_id=drone_id,
            timestamp=datetime.now(timezone.utc),
            distances=distances,
            directions=list(self.beam_directions),
        )

    def inject_obstacle(self, direction_deg, distance_m):
        """Place a fake obstacle on the beam nearest to `direction_deg`.

        The sensor only has beams at fixed bearings, so an obstacle at an
        arbitrary angle is reported by whichever beam points closest to it.

        Obstacles beyond `max_range` are ignored, and when two land on the
        same beam only the nearer one is returned — matching how a real
        LiDAR reports the first surface each beam strikes.
        """
        if distance_m < 0:
            raise ValueError("distance_m cannot be negative")
        if distance_m > self.max_range:
            return

        beam = self._nearest_beam(direction_deg)
        self._obstacles[beam] = min(
            distance_m, self._obstacles.get(beam, self.max_range)
        )

    def clear_obstacles(self):
        """Remove every injected obstacle, restoring an empty field."""
        self._obstacles.clear()

    def _nearest_beam(self, direction_deg):
        """Snap an arbitrary bearing to the closest beam, the short way round."""

        def angular_gap(beam):
            return abs((beam - direction_deg + 180.0) % 360.0 - 180.0)

        return min(self.beam_directions, key=angular_gap)
