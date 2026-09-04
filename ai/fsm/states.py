"""States and triggers for the drone decision-making FSM."""

from enum import Enum


class DroneState(str, Enum):
    """Behavioural mode a drone is currently operating in.

    Subclasses `str` so members are directly JSON-serialisable and compare
    equal to their names — this is what gets persisted to the
    `telemetry_logs.fsm_state` string column.
    """

    NORMAL = "NORMAL"
    REPLANNING = "REPLANNING"
    LOW_BATTERY_RETURN = "LOW_BATTERY_RETURN"
    BLOCKED_HOLD = "BLOCKED_HOLD"
    COMPLETE = "COMPLETE"


class Trigger(str, Enum):
    """Event that may cause a drone to change state."""

    OBSTACLE_DETECTED = "OBSTACLE_DETECTED"
    PATH_CLEAR = "PATH_CLEAR"
    BATTERY_LOW = "BATTERY_LOW"
    MISSION_COMPLETE = "MISSION_COMPLETE"
    REPLAN_DONE = "REPLAN_DONE"
    HOLD = "HOLD"
    RESUME = "RESUME"
