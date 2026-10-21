"""Risk-aware A*, Minimax search, and persistent tabular Q-learning."""
import json
import random
import warnings
from collections import deque
from heapq import heappop, heappush
from itertools import count
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from ghost import Ghost
from maze import Maze
from pathfinding import distances_from
from settings import (
    AI_DEAD_END_PENALTY,
    AI_DISCOUNT_FACTOR,
    AI_EPSILON,
    AI_GHOST_DANGER_RANGE,
    AI_LEARNING_RATE,
    AI_POWER_PELLET_BONUS,
    AI_Q_TABLE_PATH,
    AI_RISK_WEIGHT,
    AI_PELLET_CANDIDATE_LIMIT,
    Direction,
    MINIMAX_GHOST_BRANCH_LIMIT,
    MINIMAX_GHOST_COLLISION_PENALTY,
    MINIMAX_GHOST_RISK_WEIGHT,
    MINIMAX_PELLET_REWARD,
    MINIMAX_POWER_SURVIVAL_BONUS,
    MINIMAX_SCORE_TOLERANCE,
    MINIMAX_SEARCH_DEPTH,
    MINIMAX_ESCAPE_ROUTE_WEIGHT,
)

Tile = Tuple[int, int]
Action = Tuple[int, int]
State = Tuple[int, ...]
GhostInput = Union[Ghost, Tile]

DIRECTIONS: Tuple[Action, ...] = (
    Direction.UP,
    Direction.DOWN,
    Direction.LEFT,
    Direction.RIGHT,
)


