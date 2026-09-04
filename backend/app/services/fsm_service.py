"""In-memory fleet of drone state machines driven by telemetry."""

import logging
from threading import Lock

from fsm.drone_fsm import DroneFSM, InvalidTransitionError
from fsm.states import DroneState, Trigger
from obstacle_awareness.detector import ObstacleDetector, ThreatLevel

logger = logging.getLogger(__name__)

DEFAULT_BATTERY_THRESHOLD = 0.2
DEFAULT_SAFE_DISTANCE = 5.0

# Machines live only for the life of the process. Restarting the backend
# resets every drone to NORMAL; persisting state is a later concern.
_machines = {}
_lock = Lock()

_detector = ObstacleDetector(safe_distance=DEFAULT_SAFE_DISTANCE)


def get_or_create_fsm(drone_id, battery_threshold=DEFAULT_BATTERY_THRESHOLD):
    """Return this drone's state machine, creating it on first sight."""
    key = str(drone_id)
    with _lock:
        machine = _machines.get(key)
        if machine is None:
            machine = DroneFSM(key, battery_threshold=battery_threshold)
            _machines[key] = machine
        return machine


def get_drone_state(drone_id):
    """Current FSM state for a drone."""
    return get_or_create_fsm(drone_id).current_state


def process_telemetry(drone_id, battery_level, sensor_reading=None):
    """Fold one telemetry sample into a drone's state machine.

    Runs obstacle detection over `sensor_reading`, weighs it against the
    battery, and fires the one trigger the drone can currently accept.

    Returns the drone's status dict, plus the threat level that informed it.
    """
    machine = get_or_create_fsm(drone_id)
    detection = (
        _detector.analyze(sensor_reading) if sensor_reading is not None else None
    )

    trigger = _select_trigger(machine, battery_level, detection)
    if trigger is not None:
        try:
            machine.transition(
                trigger,
                {
                    "battery_level": battery_level,
                    "threat_level": detection.threat_level if detection else None,
                },
            )
        except InvalidTransitionError:
            # _select_trigger only proposes legal moves, so this means the
            # table changed underneath us. Log it rather than drop the sample.
            logger.exception("Rejected trigger %s for drone %s", trigger, drone_id)

    status = machine.get_status()
    status["threat_level"] = (
        detection.threat_level if detection else ThreatLevel.NONE
    )
    status["battery_level"] = battery_level
    return status


def reset():
    """Forget every machine. Intended for tests."""
    with _lock:
        _machines.clear()


def _select_trigger(machine, battery_level, detection):
    """Choose the trigger to fire, or None to hold position.

    Only ever returns a trigger that is legal from the drone's current
    state, since the FSM rejects anything else.
    """
    state = machine.current_state
    obstacle = detection is not None and detection.is_obstacle_detected
    critical = detection is not None and detection.threat_level is ThreatLevel.CRITICAL
    battery_low = battery_level is not None and machine.is_battery_critical(
        battery_level
    )

    if state is DroneState.NORMAL:
        # Getting home outranks routing around an obstacle.
        if battery_low:
            return Trigger.BATTERY_LOW
        if obstacle:
            return Trigger.OBSTACLE_DETECTED
        return None

    if state is DroneState.REPLANNING:
        if critical:
            return Trigger.HOLD
        if detection is not None and not obstacle:
            # Stands in for a replanning worker: once the way is clear there
            # is nothing left to route around.
            return Trigger.REPLAN_DONE
        return None

    if state is DroneState.BLOCKED_HOLD:
        if detection is not None and not obstacle:
            return Trigger.PATH_CLEAR
        return None

    # LOW_BATTERY_RETURN and COMPLETE are only left by mission-level events.
    return None
