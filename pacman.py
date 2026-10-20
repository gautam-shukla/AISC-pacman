"""
pacman.py - Player entity with responsive grid navigation and mouth animation.
"""
import math
from typing import Tuple
import pygame
from settings import (
    TILE_SIZE,
    PACMAN_SPEED,
    Direction,
)
from maze import Maze


class Pacman:
    """Represents the player-controlled Pac-Man character."""

    def __init__(self, col: int, row: int):
        self.spawn_col = col
        self.spawn_row = row
        self.col = col
        self.row = row

        # Center-based pixel coordinates for smooth turning and rendering
        self.x = (col + 0.5) * TILE_SIZE
        self.y = (row + 0.5) * TILE_SIZE

        self.current_dir: Tuple[int, int] = Direction.NONE
        self.next_dir: Tuple[int, int] = Direction.NONE
        self.speed = PACMAN_SPEED

        # Animation states
        self.mouth_angle = 30.0
        self.mouth_opening = True
        self.mouth_speed = 3.5

        # Radius for collision and drawing
        self.radius = int(TILE_SIZE * 0.45)

    def set_next_direction(self, direction: Tuple[int, int]) -> None:
        """Buffers the player's requested movement direction."""
        self.next_dir = direction

    def update(self, maze: Maze) -> None:
        """Updates position, handles turns, and prevents moving into walls."""
        # 1. Immediate reversal check
        if self.next_dir == Direction.OPPOSITES.get(self.current_dir):
            self.current_dir = self.next_dir

        # Current center of the tile Pac-Man is currently in
        current_col = int(self.x // TILE_SIZE)
        current_row = int(self.y // TILE_SIZE)
        tile_center_x = (current_col + 0.5) * TILE_SIZE
        tile_center_y = (current_row + 0.5) * TILE_SIZE

        dist_to_center_x = self.x - tile_center_x
        dist_to_center_y = self.y - tile_center_y

        # Snap tolerance for turning into perpendicular corridors
        snap_threshold = self.speed * 1.5

        # 2. Check if we can execute the buffered next_dir
        if self.next_dir != Direction.NONE and self.next_dir != self.current_dir:
            ndx, ndy = self.next_dir
            # Perpendicular turn check
            if (ndx != 0 and abs(dist_to_center_y) <= snap_threshold) or \
               (ndy != 0 and abs(dist_to_center_x) <= snap_threshold):
                target_col = current_col + ndx
                target_row = current_row + ndy
                if maze.is_walkable(target_col, target_row):
                    # Snap to tile center along the perpendicular axis
                    if ndx != 0:
                        self.y = tile_center_y
                    if ndy != 0:
                        self.x = tile_center_x
                    self.current_dir = self.next_dir

        # 3. Attempt movement in current direction
        cdx, cdy = self.current_dir
        if cdx != 0 or cdy != 0:
            target_x = self.x + (cdx * self.speed)
            target_y = self.y + (cdy * self.speed)

            # Check collision with wall in current direction
            next_col = int(target_x // TILE_SIZE)
            next_row = int(target_y // TILE_SIZE)

            # Lookahead check when crossing the tile center boundary
            heading_into_wall = False
            if cdx > 0 and (target_x > tile_center_x) and maze.is_wall(current_col + 1, current_row):
                heading_into_wall = True
            elif cdx < 0 and (target_x < tile_center_x) and maze.is_wall(current_col - 1, current_row):
                heading_into_wall = True
            elif cdy > 0 and (target_y > tile_center_y) and maze.is_wall(current_col, current_row + 1):
                heading_into_wall = True
            elif cdy < 0 and (target_y < tile_center_y) and maze.is_wall(current_col, current_row - 1):
                heading_into_wall = True

            if heading_into_wall:
                # Stop smoothly at tile center
                if cdx != 0:
                    self.x = tile_center_x
                if cdy != 0:
                    self.y = tile_center_y
                self.current_dir = Direction.NONE
            else:
                self.x = target_x
                self.y = target_y

            # Update tile coordinates
            self.col = int(self.x // TILE_SIZE)
            self.row = int(self.y // TILE_SIZE)

            # Animate mouth only while moving
            self._animate_mouth()

    def _animate_mouth(self) -> None:
        """Oscillates the mouth opening angle for classic chomp animation."""
        if self.mouth_opening:
            self.mouth_angle += self.mouth_speed
            if self.mouth_angle >= 45.0:
                self.mouth_opening = False
        else:
            self.mouth_angle -= self.mouth_speed
            if self.mouth_angle <= 5.0:
                self.mouth_opening = True

    def get_facing_angle(self) -> float:
        """Returns the facing angle in degrees for rendering (Right=0, Up=90, Left=180, Down=270)."""
        cdx, cdy = self.current_dir
        if (cdx, cdy) == Direction.RIGHT:
            return 0.0
        elif (cdx, cdy) == Direction.UP:
            return 90.0
        elif (cdx, cdy) == Direction.LEFT:
            return 180.0
        elif (cdx, cdy) == Direction.DOWN:
            return 270.0
        return 0.0

    def get_rect(self) -> pygame.Rect:
        """Returns the bounding box rectangle for collision detection."""
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

    def reset_position(self) -> None:
        """Resets Pac-Man to the spawn tile."""
        self.col = self.spawn_col
        self.row = self.spawn_row
        self.x = (self.col + 0.5) * TILE_SIZE
        self.y = (self.row + 0.5) * TILE_SIZE
        self.current_dir = Direction.NONE
        self.next_dir = Direction.NONE
        self.mouth_angle = 30.0