class RiskAwareAStar:
    """Select reachable pellets by path length, ghost risk, and escape options."""

    def __init__(self, risk_weight: float = AI_RISK_WEIGHT):
        self.risk_weight = risk_weight
        self.last_ghost_signature: Tuple[Tile, ...] = ()
        self.last_route: List[Tile] = []
        self.last_cost = float("inf")

    def legal_actions(self, maze: Maze, tile: Tile) -> List[Action]:
        col, row = tile
        return [
            direction
            for direction in DIRECTIONS
            if maze.is_walkable(col + direction[0], row + direction[1])
        ]

    def _risk(
        self,
        tile: Tile,
        ghosts: Sequence[Tile],
        power_active: bool = False,
    ) -> float:
        risk = 0.0
        for ghost in ghosts:
            distance = abs(tile[0] - ghost[0]) + abs(tile[1] - ghost[1])
            if distance <= AI_GHOST_DANGER_RANGE:
                risk += self.risk_weight / (distance + 1)
        return risk * (0.15 if power_active else 1.0)

    @staticmethod
    def _dead_end_penalty(maze: Maze, tile: Tile, goal: Tile) -> float:
        if tile == goal:
            return 0.0
        col, row = tile
        exits = sum(
            maze.is_walkable(col + dx, row + dy)
            for dx, dy in DIRECTIONS
        )
        return AI_DEAD_END_PENALTY if exits <= 1 else 0.0

    def _path_to_goal(
        self,
        maze: Maze,
        start: Tile,
        goal: Tile,
        ghosts: Sequence[Tile],
        power_active: bool = False,
    ) -> Tuple[List[Tile], float]:
        if not maze.is_walkable(*start) or not maze.is_walkable(*goal):
            return [], float("inf")
        if start == goal:
            return [start], 0.0

        sequence = count()
        frontier = [(0.0, next(sequence), start)]
        costs = {start: 0.0}
        came_from: Dict[Tile, Tile] = {}
        while frontier:
            _, _, current = heappop(frontier)
            if current == goal:
                path = [goal]
                while path[-1] in came_from:
                    path.append(came_from[path[-1]])
                path.reverse()
                return path, costs[goal]

            col, row = current
            for dx, dy in DIRECTIONS:
                neighbor = (col + dx, row + dy)
                if not maze.is_walkable(*neighbor):
                    continue
                step_cost = (
                    1.0
                    + self._risk(neighbor, ghosts, power_active)
                    + self._dead_end_penalty(maze, neighbor, goal)
                )
                candidate_cost = costs[current] + step_cost
                if candidate_cost >= costs.get(neighbor, float("inf")):
                    continue
                costs[neighbor] = candidate_cost
                came_from[neighbor] = current
                heuristic = abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                heappush(
                    frontier,
                    (candidate_cost + heuristic, next(sequence), neighbor),
                )
        return [], float("inf")

    def route_to_pellet(
        self,
        maze: Maze,
        start: Tile,
        ghosts: Sequence[Tile],
        power_active: bool = False,
    ) -> List[Tile]:
        goals = set(maze.dots) | set(maze.power_pellets)
        if not goals:
            self.last_route = []
            self.last_cost = float("inf")
            return []

        best_path: List[Tile] = []
        best_cost = float("inf")
        reachable = {start}
        frontier = deque([start])
        while frontier:
            current = frontier.popleft()
            col, row = current
            for dx, dy in DIRECTIONS:
                neighbor = (col + dx, row + dy)
                if maze.is_walkable(*neighbor) and neighbor not in reachable:
                    reachable.add(neighbor)
                    frontier.append(neighbor)
        candidates = sorted(
            (goal for goal in goals if goal in reachable),
            key=lambda goal: (
                abs(start[0] - goal[0]) + abs(start[1] - goal[1]),
                goal[1],
                goal[0],
            ),
        )[:AI_PELLET_CANDIDATE_LIMIT]
        for goal in candidates:
            path, cost = self._path_to_goal(
                maze, start, goal, ghosts, power_active
            )
            if not path:
                continue
            if goal in maze.power_pellets and not power_active:
                cost -= AI_POWER_PELLET_BONUS
            if cost < best_cost:
                best_path, best_cost = path, cost

        self.last_ghost_signature = tuple(sorted(ghosts))
        self.last_route = best_path
        self.last_cost = best_cost
        return list(best_path)

    def safe_actions(
        self,
        maze: Maze,
        tile: Tile,
        ghosts: Sequence[Tile],
        power_active: bool = False,
    ) -> List[Action]:
        legal = self.legal_actions(maze, tile)
        if len(legal) <= 1 or not ghosts:
            return legal
        risk_by_action = {
            action: self._risk(
                (tile[0] + action[0], tile[1] + action[1]),
                ghosts,
                power_active,
            )
            for action in legal
        }
        minimum_risk = min(risk_by_action.values())
        safe = [
            action
            for action, risk in risk_by_action.items()
            if risk <= minimum_risk + self.risk_weight * 0.25
        ]
        return safe or legal

    def action_cost(
        self,
        maze: Maze,
        tile: Tile,
        action: Action,
        ghosts: Sequence[Tile],
        route: Sequence[Tile],
        power_active: bool = False,
    ) -> float:
        destination = (tile[0] + action[0], tile[1] + action[1])
        action_risk = self._risk(destination, ghosts)
        if len(route) > 1 and destination == route[1]:
            route_cost = 0.0
        else:
            route_cost = 0.25
        return action_risk + route_cost


GhostSnapshot = Tuple[int, int, int, int]


