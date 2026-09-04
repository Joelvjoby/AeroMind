"""Optimal drone-to-waypoint assignment via the Hungarian algorithm."""

from scipy.optimize import linear_sum_assignment

from task_allocation.cost_matrix import build_cost_matrix


def allocate(drones, waypoints):
    """Assign drones to waypoints so total cost is minimised.

    Handles rectangular problems natively: when the counts differ, only
    min(len(drones), len(waypoints)) pairs are produced and the surplus
    drones or waypoints are left unassigned.

    Args:
        drones: list of dicts with keys {id, lat, lon, battery_level}
        waypoints: list of dicts with keys {id, lat, lon}

    Returns:
        list of {drone_id, waypoint_id, cost} dicts.
    """
    if not drones or not waypoints:
        return []

    cost_matrix = build_cost_matrix(drones, waypoints)
    row_indices, col_indices = linear_sum_assignment(cost_matrix)

    return [
        {
            "drone_id": drones[i]["id"],
            "waypoint_id": waypoints[j]["id"],
            "cost": float(cost_matrix[i, j]),
        }
        for i, j in zip(row_indices, col_indices)
    ]


def reallocate(drones, waypoints, failed_drone_id):
    """Re-run allocation from scratch with a failed drone removed.

    Args:
        drones: the original drone list
        waypoints: the waypoints still to be covered
        failed_drone_id: id of the drone that dropped out

    Returns:
        list of {drone_id, waypoint_id, cost} dicts over the surviving drones.
    """
    surviving = [d for d in drones if d["id"] != failed_drone_id]
    return allocate(surviving, waypoints)


def total_cost(assignments):
    """Sum the cost of an assignment list."""
    return sum(a["cost"] for a in assignments)
