"""Simulated Annealing decision-making for grid-based ghosts."""
import math
import random
from typing import Dict, Sequence, Tuple

from maze import Maze
from settings import (
    Direction,
    GHOST_MINIMAX_CLUSTER_PENALTY,
    GHOST_MINIMAX_DEAD_END_PENALTY,
    GHOST_MINIMAX_ESCAPE_OPTION_WEIGHT,
    GHOST_MINIMAX_SEPARATION_WEIGHT,
    GHOST_SPEED,
    TILE_SIZE,
)

Tile = Tuple[int, int]
Action = Tuple[int, int]

DIRECTIONS: Tuple[Action, ...] = (
    Direction.UP,
    Direction.DOWN,
    Direction.LEFT,
    Direction.RIGHT,
)

# Simulated Annealing Hyperparameters
DEFAULT_INITIAL_TEMP = 5.0
DEFAULT_MIN_TEMP = 0.1
DEFAULT_COOLING_RATE = 0.995


class GhostSimulatedAnnealingPlanner:
    """Stochastic ghost decision-making using Simulated Annealing (Boltzmann exploration)."""

    def __init__(
        self,
        initial_temp: float = DEFAULT_INITIAL_TEMP,
        min_temp: float = DEFAULT_MIN_TEMP,
        cooling_rate: float = DEFAULT_COOLING_RATE,
        random_seed: int | None = None,
    ):
        self.initial_temp = initial_temp
        self.min_temp = min_temp
        self.cooling_rate = cooling_rate
        self.temp = initial_temp
        self.steps = 0
        self.last_scores: Dict[Action, float] = {}
        self.last_probabilities: Dict[Action, float] = {}
        self._random = random.Random(random_seed)

    def reset(self) -> None:
        """Reset temperature to initial hot state for a new life or round."""
        self.temp = self.initial_temp
        self.steps = 0

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

    def _evaluate_candidate(
        self,
        maze: Maze,
        pacman: Tile,
        candidate_tile: Tile,
        other_ghosts: Tuple[Tile, ...],
        power_active: bool,
        player_lives: int,
    ) -> float:
        """Score candidate tile using the domain heuristic."""
        if candidate_tile == pacman:
            if power_active:
                return -1000.0
            return 2000.0 if player_lives <= 1 else 1000.0

        # Separation from other ghosts
        separation_score = 0.0
        for other_ghost in other_ghosts:
            dist = abs(candidate_tile[0] - other_ghost[0]) + abs(
                candidate_tile[1] - other_ghost[1]
            )
            separation_score += min(dist, 4) * GHOST_MINIMAX_SEPARATION_WEIGHT
            separation_score -= max(0, 2 - dist) * GHOST_MINIMAX_CLUSTER_PENALTY

        distance = abs(pacman[0] - candidate_tile[0]) + abs(
            pacman[1] - candidate_tile[1]
        )
        ghost_exits = len(self._legal_actions(maze, candidate_tile))
        pacman_exits = len(self._legal_actions(maze, pacman))

        if power_active:
            dead_end_penalty = (
                GHOST_MINIMAX_DEAD_END_PENALTY
                if ghost_exits <= 1 and distance > 0
                else 0.0
            )
            return (
                float(distance)
                + GHOST_MINIMAX_ESCAPE_OPTION_WEIGHT * ghost_exits
                - dead_end_penalty
                + separation_score
            )

        dead_end_penalty = 2.0 if ghost_exits <= 1 and distance > 0 else 0.0
        return (
            -float(distance)
            + 0.5 * (4 - pacman_exits)
            - dead_end_penalty
            + separation_score
        )

    def choose_action(
        self,
        maze: Maze,
        pacman: Tile,
        ghost: Tile,
        ghost_direction: Action,
        other_ghosts: Sequence[Tile] = (),
        power_active: bool = False,
        player_lives: int = 3,
        power_ticks_remaining: int = 0,
        ghost_speed: float = GHOST_SPEED,
        pacman_direction: Action = Direction.NONE,
    ) -> Action:
        """Select a move using Simulated Annealing Boltzmann probabilities."""
        actions = self._legal_actions(
            maze,
            ghost,
            ghost_direction,
            avoid_reverse=not power_active and power_ticks_remaining <= 0,
        )
        if not actions:
            self.last_scores = {}
            self.last_probabilities = {}
            return Direction.NONE

        static_other_ghosts = tuple(other_ghosts)
        scores: Dict[Action, float] = {}
        for action in actions:
            next_tile = (ghost[0] + action[0], ghost[1] + action[1])
            scores[action] = self._evaluate_candidate(
                maze,
                pacman,
                next_tile,
                static_other_ghosts,
                power_active=power_active or power_ticks_remaining > 0,
                player_lives=player_lives,
            )

        self.last_scores = scores
        max_score = max(scores.values())

        # Boltzmann / Softmax probability distribution:
        # P(a) = exp((Score(a) - max_score) / T) / sum(...)
        weights = []
        for action in actions:
            delta = scores[action] - max_score  # <= 0
            t = max(self.temp, 1e-4)
            scaled = delta / t
            w = math.exp(max(-50.0, scaled))
            weights.append(w)

        total_weight = sum(weights)
        if total_weight > 0:
            probs = [w / total_weight for w in weights]
        else:
            probs = [1.0 / len(actions)] * len(actions)

        self.last_probabilities = {
            action: prob for action, prob in zip(actions, probs)
        }

        # Cool down the temperature according to cooling schedule
        self.temp = max(self.min_temp, self.temp * self.cooling_rate)
        self.steps += 1

        # Sample action based on Boltzmann weights
        chosen = self._random.choices(actions, weights=probs, k=1)[0]
        return chosen
