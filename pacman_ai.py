"""Plain Minimax decision-making for autonomous Pac-Man."""
from dataclasses import dataclass, replace
from math import ceil
from typing import Dict, FrozenSet, Sequence, Tuple, Union

from ghost import Ghost
from maze import Maze
from settings import (
    Direction,
    INITIAL_LIVES,
    MINIMAX_COLLECTIBLE_REWARD,
    MINIMAX_DEAD_END_PENALTY,
    MINIMAX_ESCAPE_OPTION_WEIGHT,
    MINIMAX_GHOST_COLLISION_PENALTY,
    MINIMAX_GHOST_DANGER_RANGE,
    MINIMAX_GHOST_RISK_WEIGHT,
    MINIMAX_LIFE_LOSS_WEIGHT,
    MINIMAX_LOOP_PENALTY,
    MINIMAX_PELLET_DISTANCE_WEIGHT,
    MINIMAX_POWER_PELLET_REWARD,
    MINIMAX_REMAINING_COLLECTIBLE_WEIGHT,
    MINIMAX_SEARCH_DEPTH,
    MINIMAX_WIN_REWARD,
    PACMAN_SPEED,
    TILE_SIZE,
)

Tile = Tuple[int, int]
Action = Tuple[int, int]
GhostSnapshot = Tuple[int, int, int, int]
GhostInput = Union[Ghost, Tile]

DIRECTIONS: Tuple[Action, ...] = (
    Direction.UP,
    Direction.RIGHT,
    Direction.DOWN,
    Direction.LEFT,
)
HISTORY_LENGTH = 8


@dataclass(frozen=True)
class SearchState:
    pacman: Tile
    ghosts: Tuple[GhostSnapshot, ...]
    dots: FrozenSet[Tile]
    power_pellets: FrozenSet[Tile]
    power_active: bool
    lives: int
    recent_tiles: Tuple[Tile, ...]


