"""Per-drone finite state machine governing autonomous decision-making."""

from fsm.states import DroneState, Trigger


class InvalidTransitionError(Exception):
    """Raised when a trigger has no defined effect in the current state."""


# The complete transition table. Any (state, trigger) pair absent from this
# mapping is rejected, which makes COMPLETE a terminal state and keeps
# illegal jumps (e.g. BLOCKED_HOLD straight to NORMAL) impossible.
TRANSITIONS = {
    (DroneState.NORMAL, Trigger.OBSTACLE_DETECTED): DroneState.REPLANNING,
    (DroneState.NORMAL, Trigger.BATTERY_LOW): DroneState.LOW_BATTERY_RETURN,
    (DroneState.NORMAL, Trigger.MISSION_COMPLETE): DroneState.COMPLETE,
    (DroneState.REPLANNING, Trigger.REPLAN_DONE): DroneState.NORMAL,
    (DroneState.REPLANNING, Trigger.HOLD): DroneState.BLOCKED_HOLD,
    (DroneState.BLOCKED_HOLD, Trigger.RESUME): DroneState.REPLANNING,
    (DroneState.LOW_BATTERY_RETURN, Trigger.MISSION_COMPLETE): DroneState.COMPLETE,
}


class DroneFSM:
    """Tracks one drone's behavioural state.

    Each drone owns its own instance; no state is shared between them, so a
    fleet is just a collection of independent machines.

    Args:
        drone_id: identifier of the drone this machine governs
        battery_threshold: charge fraction at or below which the drone should
            be sent home (see `is_battery_critical`)
    """

    def __init__(self, drone_id, battery_threshold=0.2):
        self.drone_id = drone_id
        self.battery_threshold = battery_threshold
        self.current_state = DroneState.NORMAL
        self.previous_state = None
        self.last_context = {}

    def transition(self, trigger, context=None):
        """Apply a trigger and advance to the resulting state.

        Args:
            trigger: the `Trigger` that fired
            context: optional metadata about the event (battery level,
                obstacle position, ...). Recorded as `last_context`.

        Returns:
            The new `DroneState`.

        Raises:
            InvalidTransitionError: if the trigger is undefined for the
                current state.
        """
        # Defaulted to None rather than {} so callers can never share and
        # mutate a single dict held on the function object.
        context = {} if context is None else context

        try:
            next_state = TRANSITIONS[(self.current_state, trigger)]
        except KeyError:
            raise InvalidTransitionError(
                f"drone {self.drone_id}: cannot apply {getattr(trigger, 'value', trigger)} "
                f"while in {self.current_state.value}"
            ) from None

        self.previous_state = self.current_state
        self.current_state = next_state
        self.last_context = context
        return self.current_state

    def get_status(self):
        """Snapshot of who this drone is and where it stands."""
        return {
            "drone_id": self.drone_id,
            "current_state": self.current_state,
            "previous_state": self.previous_state,
        }

    def is_battery_critical(self, battery_level):
        """True if `battery_level` warrants firing `Trigger.BATTERY_LOW`.

        The FSM does not poll telemetry itself; the caller uses this to decide
        when to fire the trigger.
        """
        return battery_level <= self.battery_threshold
