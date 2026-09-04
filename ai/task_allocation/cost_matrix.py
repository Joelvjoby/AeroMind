"""Cost matrix construction for multi-drone task allocation."""

import numpy as np


def euclidean_distance(lat1, lon1, lat2, lon2):
    """Planar distance between two lat/lon points.

    Good enough for local-scale simulation; swap for haversine when
    missions span large geographic areas.
    """
    return float(np.hypot(lat1 - lat2, lon1 - lon2))


def battery_weight(battery_level):
    """Penalty multiplier for a drone's remaining charge.

    battery_level is normalised to [0, 1]. A full battery yields a weight
    of 1.0 (no penalty); an empty one yields 2.0 (double cost), so the
    allocator prefers healthier drones when distances are comparable.
    """
    return 1.0 + (1.0 - battery_level)


def build_cost_matrix(drones, waypoints):
    """Build the drone-by-waypoint cost matrix.

    Args:
        drones: list of dicts with keys {id, lat, lon, battery_level}
        waypoints: list of dicts with keys {id, lat, lon}

    Returns:
        np.ndarray of shape (len(drones), len(waypoints)) where cell [i, j]
        is the cost of sending drone i to waypoint j.
    """
    matrix = np.zeros((len(drones), len(waypoints)), dtype=float)

    for i, drone in enumerate(drones):
        weight = battery_weight(drone["battery_level"])
        for j, waypoint in enumerate(waypoints):
            distance = euclidean_distance(
                drone["lat"], drone["lon"], waypoint["lat"], waypoint["lon"]
            )
            matrix[i, j] = distance * weight

    return matrix
