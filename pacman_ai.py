"""Minimax decision-making with Alpha-Beta Pruning for autonomous Pac-Man."""
from dataclasses import dataclass, replace
from math import ceil
import random
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
    MINIMAX_GHOST_RISK_WEIGHT,
    MINIMAX_LIFE_LOSS_WEIGHT,
    MINIMAX_LOOP_PENALTY,
    MINIMAX_PELLET_DISTANCE_WEIGHT,
    MINIMAX_POWER_PELLET_REWARD,
    MINIMAX_REMAINING_COLLECTIBLE_WEIGHT,
    MINIMAX_SEARCH_DEPTH,
    MINIMAX_TIE_TOLERANCE,
    MINIMAX_WIN_REWARD,
    PACMAN_SPEED,
    POWER_PELLET_DURATION,
    TILE_SIZE,
    GHOST_SPEED,
)

Tile = Tuple[int, int]
Action = Tuple[int, int]
GhostSnapshot = Tuple[int, int, int, int, int, int, float]
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
    power_ticks_remaining: int = 0
    pacman_direction: Action = Direction.NONE


class MinimaxPlanner:
    """Search Pac-Man MAX moves and sequential ghost MIN moves with Alpha-Beta Pruning."""

    def __init__(
        self,
        depth: int = MINIMAX_SEARCH_DEPTH,
        random_seed: int | None = None,
    ):
        if depth < 1:
            raise ValueError("Minimax depth must be at least 1")
        self.depth = depth
        self.nodes_visited = 0
        self.pruned_branches = 0
        self.last_scores: Dict[Action, float] = {}
        self._random = random.Random(random_seed)

    def reseed(self, random_seed: int | None) -> None:
        self._random.seed(random_seed)

    @staticmethod
    def _snapshot(ghosts: Sequence[GhostInput]) -> Tuple[GhostSnapshot, ...]:
        snapshots = []
        for ghost in ghosts:
            if isinstance(ghost, Ghost):
                snapshots.append(
                    (
                        ghost.col,
                        ghost.row,
                        ghost.current_dir[0],
                        ghost.current_dir[1],
                        ghost.spawn_col,
                        ghost.spawn_row,
                        ghost.speed,
                    )
                )
            else:
                snapshots.append(
                    (
                        ghost[0],
                        ghost[1],
                        0,
                        0,
                        ghost[0],
                        ghost[1],
                        GHOST_SPEED,
                    )
                )
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
        power_ticks_remaining: int,
    ) -> bool:
        pacman_x = (pacman[0] + 0.5) * TILE_SIZE
        pacman_y = (pacman[1] + 0.5) * TILE_SIZE
        pacman_radius = int(TILE_SIZE * 0.45)
        pacman_frames = ceil(TILE_SIZE / PACMAN_SPEED)

        for ghost in ghosts:
            if not isinstance(ghost, Ghost):
                continue
            dx, dy = ghost.current_dir
            if dx == 0 and dy == 0:
                p_dx = 1 if pacman[0] > ghost.col else -1 if pacman[0] < ghost.col else 0
                p_dy = 1 if pacman[1] > ghost.row else -1 if pacman[1] < ghost.row else 0
                if p_dx != 0 and maze.is_walkable(ghost.col + p_dx, ghost.row):
                    dx, dy = p_dx, 0
                elif p_dy != 0 and maze.is_walkable(ghost.col, ghost.row + p_dy):
                    dx, dy = 0, p_dy
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

                powered = frame < power_ticks_remaining or (
                    destination_is_power and frame >= pacman_frames
                )
                if powered:
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
        if tile in state.power_pellets:
            power_ticks_remaining = POWER_PELLET_DURATION
        else:
            power_ticks_remaining = max(
                0,
                state.power_ticks_remaining - ceil(TILE_SIZE / PACMAN_SPEED),
            )
        power_active = power_ticks_remaining > 0
        ghosts = state.ghosts
        if power_active:
            ghosts = tuple(
                (
                    ghost[4],
                    ghost[5],
                    0,
                    0,
                    ghost[4],
                    ghost[5],
                    ghost[6],
                )
                if ghost[:2] == tile
                else ghost
                for ghost in ghosts
            )
        return SearchState(
            pacman=tile,
            pacman_direction=action,
            ghosts=ghosts,
            dots=state.dots - {tile},
            power_pellets=state.power_pellets - {tile},
            power_active=power_active,
            lives=state.lives,
            recent_tiles=self._remember(state, tile),
            power_ticks_remaining=power_ticks_remaining,
        )

    @staticmethod
    def _move_ghost(
        state: SearchState,
        ghost_index: int,
        action: Action,
    ) -> SearchState:
        ghosts = list(state.ghosts)
        col, row, _, _, spawn_col, spawn_row, ghost_speed = ghosts[ghost_index]
        next_tile = (col + action[0], row + action[1])
        power_ticks_remaining = max(
            0,
            state.power_ticks_remaining - ceil(TILE_SIZE / ghost_speed),
        )
        if next_tile == state.pacman and power_ticks_remaining > 0:
            ghosts[ghost_index] = (
                spawn_col,
                spawn_row,
                0,
                0,
                spawn_col,
                spawn_row,
                ghost_speed,
            )
        else:
            ghosts[ghost_index] = (
                next_tile[0],
                next_tile[1],
                action[0],
                action[1],
                spawn_col,
                spawn_row,
                ghost_speed,
            )
        return replace(
            state,
            ghosts=tuple(ghosts),
            power_active=power_ticks_remaining > 0,
            power_ticks_remaining=power_ticks_remaining,
        )

    def evaluate_state(self, maze: Maze, state: SearchState) -> float:
        """Score survival first, then collectible progress and escape options."""
        self.nodes_visited += 1
        if not maze.is_walkable(*state.pacman):
            return self._death_score(state.lives)

        collectibles = state.dots | state.power_pellets
        if not collectibles:
            return MINIMAX_WIN_REWARD

        live_ghosts = tuple(
            (ghost[0], ghost[1], ghost[2], ghost[3])
            for ghost in state.ghosts
        )
        if not state.power_active and any(
            state.pacman == ghost[:2] for ghost in live_ghosts
        ):
            return self._death_score(state.lives)

        score = -MINIMAX_REMAINING_COLLECTIBLE_WEIGHT * len(collectibles)
        nearest_collectible = min(
            abs(state.pacman[0] - tile[0]) + abs(state.pacman[1] - tile[1])
            for tile in collectibles
        )
        score -= MINIMAX_PELLET_DISTANCE_WEIGHT * nearest_collectible

        legal = self._legal_actions(
            maze,
            state.pacman,
            direction=state.pacman_direction,
        )
        if live_ghosts:
            danger = 0.0
            for col, row, dx, dy in live_ghosts:
                distance = abs(state.pacman[0] - col) + abs(state.pacman[1] - row)
                moving_toward_pacman = (
                    dx * (state.pacman[0] - col)
                    + dy * (state.pacman[1] - row)
                ) > 0
                predicted_distance = max(0, distance - int(moving_toward_pacman))
                danger += 1.0 / (predicted_distance + 1) ** 2
            if state.power_active:
                score += MINIMAX_GHOST_RISK_WEIGHT * danger
            else:
                score -= MINIMAX_GHOST_RISK_WEIGHT * danger
                score += MINIMAX_ESCAPE_OPTION_WEIGHT * len(legal) * danger
            if len(legal) <= 1:
                score -= MINIMAX_DEAD_END_PENALTY * danger

        score += MINIMAX_COLLECTIBLE_REWARD * (
            len(maze.dots | maze.power_pellets) - len(collectibles)
        )
        if state.power_pellets:
            nearest_power = min(
                abs(state.pacman[0] - tile[0]) + abs(state.pacman[1] - tile[1])
                for tile in state.power_pellets
            )
            if live_ghosts and not state.power_active and danger >= 0.04:
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
        alpha: float = float("-inf"),
        beta: float = float("inf"),
    ) -> float:
        self.nodes_visited += 1
        if not state.dots and not state.power_pellets:
            return MINIMAX_WIN_REWARD
        if remaining_depth <= 0:
            return self.evaluate_state(maze, state)

        if ghost_index >= len(state.ghosts):
            actions = self._legal_actions(
                maze,
                state.pacman,
                direction=state.pacman_direction,
            )
            if not actions:
                return self.evaluate_state(maze, state)
            best_score = float("-inf")
            for action in actions:
                next_state = self._move_pacman(state, action)
                if next_state.power_ticks_remaining <= 0 and any(
                    ghost[:2] == next_state.pacman
                    for ghost in next_state.ghosts
                ):
                    score = self._death_score(next_state.lives)
                else:
                    score = self._minimax(
                        maze, next_state, remaining_depth - 1, 0, alpha, beta
                    )
                    if next_state.pacman in state.dots:
                        score += MINIMAX_COLLECTIBLE_REWARD
                    if next_state.pacman in state.power_pellets:
                        score += MINIMAX_POWER_PELLET_REWARD
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    self.pruned_branches += 1
                    break
            return best_score

        ghost = state.ghosts[ghost_index]
        actions = self._legal_actions(
            maze,
            (ghost[0], ghost[1]),
            (ghost[2], ghost[3]),
            avoid_reverse=state.power_ticks_remaining <= 0,
        )
        if not actions:
            return self._minimax(
                maze, state, remaining_depth, ghost_index + 1, alpha, beta
            )

        if state.power_ticks_remaining > 0:
            best_score = float("-inf")
            for action in actions:
                next_state = self._move_ghost(state, ghost_index, action)
                if (
                    next_state.power_ticks_remaining <= 0
                    and (ghost[0] + action[0], ghost[1] + action[1])
                    == state.pacman
                ):
                    score = self._death_score(state.lives)
                else:
                    score = self._minimax(
                        maze, next_state, remaining_depth - 1, ghost_index + 1, alpha, beta
                    )
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    self.pruned_branches += 1
                    break
            return best_score

        worst_score = float("inf")
        for action in actions:
            next_state = self._move_ghost(state, ghost_index, action)
            if next_state.ghosts[ghost_index][:2] == state.pacman:
                score = self._death_score(state.lives)
            else:
                score = self._minimax(
                    maze, next_state, remaining_depth - 1, ghost_index + 1, alpha, beta
                )
            worst_score = min(worst_score, score)
            beta = min(beta, worst_score)
            if beta <= alpha:
                self.pruned_branches += 1
                break
        return worst_score

    def choose_action(
        self,
        maze: Maze,
        pacman_tile: Tile,
        ghosts: Sequence[GhostInput],
        current_direction: Action = Direction.NONE,
        power_active: bool = False,
        lives: int = 3,
        recent_tiles: Tuple[Tile, ...] = (),
        power_ticks_remaining: int = 0,
    ) -> Tuple[Action, Dict[Action, float]]:
        self.nodes_visited = 0
        self.pruned_branches = 0
        ghost_states = self._snapshot(ghosts)
        legal = self._legal_actions(
            maze,
            pacman_tile,
            direction=current_direction,
        )
        if not legal:
            self.last_scores = {}
            return Direction.NONE, {}

        state = SearchState(
            pacman=pacman_tile,
            pacman_direction=current_direction,
            ghosts=ghost_states,
            dots=frozenset(maze.dots),
            power_pellets=frozenset(maze.power_pellets),
            power_active=power_ticks_remaining > 0 or power_active,
            power_ticks_remaining=(
                power_ticks_remaining
                if power_ticks_remaining > 0
                else POWER_PELLET_DURATION if power_active else 0
            ),
            lives=lives,
            recent_tiles=recent_tiles[-HISTORY_LENGTH:],
        )
        scores: Dict[Action, float] = {}
        alpha = float("-inf")
        beta = float("inf")

        for action in legal:
            next_state = self._move_pacman(state, action)
            if self._first_step_collision(
                maze,
                pacman_tile,
                action,
                ghosts,
                destination_is_power=(
                    pacman_tile[0] + action[0],
                    pacman_tile[1] + action[1],
                )
                in state.power_pellets,
                power_ticks_remaining=state.power_ticks_remaining,
            ):
                score = self._death_score(lives)
            elif next_state.power_ticks_remaining <= 0 and any(
                ghost[:2] == next_state.pacman
                for ghost in next_state.ghosts
            ):
                score = self._death_score(lives)
            else:
                score = self._minimax(
                    maze, next_state, self.depth - 1, 0, alpha, beta
                )
                if next_state.pacman in state.dots:
                    score += MINIMAX_COLLECTIBLE_REWARD
                if next_state.pacman in state.power_pellets:
                    score += MINIMAX_POWER_PELLET_REWARD
            scores[action] = score
            if MINIMAX_TIE_TOLERANCE > 0:
                alpha = max(alpha, score - MINIMAX_TIE_TOLERANCE)
            else:
                alpha = max(alpha, score)

        self.last_scores = scores
        best_score = max(scores.values())
        best_actions = [
            action
            for action, score in scores.items()
            if best_score - score <= MINIMAX_TIE_TOLERANCE
        ]
        best_actions.sort(
            key=lambda action: (
                action != current_direction,
                action == Direction.OPPOSITES.get(current_direction),
            )
        )
        chosen = self._random.choice(best_actions)
        return chosen, scores


