"""Tests for the drone decision-making FSM."""

import time

import pytest

from fsm.drone_fsm import DroneFSM, InvalidTransitionError
from fsm.states import DroneState, Trigger


def drive(fsm, *triggers):
    """Fire a sequence of triggers and collect the resulting states."""
    return [fsm.transition(trigger) for trigger in triggers]


class TestNormalMissionFlow:
    """The happy path: fly the plan, finish the mission."""

    def test_starts_in_normal_with_no_history(self):
        fsm = DroneFSM("d1")

        assert fsm.current_state == DroneState.NORMAL
        assert fsm.previous_state is None

    def test_normal_to_complete(self):
        fsm = DroneFSM("d1")

        assert fsm.transition(Trigger.MISSION_COMPLETE) == DroneState.COMPLETE
        assert fsm.previous_state == DroneState.NORMAL

    def test_complete_is_terminal(self):
        fsm = DroneFSM("d1")
        fsm.transition(Trigger.MISSION_COMPLETE)

        for trigger in Trigger:
            with pytest.raises(InvalidTransitionError):
                fsm.transition(trigger)


class TestObstacleReplanningFlow:
    """NORMAL -> REPLANNING -> NORMAL."""

    def test_obstacle_then_replan_returns_to_normal(self):
        fsm = DroneFSM("d1")

        states = drive(fsm, Trigger.OBSTACLE_DETECTED, Trigger.REPLAN_DONE)

        assert states == [DroneState.REPLANNING, DroneState.NORMAL]
        assert fsm.previous_state == DroneState.REPLANNING

    def test_can_replan_repeatedly(self):
        fsm = DroneFSM("d1")

        for _ in range(3):
            drive(fsm, Trigger.OBSTACLE_DETECTED, Trigger.REPLAN_DONE)

        assert fsm.current_state == DroneState.NORMAL

    def test_context_is_recorded(self):
        fsm = DroneFSM("d1")
        obstacle = {"lat": 12.9, "lon": 77.6}

        fsm.transition(Trigger.OBSTACLE_DETECTED, obstacle)

        assert fsm.last_context == obstacle


class TestLowBatteryFlow:
    """NORMAL -> LOW_BATTERY_RETURN -> COMPLETE."""

    def test_low_battery_return_then_complete(self):
        fsm = DroneFSM("d1")

        states = drive(fsm, Trigger.BATTERY_LOW, Trigger.MISSION_COMPLETE)

        assert states == [DroneState.LOW_BATTERY_RETURN, DroneState.COMPLETE]

    def test_returning_drone_cannot_be_diverted_to_replan(self):
        fsm = DroneFSM("d1")
        fsm.transition(Trigger.BATTERY_LOW)

        with pytest.raises(InvalidTransitionError):
            fsm.transition(Trigger.OBSTACLE_DETECTED)

    def test_battery_threshold_governs_criticality(self):
        fsm = DroneFSM("d1", battery_threshold=0.2)

        assert fsm.is_battery_critical(0.15)
        assert fsm.is_battery_critical(0.2)
        assert not fsm.is_battery_critical(0.25)


class TestBlockedHoldFlow:
    """NORMAL -> REPLANNING -> BLOCKED_HOLD -> REPLANNING -> NORMAL."""

    def test_full_hold_and_recover_cycle(self):
        fsm = DroneFSM("d1")

        states = drive(
            fsm,
            Trigger.OBSTACLE_DETECTED,
            Trigger.HOLD,
            Trigger.RESUME,
            Trigger.REPLAN_DONE,
        )

        assert states == [
            DroneState.REPLANNING,
            DroneState.BLOCKED_HOLD,
            DroneState.REPLANNING,
            DroneState.NORMAL,
        ]

    def test_hold_is_only_reachable_from_replanning(self):
        fsm = DroneFSM("d1")

        with pytest.raises(InvalidTransitionError):
            fsm.transition(Trigger.HOLD)