class MinimaxPlanner:
    """Search Pac-Man MAX moves and sequential ghost MIN moves without pruning."""

    def __init__(self, depth: int = MINIMAX_SEARCH_DEPTH):
        if depth < 1:
            raise ValueError("Minimax depth must be at least 1")
        self.depth = depth
        self.nodes_visited = 0
        self.last_scores: Dict[Action, float] = {}

    @staticmethod
    def _snapshot(ghosts: Sequence[GhostInput]) -> Tuple[GhostSnapshot, ...]:
        snapshots = []
        for ghost in ghosts:
            if isinstance(ghost, Ghost):
                snapshots.append(
                    (ghost.col, ghost.row, ghost.current_dir[0], ghost.current_dir[1])
                )
            else:
                snapshots.append((ghost[0], ghost[1], 0, 0))
        return tuple(snapshots)

    @staticmethod
    def _legal_actions(
        maze: Maze,
        tile: Tile,
        direction: Action = Direction.NONE,
        avoid_reverse: bool = False,
    ) -> Tuple[Action, ...]:
        legal = tuple(
            action
            for action in DIRECTIONS
            if maze.is_walkable(tile[0] + action[0], tile[1] + action[1])
            and not (
                avoid_reverse
                and action == Direction.OPPOSITES.get(direction)
            )
        )
        if legal or not avoid_reverse:
            return legal
        return tuple(
            action
            for action in DIRECTIONS
            if maze.is_walkable(tile[0] + action[0], tile[1] + action[1])
        )

    @staticmethod
    def _first_step_collision(
        maze: Maze,
        pacman: Tile,
        action: Action,
        ghosts: Sequence[GhostInput],
        destination_is_power: bool,
    ) -> bool:
        pacman_x = (pacman[0] + 0.5) * TILE_SIZE
        pacman_y = (pacman[1] + 0.5) * TILE_SIZE
        pacman_radius = int(TILE_SIZE * 0.45)
        pacman_frames = ceil(TILE_SIZE / PACMAN_SPEED)

        for ghost in ghosts:
            if not isinstance(ghost, Ghost):
                continue
            dx, dy = ghost.current_dir
            next_col, next_row = ghost.col + dx, ghost.row + dy
            if not maze.is_walkable(next_col, next_row):
                dx, dy = 0, 0
                next_col, next_row = ghost.col, ghost.row

            target_x = (next_col + 0.5) * TILE_SIZE
            target_y = (next_row + 0.5) * TILE_SIZE
            ghost_col, ghost_row = ghost.col, ghost.row
            ghost_x, ghost_y = ghost.x, ghost.y
            collision_distance = pacman_radius + ghost.radius

            for frame in range(1, pacman_frames + 1):
                pacman_travel = min(frame * PACMAN_SPEED, TILE_SIZE)
                distance_to_center = abs(target_x - ghost_x) + abs(target_y - ghost_y)
                ghost_travel = min(ghost.speed, distance_to_center)
                ghost_x += dx * ghost_travel
                ghost_y += dy * ghost_travel
                if ghost_travel >= distance_to_center:
                    ghost_x, ghost_y = target_x, target_y
                    ghost_col, ghost_row = next_col, next_row
                    next_col, next_row = ghost_col + dx, ghost_row + dy
                    if maze.is_walkable(next_col, next_row):
                        target_x = (next_col + 0.5) * TILE_SIZE
                        target_y = (next_row + 0.5) * TILE_SIZE
                    else:
                        dx, dy = 0, 0

                if destination_is_power and frame >= pacman_frames:
                    continue
                pacman_x_at_frame = pacman_x + action[0] * pacman_travel
                pacman_y_at_frame = pacman_y + action[1] * pacman_travel
                if (
                    abs(pacman_x_at_frame - ghost_x) < collision_distance
                    and abs(pacman_y_at_frame - ghost_y) < collision_distance
                ):
                    return True
        return False

    @staticmethod
    def _remember(state: SearchState, tile: Tile) -> Tuple[Tile, ...]:
        return (state.recent_tiles + (tile,))[-HISTORY_LENGTH:]

    def _move_pacman(self, state: SearchState, action: Action) -> SearchState:
        tile = (state.pacman[0] + action[0], state.pacman[1] + action[1])
        power_active = state.power_active or tile in state.power_pellets
        ghosts = state.ghosts
        if power_active:
            ghosts = tuple(
                (-1, -1, 0, 0) if ghost[:2] == tile else ghost
                for ghost in ghosts
            )
        return SearchState(
            pacman=tile,
            ghosts=ghosts,
            dots=state.dots - {tile},
            power_pellets=state.power_pellets - {tile},
            power_active=power_active,
            lives=state.lives,
            recent_tiles=self._remember(state, tile),
        )

    @staticmethod
    def _move_ghost(
        state: SearchState,
        ghost_index: int,
        action: Action,
    ) -> SearchState:
        ghosts = list(state.ghosts)
        col, row, _, _ = ghosts[ghost_index]
        next_tile = (col + action[0], row + action[1])
        if next_tile == state.pacman and state.power_active:
            ghosts[ghost_index] = (-1, -1, 0, 0)
        else:
            ghosts[ghost_index] = (
                next_tile[0],
                next_tile[1],
                action[0],
                action[1],
            )
        return replace(state, ghosts=tuple(ghosts))

    def evaluate_state(self, maze: Maze, state: SearchState) -> float:
        """Score survival first, then collectible progress and escape options."""
        self.nodes_visited += 1
        if not maze.is_walkable(*state.pacman):
            return self._death_score(state.lives)

        collectibles = state.dots | state.power_pellets
        if not collectibles:
            return MINIMAX_WIN_REWARD

        live_ghosts = tuple(
            (ghost[0], ghost[1])
            for ghost in state.ghosts
            if ghost[0] >= 0 and ghost[1] >= 0
        )
        if not state.power_active and state.pacman in live_ghosts:
            return self._death_score(state.lives)

        score = -MINIMAX_REMAINING_COLLECTIBLE_WEIGHT * len(collectibles)
        nearest_collectible = min(
            abs(state.pacman[0] - tile[0]) + abs(state.pacman[1] - tile[1])
            for tile in collectibles
        )
        score -= MINIMAX_PELLET_DISTANCE_WEIGHT * nearest_collectible

        legal = self._legal_actions(maze, state.pacman)
        if live_ghosts:
            nearest_ghost = min(
                abs(state.pacman[0] - ghost[0]) + abs(state.pacman[1] - ghost[1])
                for ghost in live_ghosts
            )
            if state.power_active:
                score += MINIMAX_GHOST_RISK_WEIGHT * min(
                    nearest_ghost, MINIMAX_GHOST_DANGER_RANGE
                )
            elif nearest_ghost <= MINIMAX_GHOST_DANGER_RANGE:
                danger = MINIMAX_GHOST_DANGER_RANGE - nearest_ghost + 1
                score -= MINIMAX_GHOST_RISK_WEIGHT * danger * danger
                score += MINIMAX_ESCAPE_OPTION_WEIGHT * len(legal)
            if len(legal) <= 1 and nearest_ghost <= MINIMAX_GHOST_DANGER_RANGE:
                score -= MINIMAX_DEAD_END_PENALTY

        score += MINIMAX_COLLECTIBLE_REWARD * (
            len(maze.dots | maze.power_pellets) - len(collectibles)
        )
        if state.power_pellets:
            nearest_power = min(
                abs(state.pacman[0] - tile[0]) + abs(state.pacman[1] - tile[1])
                for tile in state.power_pellets
            )
            if live_ghosts and not state.power_active:
                nearest_ghost = min(
                    abs(state.pacman[0] - ghost[0]) + abs(state.pacman[1] - ghost[1])
                    for ghost in live_ghosts
                )
                if nearest_ghost <= MINIMAX_GHOST_DANGER_RANGE:
                    score += MINIMAX_POWER_PELLET_REWARD / (nearest_power + 1)

        recent_visits = state.recent_tiles.count(state.pacman)
        if recent_visits:
            score -= MINIMAX_LOOP_PENALTY * recent_visits
        return score

    @staticmethod
    def _death_score(lives: int) -> float:
        return -MINIMAX_GHOST_COLLISION_PENALTY - (
            MINIMAX_LIFE_LOSS_WEIGHT * max(0, INITIAL_LIVES - lives)
        )

    def _minimax(
        self,
        maze: Maze,
        state: SearchState,
        remaining_depth: int,
        ghost_index: int,
    ) -> float:
        self.nodes_visited += 1
        if not state.dots and not state.power_pellets:
            return MINIMAX_WIN_REWARD
        if remaining_depth <= 0:
            return self.evaluate_state(maze, state)

        if ghost_index >= len(state.ghosts):
            actions = self._legal_actions(maze, state.pacman)
            if not actions:
                return self.evaluate_state(maze, state)
            best_score = float("-inf")
            for action in actions:
                next_state = self._move_pacman(state, action)
                if not next_state.power_active and any(
                    ghost[:2] == next_state.pacman
                    for ghost in next_state.ghosts
                    if ghost[0] >= 0
                ):
                    score = self._death_score(next_state.lives)
                else:
                    score = self._minimax(
                        maze, next_state, remaining_depth - 1, 0
                    )
                    if next_state.pacman in state.dots:
                        score += MINIMAX_COLLECTIBLE_REWARD
                    if next_state.pacman in state.power_pellets:
                        score += MINIMAX_POWER_PELLET_REWARD
                best_score = max(best_score, score)
            return best_score

        ghost = state.ghosts[ghost_index]
        if ghost[0] < 0 or ghost[1] < 0:
            return self._minimax(
                maze, state, remaining_depth, ghost_index + 1
            )
        actions = self._legal_actions(
            maze,
            (ghost[0], ghost[1]),
            (ghost[2], ghost[3]),
            avoid_reverse=not state.power_active,
        )
        if not actions:
            return self._minimax(
                maze, state, remaining_depth, ghost_index + 1
            )

        if state.power_active:
            best_score = float("-inf")
            for action in actions:
                next_state = self._move_ghost(state, ghost_index, action)
                score = self._minimax(
                    maze, next_state, remaining_depth - 1, ghost_index + 1
                )
                best_score = max(best_score, score)
            return best_score

        worst_score = float("inf")
        for action in actions:
            next_state = self._move_ghost(state, ghost_index, action)
            if next_state.ghosts[ghost_index][:2] == state.pacman:
                score = self._death_score(state.lives)
            else:
                score = self._minimax(
                    maze, next_state, remaining_depth - 1, ghost_index + 1
                )
            worst_score = min(worst_score, score)
        return worst_score

    @staticmethod
    def _tie_break(action: Action, current_direction: Action) -> Tuple[int, int]:
        return (
            int(action == current_direction),
            int(action != Direction.OPPOSITES.get(current_direction)),
        )

    def choose_action(
        self,
        maze: Maze,
        pacman_tile: Tile,
        ghosts: Sequence[GhostInput],
        current_direction: Action = Direction.NONE,
        power_active: bool = False,
        lives: int = 3,
        recent_tiles: Tuple[Tile, ...] = (),
    ) -> Tuple[Action, Dict[Action, float]]:
        self.nodes_visited = 0
        ghost_states = self._snapshot(ghosts)
        legal = self._legal_actions(maze, pacman_tile)
        if not legal:
            self.last_scores = {}
            return Direction.NONE, {}

        state = SearchState(
            pacman=pacman_tile,
            ghosts=ghost_states,
            dots=frozenset(maze.dots),
            power_pellets=frozenset(maze.power_pellets),
            power_active=power_active,
            lives=lives,
            recent_tiles=recent_tiles[-HISTORY_LENGTH:],
        )
        scores: Dict[Action, float] = {}
        for action in legal:
            next_state = self._move_pacman(state, action)
            if (
                not power_active
                and self._first_step_collision(
                    maze,
                    pacman_tile,
                    action,
                    ghosts,
                    destination_is_power=next_state.power_active,
                )
            ):
                score = self._death_score(lives)
            elif not next_state.power_active and any(
                ghost[:2] == next_state.pacman
                for ghost in next_state.ghosts
                if ghost[0] >= 0
            ):
                score = self._death_score(lives)
            else:
                score = self._minimax(
                    maze, next_state, self.depth - 1, 0
                )
                if next_state.pacman in state.dots:
                    score += MINIMAX_COLLECTIBLE_REWARD
                if next_state.pacman in state.power_pellets:
                    score += MINIMAX_POWER_PELLET_REWARD
            scores[action] = score

        self.last_scores = scores
        best_score = max(scores.values())
        best_actions = [
            action for action, score in scores.items() if score == best_score
        ]
        chosen = max(
            best_actions,
            key=lambda action: self._tie_break(action, current_direction),
        )
        return chosen, scores


