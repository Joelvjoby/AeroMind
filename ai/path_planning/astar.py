"""A* pathfinding over a discretised mission area."""

import heapq
import logging
import math

logger = logging.getLogger(__name__)

STRAIGHT_COST = 1.0
DIAGONAL_COST = math.sqrt(2.0)

# 8-connected neighbourhood: (row delta, col delta, step cost in cell units).
NEIGHBOR_OFFSETS = (
    (-1, 0, STRAIGHT_COST),
    (1, 0, STRAIGHT_COST),
    (0, -1, STRAIGHT_COST),
    (0, 1, STRAIGHT_COST),
    (-1, -1, DIAGONAL_COST),
    (-1, 1, DIAGONAL_COST),
    (1, -1, DIAGONAL_COST),
    (1, 1, DIAGONAL_COST),
)


class AStarPlanner:
    """Plans obstacle-free routes across a `Grid` using A*.

    Costs are measured in cell units (1.0 per orthogonal step, sqrt(2) per
    diagonal) and the heuristic is straight-line Euclidean distance, which
    never overestimates those costs and so yields optimal paths.

    Diagonal moves past the corner of an obstacle are permitted — a drone
    flies over the gap rather than squeezing between two ground obstacles.
    """

    def __init__(self, grid):
        self.grid = grid

    def plan(self, start, goal):
        """Find a route between two world positions.

        Args:
            start: (lat, lon) of the departure point
            goal: (lat, lon) of the destination

        Returns:
            List of (lat, lon) waypoints at cell centres, ordered start to
            goal and inclusive of both. Empty if no route exists.

        Raises:
            ValueError: if either endpoint is blocked or outside the grid.
        """
        start_cell = self._resolve(start, "start")
        goal_cell = self._resolve(goal, "goal")

        cells = self._search(start_cell, goal_cell)
        if not cells:
            logger.warning(
                "No path found from cell %s to cell %s", start_cell, goal_cell
            )
            return []

        return [self.grid.to_world_coords(row, col) for row, col in cells]

    # -- internals -------------------------------------------------------------

    def _resolve(self, position, label):
        """Convert a world position to a cell, rejecting unusable endpoints."""
        row, col = self.grid.to_grid_coords(*position)

        if not self.grid.in_bounds(row, col):
            raise ValueError(f"{label} {position} is outside the mission area")
        if self.grid.is_blocked_cell(row, col):
            raise ValueError(f"{label} {position} is blocked by an obstacle")

        return row, col

    def _search(self, start, goal):
        """Run A* over cell coordinates; returns a cell path or []."""
        open_heap = [(self._heuristic(start, goal), start)]
        came_from = {}
        g_score = {start: 0.0}
        visited = set()

        while open_heap:
            _, current = heapq.heappop(open_heap)

            if current == goal:
                return self._reconstruct(came_from, current)
            if current in visited:
                continue
            visited.add(current)

            row, col = current
            for d_row, d_col, step in NEIGHBOR_OFFSETS:
                neighbor = (row + d_row, col + d_col)
                if self.grid.is_blocked_cell(*neighbor):
                    continue

                tentative = g_score[current] + step
                if tentative < g_score.get(neighbor, math.inf):
                    g_score[neighbor] = tentative
                    came_from[neighbor] = current
                    heapq.heappush(
                        open_heap, (tentative + self._heuristic(neighbor, goal), neighbor)
                    )

        return []

    @staticmethod
    def _heuristic(cell, goal):
        """Euclidean distance in cell units."""
        return math.hypot(cell[0] - goal[0], cell[1] - goal[1])

    @staticmethod
    def _reconstruct(came_from, current):
        """Walk parent links back to the start and return the forward path."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path
