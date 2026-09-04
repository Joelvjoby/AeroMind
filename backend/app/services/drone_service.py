"""Fleet queries."""

from app.models.drone import Drone


def get_all_drones(db):
    """Return every drone in the fleet, ordered by MAVLink id."""
    return db.query(Drone).order_by(Drone.mavlink_id).all()