class PacmanAI:
    """Run one Minimax Alpha-Beta decision at each Pac-Man tile."""

    def __init__(
        self,
        minimax_depth: int = MINIMAX_SEARCH_DEPTH,
        debug: bool = False,
        random_seed: int | None = None,
    ):
        self.minimax = MinimaxPlanner(
            depth=minimax_depth,
            random_seed=random_seed,
        )
        self.debug = debug
        self.last_decision_tile: Tile | None = None
        self.recent_tiles: Tuple[Tile, ...] = ()

    def reseed(self, random_seed: int | None) -> None:
        self.minimax.reseed(random_seed)

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
        power_ticks_remaining: int = 0,
    ) -> Action:
        action, scores = self.minimax.choose_action(
            maze,
            tile,
            ghosts,
            current_direction=current_direction,
            power_active=power_active,
            lives=lives,
            recent_tiles=self.recent_tiles,
            power_ticks_remaining=power_ticks_remaining,
        )
        if action != Direction.NONE:
            next_tile = (tile[0] + action[0], tile[1] + action[1])
            self.recent_tiles = (self.recent_tiles + (tile, next_tile))[-HISTORY_LENGTH:]
        self.last_decision_tile = tile
        if self.debug:
            print(
                f"Minimax Alpha-Beta candidates={scores} "
                f"nodes={self.minimax.nodes_visited} "
                f"pruned={self.minimax.pruned_branches} chosen={action}"
            )
        return action