class MinimaxPlanner:
    """Bounded Pac-Man-max / all-ghosts-min turn search with alpha-beta pruning."""

    def __init__(
        self,
        depth: int = MINIMAX_SEARCH_DEPTH,
        ghost_branch_limit: int = MINIMAX_GHOST_BRANCH_LIMIT,
    ):
        self.depth = max(1, depth)
        self.ghost_branch_limit = max(1, ghost_branch_limit)
        self.nodes_visited = 0
        self.pruned_branches = 0
        self.last_scores: Dict[Action, float] = {}
        self._distance_cache: Dict[Tile, Dict[Tile, int]] = {}

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
    def _tile(snapshot: GhostSnapshot) -> Tile:
        return snapshot[0], snapshot[1]

    def _legal(
        self,
        maze: Maze,
        tile: Tile,
        direction: Action,
        avoid_reverse: bool = True,
    ) -> List[Action]:
        actions = []
        for action in DIRECTIONS:
            if not maze.is_walkable(tile[0] + action[0], tile[1] + action[1]):
                continue
            if avoid_reverse and action == Direction.OPPOSITES.get(direction):
                continue
            actions.append(action)
        if actions or not avoid_reverse:
            return actions
        return [
            action
            for action in DIRECTIONS
            if maze.is_walkable(tile[0] + action[0], tile[1] + action[1])
        ]

    def _distance(self, maze: Maze, source: Tile, goal: Tile) -> int:
        if goal not in self._distance_cache:
            self._distance_cache[goal] = distances_from(maze, goal)
        return self._distance_cache[goal].get(source, maze.cols * maze.rows)

    def _evaluate(
        self,
        maze: Maze,
        pacman: Tile,
        ghosts: Tuple[GhostSnapshot, ...],
        target: Tile,
        power_active: bool,
    ) -> float:
        self.nodes_visited += 1
        if not maze.is_walkable(*pacman):
            return -MINIMAX_GHOST_COLLISION_PENALTY
        live_ghost_tiles = [
            self._tile(ghost)
            for ghost in ghosts
            if ghost[0] >= 0 and ghost[1] >= 0
        ]
        distances = [
            abs(pacman[0] - ghost[0]) + abs(pacman[1] - ghost[1])
            for ghost in live_ghost_tiles
        ]
        if distances and min(distances) == 0 and not power_active:
            return -MINIMAX_GHOST_COLLISION_PENALTY

        target_distance = self._distance(maze, pacman, target)
        legal = self._legal(maze, pacman, Direction.NONE, avoid_reverse=False)
        exits = len(legal)
        score = -float(target_distance)
        score += MINIMAX_ESCAPE_ROUTE_WEIGHT * exits
        if exits <= 1 and distances:
            score -= MINIMAX_GHOST_RISK_WEIGHT / (min(distances) + 0.5)

        if distances:
            nearest = min(distances)
            if power_active:
                score += MINIMAX_POWER_SURVIVAL_BONUS / (nearest + 1)
            elif nearest <= AI_GHOST_DANGER_RANGE:
                score -= MINIMAX_GHOST_RISK_WEIGHT / (nearest + 0.5)
        return score

    def _ghost_actions(
        self,
        maze: Maze,
        snapshot: GhostSnapshot,
        pacman: Tile,
        power_active: bool,
    ) -> List[GhostSnapshot]:
        col, row, dx, dy = snapshot
        if col < 0 or row < 0:
            return [snapshot]
        actions = self._legal(maze, (col, row), (dx, dy))
        if not actions:
            return [snapshot]
        actions.sort(
            key=lambda action: abs(pacman[0] - (col + action[0]))
            + abs(pacman[1] - (row + action[1])),
            reverse=power_active,
        )
        if power_active:
            return [
                (col + actions[0][0], row + actions[0][1], actions[0][0], actions[0][1])
            ]
        return [
            (col + action[0], row + action[1], action[0], action[1])
            for action in actions[: self.ghost_branch_limit]
        ]

    def _ghost_turn(
        self,
        maze: Maze,
        pacman: Tile,
        ghosts: Tuple[GhostSnapshot, ...],
        target: Tile,
        power_active: bool,
        remaining_depth: int,
        pacman_direction: Action,
        alpha: float,
        beta: float,
        ghost_index: int = 0,
    ) -> float:
        if ghost_index >= len(ghosts):
            if remaining_depth <= 0:
                return self._evaluate(
                    maze, pacman, ghosts, target, power_active
                )
            return self._max_turn(
                maze,
                pacman,
                ghosts,
                target,
                power_active,
                remaining_depth,
                pacman_direction,
                alpha,
                beta,
            )

        self.nodes_visited += 1
        worst_score = float("inf")
        current_ghost = ghosts[ghost_index]
        for moved_ghost in self._ghost_actions(
            maze, current_ghost, pacman, power_active
        ):
            next_ghosts = list(ghosts)
            next_ghosts[ghost_index] = moved_ghost
            updated_ghosts = tuple(next_ghosts)
            collision = moved_ghost[:2] == pacman
            if collision and not power_active:
                score = -MINIMAX_GHOST_COLLISION_PENALTY
            elif collision and power_active:
                updated_ghosts = tuple(
                    (-1, -1, 0, 0) if index == ghost_index else ghost
                    for index, ghost in enumerate(updated_ghosts)
                )
                score = self._ghost_turn(
                    maze, pacman, updated_ghosts, target, power_active,
                    remaining_depth, pacman_direction, alpha, beta,
                    ghost_index + 1,
                )
            else:
                score = self._ghost_turn(
                    maze, pacman, updated_ghosts, target, power_active,
                    remaining_depth, pacman_direction, alpha, beta,
                    ghost_index + 1,
                )
            worst_score = min(worst_score, score)
            beta = min(beta, worst_score)
            if beta <= alpha:
                self.pruned_branches += 1
                break
        return worst_score

    def _max_turn(
        self,
        maze: Maze,
        pacman: Tile,
        ghosts: Tuple[GhostSnapshot, ...],
        target: Tile,
        power_active: bool,
        remaining_depth: int,
        pacman_direction: Action,
        alpha: float,
        beta: float,
    ) -> float:
        self.nodes_visited += 1
        actions = self._legal(maze, pacman, pacman_direction)
        if not actions:
            return self._evaluate(maze, pacman, ghosts, target, power_active)
        best_score = float("-inf")
        for action in actions:
            next_pacman = (pacman[0] + action[0], pacman[1] + action[1])
            collected_power = next_pacman in maze.power_pellets
            collected_target = next_pacman == target
            next_power = power_active or collected_power
            if any(
                ghost[:2] == next_pacman and ghost[0] >= 0
                for ghost in ghosts
            ) and not next_power:
                score = -MINIMAX_GHOST_COLLISION_PENALTY
            else:
                score = self._ghost_turn(
                    maze,
                    next_pacman,
                    ghosts,
                    target,
                    next_power,
                    remaining_depth - 1,
                    action,
                    alpha,
                    beta,
                )
                if collected_target:
                    score += MINIMAX_PELLET_REWARD
                    if collected_power:
                        score += MINIMAX_POWER_SURVIVAL_BONUS
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                self.pruned_branches += 1
                break
        return best_score

    def choose_action(
        self,
        maze: Maze,
        pacman_tile: Tile,
        ghosts: Sequence[GhostInput],
        current_direction: Action,
        route: Sequence[Tile],
        power_active: bool = False,
        allowed_actions: Optional[Sequence[Action]] = None,
    ) -> Tuple[Action, Dict[Action, float]]:
        self.nodes_visited = 0
        self.pruned_branches = 0
        self._distance_cache.clear()
        ghost_states = self._snapshot(ghosts)
        legal = self._legal(maze, pacman_tile, current_direction)
        if allowed_actions is not None:
            legal = [action for action in legal if action in allowed_actions]
        if not legal:
            self.last_scores = {}
            return Direction.NONE, {}
        target = route[-1] if route else pacman_tile
        scores: Dict[Action, float] = {}
        alpha = float("-inf")
        for action in legal:
            next_tile = (pacman_tile[0] + action[0], pacman_tile[1] + action[1])
            next_power = power_active or next_tile in maze.power_pellets
            if any(
                ghost[:2] == next_tile and ghost[0] >= 0
                for ghost in ghost_states
            ) and not next_power:
                score = -MINIMAX_GHOST_COLLISION_PENALTY
            else:
                score = self._ghost_turn(
                    maze,
                    next_tile,
                    ghost_states,
                    target,
                    next_power,
                    self.depth - 1,
                    action,
                    alpha,
                    float("inf"),
                )
                if next_tile == target:
                    score += MINIMAX_PELLET_REWARD
                    if next_tile in maze.power_pellets:
                        score += MINIMAX_POWER_SURVIVAL_BONUS
            scores[action] = score
            alpha = max(alpha, score)
        self.last_scores = scores
        best_score = max(scores.values())
        best_actions = [
            action
            for action, score in scores.items()
            if score >= best_score - MINIMAX_SCORE_TOLERANCE
        ]
        route_action = (
            (route[1][0] - pacman_tile[0], route[1][1] - pacman_tile[1])
            if len(route) > 1
            else None
        )
        if route_action in best_actions:
            chosen = route_action
        else:
            chosen = best_actions[0]
        return chosen, scores


