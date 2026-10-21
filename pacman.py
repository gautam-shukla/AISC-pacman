"""
pacman.py - Player entity with responsive grid navigation and mouth animation.
"""
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
        """Move between tile centers; turns and wall checks occur at boundaries."""
        center_x = (self.col + 0.5) * TILE_SIZE
        center_y = (self.row + 0.5) * TILE_SIZE
        at_center = abs(self.x - center_x) < 0.01 and abs(self.y - center_y) < 0.01

        if at_center:
            if self.next_dir != Direction.NONE:
                next_col = self.col + self.next_dir[0]
                next_row = self.row + self.next_dir[1]
                if maze.is_walkable(next_col, next_row):
                    self.current_dir = self.next_dir
            dx, dy = self.current_dir
            if dx or dy:
                next_col = self.col + dx
                next_row = self.row + dy
                if not maze.is_walkable(next_col, next_row):
                    self.current_dir = Direction.NONE

        dx, dy = self.current_dir
        if not (dx or dy):
            return

        next_col = self.col + dx
        next_row = self.row + dy
        if not maze.is_walkable(next_col, next_row):
            self.current_dir = Direction.NONE
            return

        destination_x = (next_col + 0.5) * TILE_SIZE
        destination_y = (next_row + 0.5) * TILE_SIZE
        if dx:
            remaining = abs(destination_x - self.x)
            step = min(self.speed, remaining)
            self.x += dx * step
            if step >= remaining:
                self.x = destination_x
                self.col = next_col
                self.row = next_row
        else:
            remaining = abs(destination_y - self.y)
            step = min(self.speed, remaining)
            self.y += dy * step
            if step >= remaining:
                self.y = destination_y
                self.col = next_col
                self.row = next_row

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