class TestInvalidTransitions:
    """Undefined (state, trigger) pairs are rejected, not silently ignored."""

    def test_unknown_trigger_for_state_raises(self):
        fsm = DroneFSM("d1")

        with pytest.raises(InvalidTransitionError):
            fsm.transition(Trigger.REPLAN_DONE)

    def test_error_names_the_drone_and_state(self):
        fsm = DroneFSM("scout-7")

        with pytest.raises(InvalidTransitionError, match="scout-7.*NORMAL"):
            fsm.transition(Trigger.RESUME)

    def test_path_clear_has_no_defined_transition(self):
        # PATH_CLEAR is declared as a trigger but appears in no transition,
        # so it is currently rejected from every state.
        for state_setup in ([], [Trigger.OBSTACLE_DETECTED], [Trigger.BATTERY_LOW]):
            fsm = DroneFSM("d1")
            drive(fsm, *state_setup)

            with pytest.raises(InvalidTransitionError):
                fsm.transition(Trigger.PATH_CLEAR)

    def test_failed_transition_leaves_state_untouched(self):
        fsm = DroneFSM("d1")
        fsm.transition(Trigger.OBSTACLE_DETECTED)

        with pytest.raises(InvalidTransitionError):
            fsm.transition(Trigger.BATTERY_LOW)

        assert fsm.current_state == DroneState.REPLANNING
        assert fsm.previous_state == DroneState.NORMAL


class TestMultipleDrones:
    """Each drone's machine is fully independent."""

    def test_drones_do_not_share_state(self):
        alpha = DroneFSM("alpha")
        bravo = DroneFSM("bravo")
        charlie = DroneFSM("charlie")

        alpha.transition(Trigger.OBSTACLE_DETECTED)
        bravo.transition(Trigger.BATTERY_LOW)

        assert alpha.current_state == DroneState.REPLANNING
        assert bravo.current_state == DroneState.LOW_BATTERY_RETURN
        assert charlie.current_state == DroneState.NORMAL

    def test_failure_on_one_drone_does_not_affect_others(self):
        alpha = DroneFSM("alpha")
        bravo = DroneFSM("bravo")
        bravo.transition(Trigger.OBSTACLE_DETECTED)

        with pytest.raises(InvalidTransitionError):
            alpha.transition(Trigger.RESUME)

        assert bravo.current_state == DroneState.REPLANNING

    def test_status_reports_per_drone_identity(self):
        alpha = DroneFSM("alpha")
        alpha.transition(Trigger.OBSTACLE_DETECTED)

        assert alpha.get_status() == {
            "drone_id": "alpha",
            "current_state": DroneState.REPLANNING,
            "previous_state": DroneState.NORMAL,
        }

    def test_context_is_not_shared_between_drones(self):
        alpha = DroneFSM("alpha")
        bravo = DroneFSM("bravo")

        alpha.transition(Trigger.OBSTACLE_DETECTED, {"lat": 1.0})

        assert bravo.last_context == {}


class TestResponseTime:
    """NFR: a state transition must resolve in well under one second."""

    def test_single_transition_is_under_one_second(self):
        fsm = DroneFSM("d1")

        start = time.perf_counter()
        fsm.transition(Trigger.OBSTACLE_DETECTED)
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0

    def test_slowest_transition_across_a_full_cycle_is_under_one_second(self):
        cycle = (
            Trigger.OBSTACLE_DETECTED,
            Trigger.HOLD,
            Trigger.RESUME,
            Trigger.REPLAN_DONE,
        )
        slowest = 0.0

        for _ in range(250):
            fsm = DroneFSM("d1")
            for trigger in cycle:
                start = time.perf_counter()
                fsm.transition(trigger)
                slowest = max(slowest, time.perf_counter() - start)

        assert slowest < 1.0

    def test_rejecting_an_invalid_transition_is_also_fast(self):
        fsm = DroneFSM("d1")

        start = time.perf_counter()
        with pytest.raises(InvalidTransitionError):
            fsm.transition(Trigger.RESUME)
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0
