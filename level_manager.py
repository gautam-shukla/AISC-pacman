"""Level layouts and construction for the Pac-Man game."""
from typing import List, Optional, Sequence

from maze import Maze
from settings import DEFAULT_MAZE


def _build_level_two_layout() -> List[str]:
    rows = 25
    cols = 25
    grid = [["#"] * cols for _ in range(rows)]

    for row in range(1, rows - 1):
        for col in range(1, cols - 1):
            grid[row][col] = "."

    vertical_doors = {
        6: {3, 9, 15, 21},
        12: {2, 8, 14, 20},
        18: {3, 9, 15, 21},
    }
    for col, doors in vertical_doors.items():
        for row in range(1, rows - 1):
            if row not in doors:
                grid[row][col] = "#"

    horizontal_doors = {
        6: {2, 8, 14, 20},
        12: {3, 9, 15, 21},
        18: {2, 8, 14, 20},
    }
    for row, doors in horizontal_doors.items():
        for col in range(1, cols - 1):
            if col not in doors:
                grid[row][col] = "#"

    pacman_spawn = (2, 2)
    ghost_spawns = ((22, 2), (2, 22), (22, 22), (12, 2))
    power_pellets = ((2, 11), (22, 11), (2, 13), (22, 13))
    grid[pacman_spawn[1]][pacman_spawn[0]] = "P"
    for col, row in ghost_spawns:
        grid[row][col] = "G"
    for col, row in power_pellets:
        grid[row][col] = "o"
    return ["".join(row) for row in grid]


LEVEL_TWO_LAYOUT = tuple(_build_level_two_layout())


class LevelManager:
    """Create the requested maze while preserving a custom first-level layout."""

    def __init__(self, first_level_layout: Optional[Sequence[str]] = None):
        self.first_level_layout = tuple(first_level_layout or DEFAULT_MAZE)

    def load(self, level: int) -> Maze:
        if level == 1:
            return Maze(list(self.first_level_layout))
        if level == 2:
            return Maze(list(LEVEL_TWO_LAYOUT))
        raise ValueError(f"Unsupported level number: {level}")