class PacmanAI:
    """Run one Minimax decision at each Pac-Man tile."""

    def __init__(
        self,
        minimax_depth: int = MINIMAX_SEARCH_DEPTH,
        debug: bool = False,
    ):
        self.minimax = MinimaxPlanner(depth=minimax_depth)
        self.debug = debug
        self.last_decision_tile: Tile | None = None
        self.recent_tiles: Tuple[Tile, ...] = ()

    def reset_history(self) -> None:
        self.last_decision_tile = None
        self.recent_tiles = ()

    def choose_action(
        self,
        maze: Maze,
        tile: Tile,
        ghosts: Sequence[GhostInput],
        power_active: bool = False,
        current_direction: Action = Direction.NONE,
        lives: int = 3,
    ) -> Action:
        action, scores = self.minimax.choose_action(
            maze,
            tile,
            ghosts,
            current_direction=current_direction,
            power_active=power_active,
            lives=lives,
            recent_tiles=self.recent_tiles,
        )
        if action != Direction.NONE:
            next_tile = (tile[0] + action[0], tile[1] + action[1])
            self.recent_tiles = (self.recent_tiles + (tile, next_tile))[-HISTORY_LENGTH:]
        self.last_decision_tile = tile
        if self.debug:
            print(
                f"Minimax candidates={scores} "
                f"nodes={self.minimax.nodes_visited} chosen={action}"
            )
        return action
