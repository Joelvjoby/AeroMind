"""Fleet queries."""

from app.models.drone import Drone
from app.services import fsm_service


def get_all_drones(db):
    """Return every drone in the fleet, ordered by MAVLink id."""
    return db.query(Drone).order_by(Drone.mavlink_id).all()


def get_fleet_status(db):
    """Every drone with its live FSM state attached.

    A drone that has never reported telemetry has no machine yet, so it
    reads as NORMAL — the state a machine starts in.
    """
    return [
        {
            "id": drone.id,
            "name": drone.name,
            "mavlink_id": drone.mavlink_id,
            "status": drone.status,
            "battery_level": drone.battery_level,
            "current_lat": drone.current_lat,
            "current_lon": drone.current_lon,
            "fsm_state": fsm_service.get_drone_state(drone.id),
        }
        for drone in get_all_drones(db)
    ]
