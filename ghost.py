"""
ghost.py - Ghost entity for baseline gameplay with legal movement and collision bounds.
"""
import random
from typing import Tuple, List, Optional
import pygame
from settings import (
    TILE_SIZE,
    GHOST_SPEED,
    COLOR_GHOST_RED,
    Direction,
)
from maze import Maze


class Ghost:
    """Baseline Ghost entity that respects maze walls and navigates legal pathways."""

    def __init__(self, col: int, row: int, color: Tuple[int, int, int] = COLOR_GHOST_RED):
        self.spawn_col = col
        self.spawn_row = row
        self.col = col
        self.row = row

        self.x = (col + 0.5) * TILE_SIZE
        self.y = (row + 0.5) * TILE_SIZE

        self.current_dir: Tuple[int, int] = Direction.LEFT
        self.speed = GHOST_SPEED
        self.color = color
        self.radius = int(TILE_SIZE * 0.45)

    def get_legal_directions(self, current_col: int, current_row: int, maze: Maze) -> List[Tuple[int, int]]:
        """Returns all walkable cardinal directions from the given tile."""
        legal = []
        for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
            dx, dy = direction
            if maze.is_walkable(current_col + dx, current_row + dy):
                legal.append(direction)
        return legal

    def update(self, maze: Maze) -> None:
        """Navigates the maze tile-by-tile, choosing legal directions at intersections."""
        current_col = int(self.x // TILE_SIZE)
        current_row = int(self.y // TILE_SIZE)
        tile_center_x = (current_col + 0.5) * TILE_SIZE
        tile_center_y = (current_row + 0.5) * TILE_SIZE

        # Check if ghost is close to the tile center (within one frame's travel)
        at_center_x = abs(self.x - tile_center_x) <= (self.speed / 2.0)
        at_center_y = abs(self.y - tile_center_y) <= (self.speed / 2.0)

        if at_center_x and at_center_y:
            # Snap to center
            self.x = tile_center_x
            self.y = tile_center_y
            self.col = current_col
            self.row = current_row

            legal_dirs = self.get_legal_directions(current_col, current_row, maze)
            opposite = Direction.OPPOSITES.get(self.current_dir)

            # Do not reverse direction unless at a dead end
            forward_dirs = [d for d in legal_dirs if d != opposite]

            if forward_dirs:
                # If current direction is still open, biased choice to maintain momentum
                if self.current_dir in forward_dirs and random.random() < 0.65:
                    pass  # keep current direction
                else:
                    self.current_dir = random.choice(forward_dirs)
            elif legal_dirs:
                # Dead end: must reverse
                self.current_dir = legal_dirs[0]
            else:
                self.current_dir = Direction.NONE

        # Advance along current direction
        dx, dy = self.current_dir
        if dx != 0 or dy != 0:
            target_x = self.x + (dx * self.speed)
            target_y = self.y + (dy * self.speed)

            # Prevent stepping inside walls
            next_col = int(target_x // TILE_SIZE)
            next_row = int(target_y // TILE_SIZE)

            if not maze.is_wall(next_col, next_row):
                self.x = target_x
                self.y = target_y
            else:
                self.x = tile_center_x
                self.y = tile_center_y

        self.col = int(self.x // TILE_SIZE)
        self.row = int(self.y // TILE_SIZE)

    def get_rect(self) -> pygame.Rect:
        """Returns the bounding rectangle for ghost collisions."""
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

    def reset_position(self) -> None:
        """Resets the ghost back to its spawn position."""
        self.col = self.spawn_col
        self.row = self.spawn_row
        self.x = (self.col + 0.5) * TILE_SIZE
        self.y = (self.row + 0.5) * TILE_SIZE
        self.current_dir = Direction.LEFT