class QLearningAgent:
    """Epsilon-greedy tabular learner with a compact, persisted state table."""

    def __init__(
        self,
        q_table_path: Optional[str] = None,
        epsilon: float = AI_EPSILON,
        learning_rate: float = AI_LEARNING_RATE,
        discount_factor: float = AI_DISCOUNT_FACTOR,
        seed: Optional[int] = None,
    ):
        self.path = Path(q_table_path or AI_Q_TABLE_PATH).expanduser()
        self.epsilon = epsilon
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.random = random.Random(seed)
        self.q_values: Dict[State, Dict[Action, float]] = {}
        self._load()

    @staticmethod
    def _state_key(state: State) -> str:
        return ",".join(str(value) for value in state)

    @staticmethod
    def _action_key(action: Action) -> str:
        return f"{action[0]},{action[1]}"

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError, json.JSONDecodeError) as error:
            warnings.warn(f"Could not load Pac-Man Q-table {self.path}: {error}")
            return

        if not isinstance(data, dict):
            warnings.warn(f"Ignoring invalid Pac-Man Q-table format: {self.path}")
            return
        for state_key, action_values in data.items():
            try:
                state = tuple(int(part) for part in state_key.split(","))
                if not isinstance(action_values, dict):
                    continue
                values = {
                    tuple(int(part) for part in action_key.split(",")): float(value)
                    for action_key, value in action_values.items()
                }
                self.q_values[state] = values
            except (TypeError, ValueError):
                warnings.warn(f"Ignoring invalid Q-table entry for state {state_key!r}")

    def save(self) -> None:
        data = {
            self._state_key(state): {
                self._action_key(action): value
                for action, value in action_values.items()
            }
            for state, action_values in self.q_values.items()
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(data), encoding="utf-8")
        except OSError as error:
            warnings.warn(f"Could not save Pac-Man Q-table {self.path}: {error}")

    def choose_action(
        self,
        state: State,
        safe_actions: Sequence[Action],
        route_actions: Sequence[Action],
    ) -> Action:
        if not safe_actions:
            return Direction.NONE
        if self.random.random() < self.epsilon:
            return self.random.choice(list(safe_actions))

        values = self.q_values.get(state, {})
        return max(
            safe_actions,
            key=lambda action: values.get(action, 0.0)
            + (0.1 if action in route_actions else 0.0),
        )

    def update(
        self,
        state: State,
        action: Action,
        reward: float,
        next_state: State,
        next_actions: Sequence[Action],
        terminal: bool = False,
    ) -> None:
        current_values = self.q_values.setdefault(state, {})
        old_value = current_values.get(action, 0.0)
        future_value = 0.0
        if not terminal and next_actions:
            future_values = self.q_values.get(next_state, {})
            future_value = max(future_values.get(next_action, 0.0) for next_action in next_actions)
        target = reward + self.discount_factor * future_value
        current_values[action] = old_value + self.learning_rate * (target - old_value)


