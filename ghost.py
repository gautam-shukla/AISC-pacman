"""Minimax-controlled ghosts with wall-safe movement and frightened behavior."""
import random
from typing import List, Optional, Sequence, Tuple

import pygame

from ghost_minimax import GhostMinimaxPlanner, Tile
from maze import Maze
from pacman import Pacman
from settings import (
    COLOR_GHOST_CYAN,
    COLOR_GHOST_FLEE,
    COLOR_GHOST_ORANGE,
    COLOR_GHOST_PINK,
    COLOR_GHOST_RED,
    GHOST_SPEED,
    GHOST_PROXIMITY_RANGE_TILES,
    GHOST_PROXIMITY_SPEED_BONUS,
    GHOST_LOW_LIVES_SPEED_REDUCTION,
    GHOST_MAX_LIVES_SPEED_REDUCTION,
    INITIAL_LIVES,
    TILE_SIZE,
    Direction,
    DIFFICULTY_MIN,
    DIFFICULTY_MAX,
    GhostState,
    GhostType,
    GHOST_MINIMAX_SEARCH_DEPTH,
    POWER_PELLET_DURATION,
)

DirectionVector = Tuple[int, int]

GHOST_COLORS = {
    GhostType.HUNTER: COLOR_GHOST_RED,
    GhostType.AMBUSHER: COLOR_GHOST_PINK,
    GhostType.PATROL: COLOR_GHOST_CYAN,
    GhostType.GUARD: COLOR_GHOST_ORANGE,
}


class Ghost:
    """A Minimax-controlled ghost with the existing visual role and flee state."""

    def __init__(
        self,
        col: int,
        row: int,
        color: Optional[Tuple[int, int, int]] = None,
        ghost_type: GhostType = GhostType.HUNTER,
        minimax_depth: int = GHOST_MINIMAX_SEARCH_DEPTH,
        random_seed: int | None = None,
    ):
        self.spawn_col = col
        self.spawn_row = row
        self.col = col
        self.row = row
        self.x = (col + 0.5) * TILE_SIZE
        self.y = (row + 0.5) * TILE_SIZE
        self.current_dir: DirectionVector = Direction.NONE
        self.ghost_type = ghost_type
        self.base_color = color if color is not None else GHOST_COLORS[ghost_type]
        self.color = self.base_color
        self.speed = GHOST_SPEED
        self.radius = int(TILE_SIZE * 0.45)
        self.state = (
            GhostState.PATROL
            if ghost_type in (GhostType.PATROL, GhostType.GUARD)
            else GhostState.CHASE
        )
        self.minimax = GhostMinimaxPlanner(
            depth=minimax_depth,
            random_seed=random_seed,
        )

    def get_legal_directions(
        self, current_col: int, current_row: int, maze: Maze
    ) -> List[DirectionVector]:
        """Return walkable cardinal directions from a tile."""
        legal = []
        for direction in (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT):
            dx, dy = direction
            if maze.is_walkable(current_col + dx, current_row + dy):
                legal.append(direction)
        return legal

    def update(
        self,
        maze: Maze,
        pacman: Optional[Pacman] = None,
        player_lives: int = 3,
        protection: float = 0.0,
        difficulty_multiplier: float = 1.0,
        other_ghosts: Sequence[Tile] = (),
    ) -> None:
        """Update ghost movement; protection and difficulty are normalized ratios."""
        difficulty_multiplier = min(
            DIFFICULTY_MAX, max(DIFFICULTY_MIN, difficulty_multiplier)
        )
        center_x = (self.col + 0.5) * TILE_SIZE
        center_y = (self.row + 0.5) * TILE_SIZE
        at_center = (
            abs(self.x - center_x) < 0.01
            and abs(self.y - center_y) < 0.01
        )

        if at_center:
            self.x = center_x
            self.y = center_y

            if pacman is None:
                legal = self.get_legal_directions(self.col, self.row, maze)
                reverse = Direction.OPPOSITES.get(self.current_dir)
                options = [direction for direction in legal if direction != reverse]
                self.current_dir = random.choice(options or legal) if legal else Direction.NONE
                self.state = GhostState.PATROL
                self.color = self.base_color
                self.speed = GHOST_SPEED
            else:
                player_tile = (pacman.col, pacman.row)
                frightened = protection > 0
                if frightened:
                    self.state = GhostState.FLEE
                    self.color = COLOR_GHOST_FLEE
                else:
                    self.state = GhostState.CHASE
                    self.color = self.base_color
                distance = abs(self.col - pacman.col) + abs(self.row - pacman.row)
                proximity_bonus = (
                    max(0, GHOST_PROXIMITY_RANGE_TILES - distance)
                    / GHOST_PROXIMITY_RANGE_TILES
                    * GHOST_PROXIMITY_SPEED_BONUS
                )
                lives_relief = min(
                    max(0, INITIAL_LIVES - player_lives)
                    * GHOST_LOW_LIVES_SPEED_REDUCTION,
                    GHOST_MAX_LIVES_SPEED_REDUCTION,
                )
                self.speed = (
                    GHOST_SPEED
                    * (1.0 + proximity_bonus)
                    * (1.0 - lives_relief)
                    * difficulty_multiplier
                )
                self.current_dir = self.minimax.choose_action(
                    maze,
                    player_tile,
                    (self.col, self.row),
                    self.current_dir,
                    other_ghosts,
                    power_active=frightened,
                    player_lives=player_lives,
                    power_ticks_remaining=(
                        round(protection * POWER_PELLET_DURATION)
                    ),
                    ghost_speed=self.speed,
                    pacman_direction=pacman.current_dir,
                )

        if pacman is not None:
            if protection > 0:
                self.state = GhostState.FLEE
                self.color = COLOR_GHOST_FLEE
            elif self.state == GhostState.FLEE:
                self.color = self.base_color

        dx, dy = self.current_dir
        if dx or dy:
            next_col = self.col + dx
            next_row = self.row + dy
            if not maze.is_walkable(next_col, next_row):
                self.current_dir = Direction.NONE
                return

            destination_x = (next_col + 0.5) * TILE_SIZE
            destination_y = (next_row + 0.5) * TILE_SIZE
            if dx:
                distance_to_center = abs(destination_x - self.x)
                step = min(self.speed, distance_to_center)
                self.x += dx * step
                if step >= distance_to_center:
                    self.x = destination_x
                    self.col = next_col
            else:
                distance_to_center = abs(destination_y - self.y)
                step = min(self.speed, distance_to_center)
                self.y += dy * step
                if step >= distance_to_center:
                    self.y = destination_y
                    self.row = next_row

    def get_rect(self) -> pygame.Rect:
        """Return the bounding rectangle used for ghost collisions."""
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

    def reset_position(self) -> None:
        """Reset the ghost to its spawn and initial behavior."""
        self.col = self.spawn_col
        self.row = self.spawn_row
        self.x = (self.col + 0.5) * TILE_SIZE
        self.y = (self.row + 0.5) * TILE_SIZE
        self.current_dir = Direction.NONE
        self.state = (
            GhostState.PATROL
            if self.ghost_type in (GhostType.PATROL, GhostType.GUARD)
            else GhostState.CHASE
        )
        self.color = self.base_color
        self.speed = GHOST_SPEED
