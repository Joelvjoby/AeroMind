"""Tests for the A* path planning module."""

import logging

import pytest

from path_planning.astar import AStarPlanner
from path_planning.grid import BLOCKED, FREE, Grid


def make_grid(width=10, height=10, cell_size=10.0):
    return Grid(width=width, height=height, cell_size=cell_size)


def block(grid, *cells):
    """Block cells by (row, col), driving the public lat/lon obstacle API."""
    for row, col in cells:
        grid.set_obstacle(*grid.to_world_coords(row, col))


def as_cells(grid, path):
    """Convert a (lat, lon) path back to (row, col) cells."""
    return [grid.to_grid_coords(lat, lon) for lat, lon in path]


def assert_valid_path(grid, cells, start, goal):
    """A path must run start-to-goal in contiguous, unobstructed steps."""
    assert cells[0] == start
    assert cells[-1] == goal

    for row, col in cells:
        assert not grid.is_blocked_cell(row, col), f"path crosses obstacle at {(row, col)}"

    for (r1, c1), (r2, c2) in zip(cells, cells[1:]):
        assert max(abs(r2 - r1), abs(c2 - c1)) == 1, "path has a gap or repeat"


class TestGrid:
    """Coordinate conversion and occupancy bookkeeping."""

    def test_cell_to_world_and_back_round_trips(self):
        grid = make_grid()

        for cell in [(0, 0), (3, 7), (9, 9)]:
            assert grid.to_grid_coords(*grid.to_world_coords(*cell)) == cell

    def test_grid_starts_empty(self):
        grid = make_grid()

        assert (grid.cells == FREE).all()
        assert not grid.is_blocked(*grid.to_world_coords(4, 4))

    def test_set_obstacle_marks_only_that_cell(self):
        grid = make_grid()
        block(grid, (4, 4))

        assert grid.cells[4, 4] == BLOCKED
        assert grid.is_blocked(*grid.to_world_coords(4, 4))
        assert not grid.is_blocked(*grid.to_world_coords(4, 5))

    def test_outside_the_area_counts_as_blocked(self):
        grid = make_grid()

        assert grid.is_blocked_cell(-1, 0)
        assert grid.is_blocked_cell(0, 10)
        assert not grid.in_bounds(10, 10)


class TestStraightLine:
    """No obstacles — the planner should not wander."""

    def test_walks_directly_along_the_row(self):
        grid = make_grid()
        planner = AStarPlanner(grid)

        path = planner.plan(grid.to_world_coords(0, 0), grid.to_world_coords(0, 9))

        # Diagonal detours cost sqrt(2) per step, so the straight run is the
        # unique optimum here.
        assert as_cells(grid, path) == [(0, col) for col in range(10)]

    def test_same_start_and_goal_returns_single_point(self):
        grid = make_grid()
        planner = AStarPlanner(grid)

        start = grid.to_world_coords(3, 3)
        path = planner.plan(start, start)

        assert as_cells(grid, path) == [(3, 3)]


class TestSingleObstacle:
    """One blocked cell sitting on the direct line."""

    def test_routes_around_the_obstacle(self):
        grid = make_grid()
        block(grid, (0, 5))
        planner = AStarPlanner(grid)

        path = planner.plan(grid.to_world_coords(0, 0), grid.to_world_coords(0, 9))
        cells = as_cells(grid, path)

        assert_valid_path(grid, cells, start=(0, 0), goal=(0, 9))
        assert (0, 5) not in cells

    def test_detour_uses_diagonals_and_stays_tight(self):
        grid = make_grid()
        block(grid, (0, 5))
        planner = AStarPlanner(grid)

        path = planner.plan(grid.to_world_coords(0, 0), grid.to_world_coords(0, 9))
        cells = as_cells(grid, path)

        # Two diagonal steps hop around the single blocked cell, so the path
        # is the same length as the unobstructed run and never leaves row 1.
        assert len(cells) == 10
        assert max(row for row, _ in cells) == 1


class TestWallOfObstacles:
    """A full-height wall with a single gap must be funnelled through."""

    def test_path_passes_through_the_only_gap(self):
        grid = make_grid()
        block(grid, *[(row, 5) for row in range(9)])  # gap left at (9, 5)
        planner = AStarPlanner(grid)

        path = planner.plan(grid.to_world_coords(0, 0), grid.to_world_coords(0, 9))
        cells = as_cells(grid, path)

        assert_valid_path(grid, cells, start=(0, 0), goal=(0, 9))
        assert (9, 5) in cells

    def test_wall_without_a_gap_has_no_path(self):
        grid = make_grid()
        block(grid, *[(row, 5) for row in range(10)])
        planner = AStarPlanner(grid)

        path = planner.plan(grid.to_world_coords(0, 0), grid.to_world_coords(0, 9))

        assert path == []


class TestNoPathExists:
    """Goal is reachable-looking but sealed off entirely."""

    def setup_method(self):
        self.grid = make_grid()
        # Ring the goal at (5, 5) with obstacles, leaving the goal itself free.
        block(
            self.grid,
            *[
                (5 + d_row, 5 + d_col)
                for d_row in (-1, 0, 1)
                for d_col in (-1, 0, 1)
                if (d_row, d_col) != (0, 0)
            ],
        )
        self.planner = AStarPlanner(self.grid)

    def test_returns_empty_list(self):
        path = self.planner.plan(
            self.grid.to_world_coords(0, 0), self.grid.to_world_coords(5, 5)
        )

        assert path == []

    def test_logs_a_warning(self, caplog):
        with caplog.at_level(logging.WARNING, logger="path_planning.astar"):
            self.planner.plan(
                self.grid.to_world_coords(0, 0), self.grid.to_world_coords(5, 5)
            )

        assert "No path found" in caplog.text


class TestBlockedEndpoints:
    """Unusable endpoints are a caller error, not an empty result."""

    def test_blocked_start_raises(self):
        grid = make_grid()
        block(grid, (0, 0))
        planner = AStarPlanner(grid)

        with pytest.raises(ValueError, match="start"):
            planner.plan(grid.to_world_coords(0, 0), grid.to_world_coords(9, 9))

    def test_blocked_goal_raises(self):
        grid = make_grid()
        block(grid, (9, 9))
        planner = AStarPlanner(grid)

        with pytest.raises(ValueError, match="goal"):
            planner.plan(grid.to_world_coords(0, 0), grid.to_world_coords(9, 9))

    def test_endpoint_outside_the_area_raises(self):
        grid = make_grid()
        planner = AStarPlanner(grid)

        with pytest.raises(ValueError, match="outside the mission area"):
            planner.plan((-1.0, -1.0), grid.to_world_coords(9, 9))
