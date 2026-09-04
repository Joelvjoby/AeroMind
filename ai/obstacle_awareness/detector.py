"""Threshold-based obstacle detection over simulated sensor readings."""

from dataclasses import dataclass
from enum import Enum

from fsm.states import Trigger


class ThreatLevel(str, Enum):
    """How urgently an obstacle needs to be acted on."""

    NONE = "NONE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class DetectionResult:
    """Verdict on a single sensor sweep."""

    is_obstacle_detected: bool
    closest_distance: float
    closest_direction: float
    threat_level: ThreatLevel


class ObstacleDetector:
    """Classifies sensor sweeps by proximity to the nearest return.

    Args:
        safe_distance: anything nearer than this is CRITICAL
        warning_distance: outer edge of the WARNING band; defaults to twice
            `safe_distance`, giving the 5-10 m band for the 5 m default
    """

    def __init__(self, safe_distance=5.0, warning_distance=None):
        if safe_distance <= 0:
            raise ValueError("safe_distance must be positive")

        self.safe_distance = safe_distance
        self.warning_distance = (
            safe_distance * 2.0 if warning_distance is None else warning_distance
        )

        if self.warning_distance < self.safe_distance:
            raise ValueError("warning_distance cannot be nearer than safe_distance")

    def analyze(self, reading):
        """Reduce a sweep to its nearest return and a threat classification.

        Raises:
            ValueError: if the reading carries no beams. A sweep with no data
                is a sensor fault, and reporting it as "path clear" would be
                the one wrong answer to give an obstacle-avoidance loop.
        """
        if not reading.distances:
            raise ValueError("sensor reading contains no beams")

        # Ties resolve to the first beam in the sweep, keeping results stable.
        closest_direction, closest_distance = min(
            reading.beams(), key=lambda beam: beam[1]
        )
        threat_level = self._classify(closest_distance)

        return DetectionResult(
            is_obstacle_detected=threat_level is not ThreatLevel.NONE,
            closest_distance=closest_distance,
            closest_direction=closest_direction,
            threat_level=threat_level,
        )

    def get_fsm_trigger(self, result):
        """Map a detection result onto the FSM trigger it should fire.

        Note the returned trigger is only valid in some FSM states — the
        caller is responsible for firing it when the drone can accept it.
        """
        if result.threat_level is ThreatLevel.NONE:
            return Trigger.PATH_CLEAR
        return Trigger.OBSTACLE_DETECTED

    def _classify(self, distance):
        """Band a distance into a threat level."""
        if distance < self.safe_distance:
            return ThreatLevel.CRITICAL
        if distance <= self.warning_distance:
            return ThreatLevel.WARNING
        return ThreatLevel.NONE
