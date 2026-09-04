"""Discretisation of a mission area into a flat 2D occupancy grid."""

import math

import numpy as np

FREE = 0
BLOCKED = 1

# Metres per degree of latitude. Longitude is scaled by cos(latitude) at the
# grid origin, which is accurate enough for the local-scale areas a single
# mission covers.
METERS_PER_DEGREE_LAT = 111_320.0


class Grid:
    """A rectangular mission area split into square cells.

    Cell (0, 0) sits at the origin corner; rows increase northward and
    columns increase eastward.

    Args:
        width: number of columns (east-west extent, in cells)
        height: number of rows (north-south extent, in cells)
        cell_size: edge length of one cell, in metres
        origin_lat: latitude of the grid's south-west corner
        origin_lon: longitude of the grid's south-west corner
    """

    def __init__(self, width, height, cell_size, origin_lat=0.0, origin_lon=0.0):
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if cell_size <= 0:
            raise ValueError("cell_size must be positive")

        cos_lat = math.cos(math.radians(origin_lat))
        if abs(cos_lat) < 1e-9:
            raise ValueError("origin_lat too close to a pole for planar projection")

        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.origin_lat = origin_lat
        self.origin_lon = origin_lon

        self.cells = np.full((height, width), FREE, dtype=np.uint8)
        self._meters_per_degree_lon = METERS_PER_DEGREE_LAT * cos_lat

    # -- coordinate conversion -------------------------------------------------

    def to_grid_coords(self, lat, lon):
        """Map a world position to the (row, col) cell containing it.

        The result may fall outside the grid; use `in_bounds` to check.
        """
        north_m = (lat - self.origin_lat) * METERS_PER_DEGREE_LAT
        east_m = (lon - self.origin_lon) * self._meters_per_degree_lon
        return (
            int(math.floor(north_m / self.cell_size)),
            int(math.floor(east_m / self.cell_size)),
        )

    def to_world_coords(self, row, col):
        """Map a cell to the (lat, lon) at its centre."""
        if not self.in_bounds(row, col):
            raise ValueError(f"cell ({row}, {col}) is outside the grid")

        north_m = (row + 0.5) * self.cell_size
        east_m = (col + 0.5) * self.cell_size
        return (
            self.origin_lat + north_m / METERS_PER_DEGREE_LAT,
            self.origin_lon + east_m / self._meters_per_degree_lon,
        )

    # -- occupancy -------------------------------------------------------------

    def in_bounds(self, row, col):
        """True if the cell lies inside the mission area."""
        return 0 <= row < self.height and 0 <= col < self.width

    def set_obstacle(self, lat, lon):
        """Mark the cell containing this position as BLOCKED."""
        row, col = self.to_grid_coords(lat, lon)
        if not self.in_bounds(row, col):
            raise ValueError(f"({lat}, {lon}) is outside the grid")
        self.cells[row, col] = BLOCKED

    def is_blocked(self, lat, lon):
        """True if this position is obstructed, or outside the mission area."""
        return self.is_blocked_cell(*self.to_grid_coords(lat, lon))

    def is_blocked_cell(self, row, col):
        """Cell-indexed occupancy test. Out-of-bounds counts as blocked."""
        if not self.in_bounds(row, col):
            return True
        return bool(self.cells[row, col] == BLOCKED)
