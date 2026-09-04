"""Tests for the simulated sensor and threshold-based obstacle detector."""

import pytest

from fsm.drone_fsm import DroneFSM, InvalidTransitionError
from fsm.states import DroneState, Trigger
from obstacle_awareness.detector import ObstacleDetector, ThreatLevel
from obstacle_awareness.sensor import (
    DEFAULT_BEAM_DIRECTIONS,
    MockLidarSensor,
    SensorReading,
)


@pytest.fixture
def sensor():
    return MockLidarSensor()


@pytest.fixture
def detector():
    return ObstacleDetector(safe_distance=5.0)


def analyze_with(sensor, detector, drone_id="d1"):
    """Take a sweep and classify it in one step."""
    return detector.analyze(sensor.get_reading(drone_id))


class TestMockLidarSensor:
    """Sweep generation and obstacle injection."""

    def test_reading_has_eight_beams_at_expected_bearings(self, sensor):
        reading = sensor.get_reading("d1")

        assert reading.directions == list(DEFAULT_BEAM_DIRECTIONS)
        assert len(reading.distances) == 8
        assert reading.drone_id == "d1"

    def test_empty_field_reads_max_range_on_every_beam(self, sensor):
        reading = sensor.get_reading("d1")

        assert reading.distances == [20.0] * 8

    def test_injected_obstacle_appears_on_its_beam_only(self, sensor):
        sensor.inject_obstacle(90.0, 7.0)
        reading = sensor.get_reading("d1")

        assert dict(reading.beams())[90.0] == 7.0
        assert [d for direction, d in reading.beams() if direction != 90.0] == [20.0] * 7

    def test_arbitrary_bearing_snaps_to_nearest_beam(self, sensor):
        sensor.inject_obstacle(80.0, 6.0)  # nearest beam is 90 degrees
        sensor.inject_obstacle(350.0, 8.0)  # wraps round to the 0 degree beam

        beams = dict(sensor.get_reading("d1").beams())
        assert beams[90.0] == 6.0
        assert beams[0.0] == 8.0

    def test_obstacle_beyond_max_range_is_invisible(self, sensor):
        sensor.inject_obstacle(0.0, 25.0)

        assert sensor.get_reading("d1").distances == [20.0] * 8

    def test_nearer_obstacle_wins_on_a_shared_beam(self, sensor):
        sensor.inject_obstacle(45.0, 12.0)
        sensor.inject_obstacle(45.0, 3.0)

        assert dict(sensor.get_reading("d1").beams())[45.0] == 3.0

    def test_negative_distance_rejected(self, sensor):
        with pytest.raises(ValueError, match="negative"):
            sensor.inject_obstacle(0.0, -1.0)

    def test_mismatched_reading_lengths_rejected(self):
        with pytest.raises(ValueError, match="distances"):
            SensorReading("d1", None, distances=[1.0, 2.0], directions=[0.0])


class TestNoObstacle:
    """All beams at max range means a clear field."""

    def test_clear_field_reports_no_detection(self, sensor, detector):
        result = analyze_with(sensor, detector)

        assert result.is_obstacle_detected is False
        assert result.threat_level is ThreatLevel.NONE
        assert result.closest_distance == 20.0

    def test_distant_obstacle_is_still_clear(self, sensor, detector):
        sensor.inject_obstacle(180.0, 15.0)
        result = analyze_with(sensor, detector)

        assert result.threat_level is ThreatLevel.NONE
        assert result.is_obstacle_detected is False


class TestWarningThreatLevel:
    """Obstacles in the 5-10 m band."""

    @pytest.mark.parametrize("distance", [5.0, 6.5, 8.0, 10.0])
    def test_obstacle_in_band_raises_warning(self, sensor, detector, distance):
        sensor.inject_obstacle(135.0, distance)
        result = analyze_with(sensor, detector)

        assert result.threat_level is ThreatLevel.WARNING
        assert result.is_obstacle_detected is True
        assert result.closest_distance == distance
        assert result.closest_direction == 135.0


class TestCriticalThreatLevel:
    """Obstacles inside the safe distance."""

    @pytest.mark.parametrize("distance", [0.0, 1.5, 4.99])
    def test_obstacle_inside_safe_distance_is_critical(self, sensor, detector, distance):
        sensor.inject_obstacle(270.0, distance)
        result = analyze_with(sensor, detector)

        assert result.threat_level is ThreatLevel.CRITICAL
        assert result.is_obstacle_detected is True
        assert result.closest_direction == 270.0


