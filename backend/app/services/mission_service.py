"""Mission planning and reporting operations."""

from app.models.alert import Alert
from app.models.mission import Mission
from app.models.task import Task, TaskStatus
from app.models.waypoint import Waypoint


def create_mission(db, payload):
    """Persist a mission and its route in a single transaction.

    Waypoints keep the order they were submitted in unless the caller
    supplies an explicit `sequence_order`.
    """
    mission = Mission(
        name=payload.name,
        description=payload.description,
        created_by=payload.created_by,
    )
    db.add(mission)
    db.flush()  # assigns mission.id without ending the transaction

    for index, waypoint in enumerate(payload.waypoints):
        db.add(
            Waypoint(
                mission_id=mission.id,
                sequence_order=(
                    index if waypoint.sequence_order is None else waypoint.sequence_order
                ),
                latitude=waypoint.latitude,
                longitude=waypoint.longitude,
                altitude=waypoint.altitude,
            )
        )

    db.commit()
    db.refresh(mission)
    return mission


def get_mission(db, mission_id):
    """Return a mission, or None if it does not exist."""
    return db.get(Mission, mission_id)


def get_mission_waypoints(db, mission_id):
    """Return a mission's route in flight order."""
    return (
        db.query(Waypoint)
        .filter(Waypoint.mission_id == mission_id)
        .order_by(Waypoint.sequence_order)
        .all()
    )


def get_mission_report(db, mission_id):
    """Summarise a mission's execution, or None if it does not exist."""
    mission = db.get(Mission, mission_id)
    if mission is None:
        return None

    tasks = db.query(Task).filter(Task.mission_id == mission_id).all()
    alerts = (
        db.query(Alert)
        .filter(Alert.mission_id == mission_id)
        .order_by(Alert.created_at.desc())
        .all()
    )

    # Every status is present so consumers can chart the breakdown without
    # guarding for missing keys.
    task_counts = {status.value: 0 for status in TaskStatus}
    for task in tasks:
        task_counts[task.status.value] += 1

    return {
        "mission": mission,
        "total_waypoints": db.query(Waypoint)
        .filter(Waypoint.mission_id == mission_id)
        .count(),
        "task_counts": task_counts,
        "tasks": tasks,
        "alerts": alerts,
        "unread_alerts": sum(1 for alert in alerts if not alert.is_read),
    }
