"""
maze.py - Grid representation, wall collision checking, collectible tracking.
"""
from typing import List, Tuple, Set, Optional
from settings import (
    TILE_SIZE,
    GRID_COLS,
    GRID_ROWS,
    DOT_POINTS,
    POWER_PELLET_POINTS,
    DEFAULT_MAZE,
)


class Maze:
    """Manages the grid layout, walls, collectible dots, and pellets."""

    def __init__(self, layout: Optional[List[str]] = None):
        self.layout_strings = layout or DEFAULT_MAZE
        self.rows = len(self.layout_strings)
        self.cols = len(self.layout_strings[0]) if self.rows > 0 else 0

        self.walls: Set[Tuple[int, int]] = set()
        self.dots: Set[Tuple[int, int]] = set()
        self.power_pellets: Set[Tuple[int, int]] = set()
        self.initial_dots: Set[Tuple[int, int]] = set()
        self.initial_power_pellets: Set[Tuple[int, int]] = set()

        self.pacman_spawn: Tuple[int, int] = (10, 14)
        self.ghost_spawns: List[Tuple[int, int]] = []

        self._parse_layout()

    def _parse_layout(self) -> None:
        """Parses layout strings into coordinate sets."""
        for r, line in enumerate(self.layout_strings):
            for c, char in enumerate(line):
                if char == "#":
                    self.walls.add((c, r))
                elif char == ".":
                    self.dots.add((c, r))
                elif char == "o":
                    self.power_pellets.add((c, r))
                elif char == "P":
                    self.pacman_spawn = (c, r)
                elif char == "G":
                    self.ghost_spawns.append((c, r))

        if not self.ghost_spawns:
            self.ghost_spawns.append((10, 10))

        # Store initial collectible sets for resets
        self.initial_dots = set(self.dots)
        self.initial_power_pellets = set(self.power_pellets)

    def is_wall(self, col: int, row: int) -> bool:
        """Returns True if the grid coordinate is a wall or outside boundaries."""
        if col < 0 or col >= self.cols or row < 0 or row >= self.rows:
            return True
        return (col, row) in self.walls

    def is_walkable(self, col: int, row: int) -> bool:
        """Returns True if the tile is within bounds and not blocked by a wall."""
        return not self.is_wall(col, row)

    def eat_dot(self, col: int, row: int) -> int:
        """Removes a normal dot at (col, row) if present. Returns points earned."""
        if (col, row) in self.dots:
            self.dots.remove((col, row))
            return DOT_POINTS
        return 0

    def eat_power_pellet(self, col: int, row: int) -> int:
        """Removes a power pellet at (col, row) if present. Returns points earned."""
        if (col, row) in self.power_pellets:
            self.power_pellets.remove((col, row))
            return POWER_PELLET_POINTS
        return 0

    def total_dots_count(self) -> int:
        """Returns total initial collectibles."""
        return len(self.initial_dots) + len(self.initial_power_pellets)

    def remaining_dots_count(self) -> int:
        """Returns total remaining collectibles in the maze."""
        return len(self.dots) + len(self.power_pellets)

    def reset_collectibles(self) -> None:
        """Restores all dots and power pellets."""
        self.dots = set(self.initial_dots)
        self.power_pellets = set(self.initial_power_pellets)
