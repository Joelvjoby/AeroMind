"""Mission planning, task allocation, route planning and reporting."""

import logging

from sqlalchemy import func

from path_planning.astar import AStarPlanner
from path_planning.grid import METERS_PER_DEGREE_LAT, Grid
from task_allocation.allocator import allocate

from app.models.alert import Alert
from app.models.drone import Drone, DroneStatus
from app.models.mission import Mission
from app.models.task import Task, TaskStatus
from app.models.waypoint import Waypoint

logger = logging.getLogger(__name__)

GRID_WIDTH = 1000
GRID_HEIGHT = 1000
GRID_CELL_SIZE = 1.0

# Cells of padding between the grid's south-west corner and the nearest
# endpoint, so neither sits exactly on the boundary.
GRID_MARGIN_CELLS = 5


def create_mission(db, payload):
    """Plan a mission: persist the route, assign drones, and plot their paths.

    Allocation and path planning are best-effort. A mission with no available
    drones, or whose routes cannot be planned, is still created — it just
    lands with fewer tasks.
    """
    mission = Mission(
        name=payload.name,
        description=payload.description,
        created_by=payload.created_by,
    )
    db.add(mission)
    db.flush()  # assigns mission.id without ending the transaction

    waypoints = []
    for index, waypoint in enumerate(payload.waypoints):
        record = Waypoint(
            mission_id=mission.id,
            sequence_order=(
                index if waypoint.sequence_order is None else waypoint.sequence_order
            ),
            latitude=waypoint.latitude,
            longitude=waypoint.longitude,
            altitude=waypoint.altitude,
        )
        db.add(record)
        waypoints.append(record)

    db.flush()  # assigns waypoint ids for the allocator
    _assign_tasks(db, mission, waypoints)

    db.commit()
    db.refresh(mission)
    return mission


def _assign_tasks(db, mission, waypoints):
    """Allocate idle drones to waypoints and plot a route for each pair."""
    if not waypoints:
        logger.warning("Mission %s has no waypoints; nothing to allocate", mission.id)
        return

    drones = _available_drones(db)
    if not drones:
        logger.warning(
            "Mission %s created with no IDLE drones available; no tasks assigned",
            mission.id,
        )
        return

    drone_payload = [
        {
            "id": drone.id,
            "lat": drone.current_lat,
            "lon": drone.current_lon,
            # An unknown charge is treated as empty, so a drone we know
            # nothing about is the last one the allocator reaches for.
            "battery_level": 0.0 if drone.battery_level is None else drone.battery_level,
        }
        for drone in drones
    ]
    waypoint_payload = [
        {"id": waypoint.id, "lat": waypoint.latitude, "lon": waypoint.longitude}
        for waypoint in waypoints
    ]

    drones_by_id = {drone.id: drone for drone in drones}
    waypoints_by_id = {waypoint.id: waypoint for waypoint in waypoints}

    for assignment in allocate(drone_payload, waypoint_payload):
        drone = drones_by_id[assignment["drone_id"]]
        waypoint = waypoints_by_id[assignment["waypoint_id"]]

        db.add(
            Task(
                mission_id=mission.id,
                drone_id=drone.id,
                waypoint_id=waypoint.id,
                status=TaskStatus.PENDING,
                planned_path=plan_route(
                    drone.current_lat,
                    drone.current_lon,
                    waypoint.latitude,
                    waypoint.longitude,
                ),
            )
        )


def _available_drones(db):
    """Idle drones whose position is known.

    A drone with no fix cannot have a distance computed, so it is skipped
    rather than assigned on bad data.
    """
    idle = db.query(Drone).filter(Drone.status == DroneStatus.IDLE).all()
    positioned = [
        drone
        for drone in idle
        if drone.current_lat is not None and drone.current_lon is not None
    ]

    skipped = len(idle) - len(positioned)
    if skipped:
        logger.warning("Skipped %d idle drone(s) with no position fix", skipped)

    return positioned


def plan_route(start_lat, start_lon, goal_lat, goal_lon):
    """Plot an A* route between two positions.

    Returns a list of {"lat", "lon"} points, or None when the pair cannot be
    planned — the endpoints are further apart than the grid spans, or one of
    them is blocked.

    The grid's origin is its south-west corner, so it is anchored below and
    left of both endpoints rather than on the goal; anchoring it on the goal
    would put any drone south or west of the waypoint outside the grid.
    """
    margin_lat = GRID_MARGIN_CELLS * GRID_CELL_SIZE / METERS_PER_DEGREE_LAT
    origin_lat = min(start_lat, goal_lat) - margin_lat
    origin_lon = min(start_lon, goal_lon) - margin_lat  # scaled by Grid via cos(lat)

    grid = Grid(
        width=GRID_WIDTH,
        height=GRID_HEIGHT,
        cell_size=GRID_CELL_SIZE,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
    )

    try:
        path = AStarPlanner(grid).plan((start_lat, start_lon), (goal_lat, goal_lon))
    except ValueError as error:
        logger.warning(
            "Could not plan (%s, %s) -> (%s, %s): %s",
            start_lat,
            start_lon,
            goal_lat,
            goal_lon,
            error,
        )
        return None

    if not path:
        logger.warning("No route found between drone and waypoint")
        return None

    return [{"lat": lat, "lon": lon} for lat, lon in path]


def get_missions(db, status=None):
    """Return missions newest first, each with its task count attached.

    One aggregate query rather than counting per mission, so the list scales
    with mission count instead of mission count times task count.
    """
    query = (
        db.query(Mission, func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.mission_id == Mission.id)
        .group_by(Mission.id)
    )
    if status is not None:
        query = query.filter(Mission.status == status)

    return [
        {
            "id": mission.id,
            "name": mission.name,
            "status": mission.status,
            "created_at": mission.created_at,
            "task_count": task_count,
        }
        for mission, task_count in query.order_by(Mission.created_at.desc()).all()
    ]


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
