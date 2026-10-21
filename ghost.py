"""Role-based ghosts with wall-safe pathfinding and frightened behavior."""
import random
from typing import List, Optional, Tuple

import pygame

from maze import Maze
from pacman import Pacman
from pathfinding import a_star_search, distances_from
from settings import (
    COLOR_GHOST_CYAN,
    COLOR_GHOST_FLEE,
    COLOR_GHOST_ORANGE,
    COLOR_GHOST_PINK,
    COLOR_GHOST_RED,
    GHOST_SPEED,
    TILE_SIZE,
    Direction,
    GhostState,
    GhostType,
)

Tile = Tuple[int, int]
DirectionVector = Tuple[int, int]

GHOST_COLORS = {
    GhostType.HUNTER: COLOR_GHOST_RED,
    GhostType.AMBUSHER: COLOR_GHOST_PINK,
    GhostType.PATROL: COLOR_GHOST_CYAN,
    GhostType.GUARD: COLOR_GHOST_ORANGE,
}


class Ghost:
    """A ghost that chases, ambushes, patrols, guards, or flees Pac-Man."""

    def __init__(
        self,
        col: int,
        row: int,
        color: Optional[Tuple[int, int, int]] = None,
        ghost_type: GhostType = GhostType.HUNTER,
    ):
        self.spawn_col = col
        self.spawn_row = row
        self.col = col
        self.row = row
        self.x = (col + 0.5) * TILE_SIZE
        self.y = (row + 0.5) * TILE_SIZE
        self.current_dir: DirectionVector = Direction.LEFT
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
        self.patrol_targets: List[Tile] = []
        self.patrol_index = 0
        self.last_seen_player: Optional[Tile] = None

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

    @staticmethod
    def _manhattan(first: Tile, second: Tile) -> int:
        return abs(first[0] - second[0]) + abs(first[1] - second[1])

    def _get_patrol_targets(self, maze: Maze) -> List[Tile]:
        walkable = [
            (col, row)
            for row in range(maze.rows)
            for col in range(maze.cols)
            if maze.is_walkable(col, row)
        ]
        if not walkable:
            return [(self.spawn_col, self.spawn_row)]

        corners = (
            (1, 1),
            (maze.cols - 2, 1),
            (maze.cols - 2, maze.rows - 2),
            (1, maze.rows - 2),
        )
        targets: List[Tile] = []
        for corner in corners:
            nearest = min(walkable, key=lambda tile: self._manhattan(tile, corner))
            if nearest not in targets:
                targets.append(nearest)
        return targets or [walkable[0]]

    def _target_for_player(self, maze: Maze, pacman: Pacman) -> Tile:
        player_tile = (pacman.col, pacman.row)
        self.last_seen_player = player_tile

        if self.ghost_type == GhostType.HUNTER:
            self.state = GhostState.CHASE
            return player_tile

        if self.ghost_type == GhostType.AMBUSHER:
            self.state = GhostState.CHASE
            dx, dy = pacman.current_dir
            for lead in range(4, 0, -1):
                target = (pacman.col + dx * lead, pacman.row + dy * lead)
                if maze.is_walkable(*target):
                    return target
            return player_tile

        if not self.patrol_targets:
            self.patrol_targets = self._get_patrol_targets(maze)
        patrol_target = self.patrol_targets[self.patrol_index]
        distance = self._manhattan((self.col, self.row), player_tile)

        if self.ghost_type == GhostType.GUARD:
            if distance <= 5:
                self.state = GhostState.CHASE
                return player_tile
            self.state = GhostState.PATROL
            return patrol_target

        if distance <= 7:
            self.state = GhostState.SEARCH
            return player_tile
        self.state = GhostState.PATROL
        return patrol_target

    def _choose_direction(
        self,
        maze: Maze,
        pacman: Pacman,
        frightened: bool,
        target: Tile,
    ) -> None:
        legal = self.get_legal_directions(self.col, self.row, maze)
        if not legal:
            self.current_dir = Direction.NONE
            return

        reverse = Direction.OPPOSITES.get(self.current_dir)
        forward_options = [direction for direction in legal if direction != reverse]
        if not forward_options:
            forward_options = legal

        if frightened:
            distances = distances_from(maze, (pacman.col, pacman.row))
            self.current_dir = max(
                legal,
                key=lambda direction: distances.get(
                    (self.col + direction[0], self.row + direction[1]), -1
                ),
            )
            self.state = GhostState.FLEE
            return

        path = a_star_search(maze, (self.col, self.row), target)
        if len(path) > 1:
            next_tile = path[1]
            direction = (next_tile[0] - self.col, next_tile[1] - self.row)
            if direction in legal:
                self.current_dir = direction
                return
        self.current_dir = random.choice(forward_options)

    def update(
        self,
        maze: Maze,
        pacman: Optional[Pacman] = None,
        player_lives: int = 3,
        protection: float = 0.0,
    ) -> None:
        """Update ghost movement; ``protection`` is a 0-1 power duration ratio."""
        current_col = int(self.x // TILE_SIZE)
        current_row = int(self.y // TILE_SIZE)
        center_x = (current_col + 0.5) * TILE_SIZE
        center_y = (current_row + 0.5) * TILE_SIZE
        at_center = (
            abs(self.x - center_x) <= self.speed / 2
            and abs(self.y - center_y) <= self.speed / 2
        )

        if at_center:
            self.x = center_x
            self.y = center_y
            self.col = current_col
            self.row = current_row

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
                target = self._target_for_player(maze, pacman)
                if (
                    self.ghost_type in (GhostType.PATROL, GhostType.GUARD)
                    and self.state == GhostState.PATROL
                    and (self.col, self.row) == self.patrol_targets[self.patrol_index]
                ):
                    self.patrol_index = (self.patrol_index + 1) % len(self.patrol_targets)
                    target = self.patrol_targets[self.patrol_index]

                frightened = protection > 0
                if frightened:
                    self.state = GhostState.FLEE
                    self.color = COLOR_GHOST_FLEE
                else:
                    self.color = self.base_color
                distance = self._manhattan((self.col, self.row), player_tile)
                life_pressure = max(0, 2 - player_lives) / 20
                self.speed = GHOST_SPEED * (
                    1.0 + max(0, 8 - distance) / 40 + life_pressure
                )
                self._choose_direction(maze, pacman, frightened, target)

        if pacman is not None:
            if protection > 0:
                self.state = GhostState.FLEE
                self.color = COLOR_GHOST_FLEE
            elif self.state == GhostState.FLEE:
                self.color = self.base_color

        dx, dy = self.current_dir
        if dx or dy:
            target_x = self.x + dx * self.speed
            target_y = self.y + dy * self.speed
            next_col = int(target_x // TILE_SIZE)
            next_row = int(target_y // TILE_SIZE)
            if maze.is_walkable(next_col, next_row):
                self.x = target_x
                self.y = target_y
            else:
                self.x = center_x
                self.y = center_y

        self.col = int(self.x // TILE_SIZE)
        self.row = int(self.y // TILE_SIZE)

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
        self.current_dir = Direction.LEFT
        self.state = (
            GhostState.PATROL
            if self.ghost_type in (GhostType.PATROL, GhostType.GUARD)
            else GhostState.CHASE
        )
        self.color = self.base_color
        self.speed = GHOST_SPEED
        self.patrol_index = 0
        self.last_seen_player = None
