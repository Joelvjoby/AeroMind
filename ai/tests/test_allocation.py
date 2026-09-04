"""Tests for the Hungarian-algorithm task allocator."""

import pytest

from task_allocation.allocator import allocate, reallocate


def drone(id_, lat, lon, battery_level=1.0):
    return {"id": id_, "lat": lat, "lon": lon, "battery_level": battery_level}


def waypoint(id_, lat, lon):
    return {"id": id_, "lat": lat, "lon": lon}


def pairs(assignments):
    """Reduce assignments to a comparable set of (drone_id, waypoint_id)."""
    return {(a["drone_id"], a["waypoint_id"]) for a in assignments}


class TestSquareAllocation:
    """3 drones, 3 waypoints — every drone and waypoint is covered."""

    def setup_method(self):
        self.drones = [drone("d1", 0.0, 0.0), drone("d2", 10.0, 0.0), drone("d3", 20.0, 0.0)]
        self.waypoints = [waypoint("w1", 0.0, 0.0), waypoint("w2", 10.0, 0.0), waypoint("w3", 20.0, 0.0)]

    def test_every_drone_and_waypoint_assigned_once(self):
        result = allocate(self.drones, self.waypoints)

        assert len(result) == 3
        assert len({a["drone_id"] for a in result}) == 3
        assert len({a["waypoint_id"] for a in result}) == 3

    def test_picks_the_nearest_pairing(self):
        result = allocate(self.drones, self.waypoints)

        assert pairs(result) == {("d1", "w1"), ("d2", "w2"), ("d3", "w3")}
        assert all(a["cost"] == pytest.approx(0.0) for a in result)

    def test_low_battery_drone_is_penalised_in_cost(self):
        # A half-charged drone one unit away costs 1 * (1 + 0.5) = 1.5
        drones = [drone("d1", 0.0, 0.0, battery_level=0.5)]
        result = allocate(drones, [waypoint("w1", 1.0, 0.0)])

        assert result[0]["cost"] == pytest.approx(1.5)


class TestMoreDronesThanWaypoints:
    """4 drones, 2 waypoints — the two best drones fly, the rest idle."""

    def setup_method(self):
        self.drones = [
            drone("near1", 0.0, 0.0),
            drone("near2", 5.0, 0.0),
            drone("far1", 100.0, 100.0),
            drone("far2", 200.0, 200.0),
        ]
        self.waypoints = [waypoint("w1", 0.0, 0.0), waypoint("w2", 5.0, 0.0)]

    def test_assignment_count_matches_waypoints(self):
        result = allocate(self.drones, self.waypoints)

        assert len(result) == 2
        assert len({a["drone_id"] for a in result}) == 2

    def test_surplus_drones_are_left_unassigned(self):
        result = allocate(self.drones, self.waypoints)

        assert pairs(result) == {("near1", "w1"), ("near2", "w2")}
        assigned = {a["drone_id"] for a in result}
        assert "far1" not in assigned
        assert "far2" not in assigned


class TestMoreWaypointsThanDrones:
    """2 drones, 4 waypoints — only two waypoints get covered this round."""

    def setup_method(self):
        self.drones = [drone("d1", 0.0, 0.0), drone("d2", 30.0, 0.0)]
        self.waypoints = [
            waypoint("w1", 0.0, 0.0),
            waypoint("w2", 10.0, 0.0),
            waypoint("w3", 30.0, 0.0),
            waypoint("w4", 60.0, 0.0),
        ]

    def test_assignment_count_matches_drones(self):
        result = allocate(self.drones, self.waypoints)

        assert len(result) == 2
        assert len({a["waypoint_id"] for a in result}) == 2

    def test_closest_waypoints_are_chosen(self):
        result = allocate(self.drones, self.waypoints)

        assert pairs(result) == {("d1", "w1"), ("d2", "w3")}


class TestReallocation:
    """A drone drops out mid-mission and work is redistributed."""

    def setup_method(self):
        self.drones = [drone("d1", 0.0, 0.0), drone("d2", 10.0, 0.0), drone("d3", 20.0, 0.0)]
        self.waypoints = [waypoint("w1", 0.0, 0.0), waypoint("w2", 10.0, 0.0), waypoint("w3", 20.0, 0.0)]

    def test_failed_drone_is_excluded(self):
        result = reallocate(self.drones, self.waypoints, failed_drone_id="d2")

        assert "d2" not in {a["drone_id"] for a in result}

    def test_surviving_drones_are_all_reassigned(self):
        result = reallocate(self.drones, self.waypoints, failed_drone_id="d2")

        assert len(result) == 2
        assert {a["drone_id"] for a in result} == {"d1", "d3"}

    def test_orphaned_waypoint_is_dropped_not_duplicated(self):
        # d2 owned w2; with two drones left only two waypoints can be served
        result = reallocate(self.drones, self.waypoints, failed_drone_id="d2")

        assert pairs(result) == {("d1", "w1"), ("d3", "w3")}

    def test_reallocating_the_last_drone_yields_nothing(self):
        result = reallocate([drone("d1", 0.0, 0.0)], self.waypoints, failed_drone_id="d1")

        assert result == []