class PacmanAI:
    """Combines A* target selection, minimax safety, and Q-learning tie breaks."""

    def __init__(
        self,
        q_table_path: Optional[str] = None,
        seed: Optional[int] = None,
        minimax_depth: int = MINIMAX_SEARCH_DEPTH,
        debug: bool = False,
    ):
        self.planner = RiskAwareAStar()
        self.minimax = MinimaxPlanner(depth=minimax_depth)
        self.learner = QLearningAgent(q_table_path=q_table_path, seed=seed)
        self.debug = debug
        self.previous_state: Optional[State] = None
        self.previous_action: Optional[Action] = None
        self.last_decision_tile: Optional[Tile] = None
        self.pending_reward = 0.0

    def state_for(
        self,
        maze: Maze,
        tile: Tile,
        ghosts: Sequence[Tile],
    ) -> State:
        legal = self.planner.legal_actions(maze, tile)
        nearest_ghost = min(
            (
                abs(tile[0] - ghost[0]) + abs(tile[1] - ghost[1])
                for ghost in ghosts
            ),
            default=AI_GHOST_DANGER_RANGE + 1,
        )
        danger = int(nearest_ghost <= 2), int(nearest_ghost <= AI_GHOST_DANGER_RANGE)
        pellet_distances = [
            abs(tile[0] - pellet[0]) + abs(tile[1] - pellet[1])
            for pellet in maze.dots | maze.power_pellets
        ]
        nearest_pellet = min(pellet_distances, default=20)
        pellet_bucket = min(nearest_pellet // 3, 4)
        power_available = int(bool(maze.power_pellets))
        escape_options = min(len(legal), 3)
        return (
            danger[0],
            danger[1],
            int(Direction.UP in legal),
            int(Direction.DOWN in legal),
            int(Direction.LEFT in legal),
            int(Direction.RIGHT in legal),
            pellet_bucket,
            power_available,
            escape_options,
        )

    def choose_action(
        self,
        maze: Maze,
        tile: Tile,
        ghosts: Sequence[GhostInput],
        power_active: bool = False,
        current_direction: Action = Direction.NONE,
    ) -> Action:
        legal = self.planner.legal_actions(maze, tile)
        if not legal:
            self.previous_state = None
            self.previous_action = None
            return Direction.NONE

        ghost_tiles = [
            (ghost.col, ghost.row) if isinstance(ghost, Ghost) else ghost
            for ghost in ghosts
        ]
        route = self.planner.route_to_pellet(
            maze, tile, ghost_tiles, power_active=power_active
        )
        safe = self.planner.safe_actions(
            maze, tile, ghost_tiles, power_active=power_active
        )
        route_action = (
            (route[1][0] - tile[0], route[1][1] - tile[1])
            if len(route) > 1
            else None
        )
        route_actions = [route_action] if route_action in safe else []
        state = self.state_for(maze, tile, ghost_tiles)
        if self.previous_state is not None and self.previous_action is not None:
            self.learner.update(
                self.previous_state,
                self.previous_action,
                self.pending_reward,
                state,
                safe,
            )
            self.pending_reward = 0.0
        minimax_action, scores = self.minimax.choose_action(
            maze,
            tile,
            ghosts,
            current_direction,
            route,
            power_active=power_active,
            allowed_actions=safe,
        )
        if scores:
            best_score = max(scores.values())
            finalists = [
                action
                for action, score in scores.items()
                if score >= best_score - MINIMAX_SCORE_TOLERANCE
            ]
            action = self.learner.choose_action(state, finalists, route_actions)
            if action not in finalists:
                action = minimax_action
        else:
            action = minimax_action
        if self.debug:
            target = route[-1] if route else None
            print(
                f"AI target={target} candidates={scores} "
                f"nodes={self.minimax.nodes_visited} "
                f"pruned={self.minimax.pruned_branches} "
                f"chosen={action}"
            )
        self.previous_state = state
        self.previous_action = action
        return action

    def learn(
        self,
        reward: float,
        maze: Maze,
        tile: Tile,
        ghosts: Sequence[Tile],
        terminal: bool = False,
    ) -> None:
        self.pending_reward += reward
        if self.previous_state is None or self.previous_action is None or not terminal:
            return
        next_state = self.state_for(maze, tile, ghosts)
        next_actions = self.planner.safe_actions(maze, tile, ghosts)
        self.learner.update(
            self.previous_state,
            self.previous_action,
            self.pending_reward,
            next_state,
            next_actions,
            terminal=True,
        )
        self.previous_state = None
        self.previous_action = None
        self.pending_reward = 0.0

    def save(self) -> None:
        self.learner.save()