class TestThreatBoundaries:
    """The exact edges of each band."""

    def test_safe_distance_itself_is_warning_not_critical(self, sensor, detector):
        sensor.inject_obstacle(0.0, 5.0)

        assert analyze_with(sensor, detector).threat_level is ThreatLevel.WARNING

    def test_just_inside_safe_distance_is_critical(self, sensor, detector):
        sensor.inject_obstacle(0.0, 4.999)

        assert analyze_with(sensor, detector).threat_level is ThreatLevel.CRITICAL

    def test_warning_edge_is_inclusive(self, sensor, detector):
        sensor.inject_obstacle(0.0, 10.0)

        assert analyze_with(sensor, detector).threat_level is ThreatLevel.WARNING

    def test_just_beyond_warning_edge_is_clear(self, sensor, detector):
        sensor.inject_obstacle(0.0, 10.001)

        assert analyze_with(sensor, detector).threat_level is ThreatLevel.NONE

    def test_thresholds_scale_with_safe_distance(self, sensor):
        detector = ObstacleDetector(safe_distance=2.0)  # warning band 2-4 m
        sensor.inject_obstacle(0.0, 3.0)

        assert analyze_with(sensor, detector).threat_level is ThreatLevel.WARNING

    def test_warning_distance_nearer_than_safe_is_rejected(self):
        with pytest.raises(ValueError, match="warning_distance"):
            ObstacleDetector(safe_distance=5.0, warning_distance=3.0)


class TestMultipleObstacles:
    """The nearest return is the one that matters."""

    def test_closest_obstacle_is_reported(self, sensor, detector):
        sensor.inject_obstacle(0.0, 18.0)
        sensor.inject_obstacle(90.0, 3.0)
        sensor.inject_obstacle(180.0, 9.0)

        result = analyze_with(sensor, detector)

        assert result.closest_distance == 3.0
        assert result.closest_direction == 90.0
        assert result.threat_level is ThreatLevel.CRITICAL

    def test_critical_outranks_a_nearer_looking_warning(self, sensor, detector):
        sensor.inject_obstacle(45.0, 5.5)
        sensor.inject_obstacle(225.0, 4.5)

        result = analyze_with(sensor, detector)

        assert result.closest_direction == 225.0
        assert result.threat_level is ThreatLevel.CRITICAL

    def test_all_beams_blocked_reports_the_nearest(self, sensor, detector):
        for index, direction in enumerate(DEFAULT_BEAM_DIRECTIONS):
            sensor.inject_obstacle(direction, 12.0 - index)

        result = analyze_with(sensor, detector)

        assert result.closest_distance == 5.0
        assert result.closest_direction == 315.0


class TestClearObstacles:
    """Resetting the simulated field."""

    def test_clear_restores_max_range_on_every_beam(self, sensor):
        sensor.inject_obstacle(0.0, 2.0)
        sensor.inject_obstacle(180.0, 4.0)
        sensor.clear_obstacles()

        assert sensor.get_reading("d1").distances == [20.0] * 8

    def test_detection_returns_to_none_after_clearing(self, sensor, detector):
        sensor.inject_obstacle(90.0, 1.0)
        assert analyze_with(sensor, detector).threat_level is ThreatLevel.CRITICAL

        sensor.clear_obstacles()
        assert analyze_with(sensor, detector).threat_level is ThreatLevel.NONE

    def test_clearing_an_empty_field_is_harmless(self, sensor):
        sensor.clear_obstacles()

        assert sensor.get_reading("d1").distances == [20.0] * 8


class TestFsmTriggerMapping:
    """Each threat level maps onto the trigger the FSM expects."""

    def test_critical_fires_obstacle_detected(self, sensor, detector):
        sensor.inject_obstacle(0.0, 2.0)
        result = analyze_with(sensor, detector)

        assert detector.get_fsm_trigger(result) is Trigger.OBSTACLE_DETECTED

    def test_warning_also_fires_obstacle_detected(self, sensor, detector):
        sensor.inject_obstacle(0.0, 7.0)
        result = analyze_with(sensor, detector)

        assert detector.get_fsm_trigger(result) is Trigger.OBSTACLE_DETECTED

    def test_clear_field_fires_path_clear(self, sensor, detector):
        result = analyze_with(sensor, detector)

        assert detector.get_fsm_trigger(result) is Trigger.PATH_CLEAR


class TestFsmIntegration:
    """The trigger actually drives a drone's state machine."""

    def test_critical_detection_sends_a_flying_drone_to_replanning(self, sensor, detector):
        fsm = DroneFSM("d1")
        sensor.inject_obstacle(45.0, 2.0)
        result = analyze_with(sensor, detector)

        fsm.transition(detector.get_fsm_trigger(result), {"bearing": result.closest_direction})

        assert fsm.current_state is DroneState.REPLANNING

    def test_clearing_releases_a_held_drone(self, sensor, detector):
        fsm = DroneFSM("d1")
        sensor.inject_obstacle(45.0, 2.0)
        fsm.transition(detector.get_fsm_trigger(analyze_with(sensor, detector)))
        fsm.transition(Trigger.HOLD)

        sensor.clear_obstacles()
        fsm.transition(detector.get_fsm_trigger(analyze_with(sensor, detector)))

        assert fsm.current_state is DroneState.NORMAL

    def test_path_clear_is_rejected_by_a_drone_already_flying(self, sensor, detector):
        # A clear sweep yields PATH_CLEAR, which only BLOCKED_HOLD accepts, so
        # callers must check state before firing rather than polling blindly.
        fsm = DroneFSM("d1")
        result = analyze_with(sensor, detector)

        with pytest.raises(InvalidTransitionError):
            fsm.transition(detector.get_fsm_trigger(result))
