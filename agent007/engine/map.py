"""Tile-based map system for the raycaster."""

from __future__ import annotations

import json
from pathlib import Path

# Tile types
EMPTY = 0
WALL = 1
# Future: DOOR = 2, WINDOW = 3, PICKUP = 4, ENEMY_SPAWN = 5

# Wall colors (R, G, B) — distinct per facing for visual feedback
WALL_COLORS = {
    "north": (200, 60, 60),   # Red-ish
    "south": (180, 50, 180),  # Purple
    "east":  (60, 60, 200),   # Blue-ish
    "west":  (60, 180, 60),   # Green
}


class Map:
    """2D grid map with collision and metadata."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid: list[list[int]] = [
            [WALL if x == 0 or x == width - 1 or y == 0 or y == height - 1 else EMPTY]
            for x in range(width)
        ]
        # Actually build the grid properly
        self.grid = [[EMPTY for _ in range(width)] for _ in range(height)]
        for y in range(height):
            for x in range(width):
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    self.grid[y][x] = WALL

    @classmethod
    def from_string(cls, map_str: str) -> Map:
        """Parse an ASCII map. '#' = wall, ' ' or '.' = empty."""
        lines = [line.rstrip() for line in map_str.strip().split("\n") if line.strip()]
        height = len(lines)
        width = max(len(line) for line in lines)
        m = cls.__new__(cls)
        m.width = width
        m.height = height
        m.grid = [[EMPTY for _ in range(width)] for _ in range(height)]
        for y, line in enumerate(lines):
            for x, ch in enumerate(line):
                m.grid[y][x] = WALL if ch == "#" else EMPTY
        return m

    def is_solid(self, x: float, y: float) -> bool:
        """True if the tile at (x, y) is a wall."""
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= self.width or iy < 0 or iy >= self.height:
            return True
        return self.grid[iy][ix] == WALL

    def get_tile(self, x: int, y: int) -> int:
        """Get tile type at integer coordinates."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return WALL
        return self.grid[y][x]

    def to_json(self, path: str | Path) -> None:
        """Export map to JSON."""
        with open(path, "w") as f:
            json.dump(self.grid, f)

    @classmethod
    def from_json(cls, path: str | Path) -> Map:
        """Import map from JSON."""
        with open(path) as f:
            grid = json.load(f)
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        m = cls.__new__(cls)
        m.width = width
        m.height = height
        m.grid = grid
        return m

    def __repr__(self) -> str:
        return f"Map({self.width}x{self.height})"


# Default test map — a small secret facility
FACILITY_MAP = Map.from_string(
    """
################
#..............#
#..##.....##...#
#..............#
#..............#
#....###.......#
#..............#
#..............#
#..#.......#...#
#..#.......#...#
#..#.......#...#
#..............#
#..............#
#..............#
#..............#
################
"""
)