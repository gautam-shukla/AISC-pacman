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
    GHOST_PROXIMITY_RANGE_TILES,
    GHOST_PROXIMITY_SPEED_BONUS,
    GHOST_LOW_LIVES_SPEED_REDUCTION,
    GHOST_MAX_LIVES_SPEED_REDUCTION,
    GHOST_GUARD_CHASE_RANGE,
    GHOST_SEARCH_RANGE,
    INITIAL_LIVES,
    TILE_SIZE,
    Direction,
    DIFFICULTY_MIN,
    DIFFICULTY_MAX,
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

    def _target_for_player(
        self, maze: Maze, pacman: Pacman, difficulty_multiplier: float
    ) -> Tile:
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
            if distance <= GHOST_GUARD_CHASE_RANGE * difficulty_multiplier:
                self.state = GhostState.CHASE
                return player_tile
            self.state = GhostState.PATROL
            return patrol_target

        if distance <= GHOST_SEARCH_RANGE * difficulty_multiplier:
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
        difficulty_multiplier: float = 1.0,
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
                target = self._target_for_player(
                    maze, pacman, difficulty_multiplier
                )
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
                self._choose_direction(maze, pacman, frightened, target)

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
        self.current_dir = Direction.LEFT
        self.state = (
            GhostState.PATROL
            if self.ghost_type in (GhostType.PATROL, GhostType.GUARD)
            else GhostState.CHASE
        )
        self.color = self.base_color
        self.speed = GHOST_SPEED
        self.patrol_index = 0
        self.patrol_targets = []
        self.last_seen_player = None
