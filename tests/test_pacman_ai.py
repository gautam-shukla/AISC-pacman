"""Tests for Pac-Man's risk-aware planner and Q-learning agent."""
import json

from game_state import GameState
from maze import Maze
from pacman import Pacman
from pacman_ai import MinimaxPlanner, PacmanAI, QLearningAgent, RiskAwareAStar
from settings import Direction, GhostType, TILE_SIZE
from ghost import Ghost


def test_risk_planner_returns_walkable_route_and_avoids_ghost_adjacent_actions():
    maze = Maze(
        [
            "#######",
            "#.....#",
            "#.#.#.#",
            "#.....#",
            "#######",
        ]
    )
    planner = RiskAwareAStar()

    route = planner.route_to_pellet(maze, (3, 1), [(4, 1)])

    assert route[0] == (3, 1)
    assert all(maze.is_walkable(*tile) for tile in route)
    safe_actions = planner.safe_actions(maze, (3, 1), [(4, 1)])
    assert Direction.RIGHT not in safe_actions
    assert safe_actions


def test_unreachable_pellets_are_not_selected():
    maze = Maze(
        [
            "#######",
            "#...###",
            "#######",
            "###...#",
            "#######",
        ]
    )
    maze.dots = {(2, 1), (4, 3)}

    route = RiskAwareAStar().route_to_pellet(maze, (1, 1), [])

    assert route[-1] == (2, 1)
    assert (4, 3) not in route


def test_q_learning_updates_and_persists_values(tmp_path):
    table = tmp_path / "q_table.json"
    agent = QLearningAgent(
        q_table_path=str(table),
        epsilon=0,
        learning_rate=0.5,
        discount_factor=0.9,
        seed=1,
    )
    state = (1, 0, 1, 0)
    action = Direction.RIGHT
    agent.update(state, action, 10.0, (0, 0, 1, 0), [], terminal=True)
    assert agent.q_values[state][action] == 5.0

    agent.save()
    saved = json.loads(table.read_text(encoding="utf-8"))
    assert saved["1,0,1,0"]["1,0"] == 5.0

    restored = QLearningAgent(q_table_path=str(table), epsilon=0, seed=1)
    assert restored.q_values[state][action] == 5.0


def test_autonomous_agent_only_selects_legal_actions(tmp_path):
    maze = Maze(["#####", "#...#", "#####"])
    agent = PacmanAI(q_table_path=str(tmp_path / "q.json"), seed=4)

    action = agent.choose_action(maze, (1, 1), [])

    assert action in (Direction.RIGHT,)
    assert agent.previous_state is not None
    assert agent.previous_action == action


def test_autonomous_agent_uses_ghost_positions_and_directions(tmp_path):
    maze = Maze(["#######", "#.....#", "#######"])
    agent = PacmanAI(q_table_path=str(tmp_path / "q.json"), seed=4)
    ghost = Ghost(4, 1, ghost_type=GhostType.HUNTER)

    action = agent.choose_action(maze, (1, 1), [ghost])

    assert action in (Direction.RIGHT,)


def test_ai_game_mode_moves_pacman_and_learns(tmp_path):
    maze = Maze(
        [
            "#########",
            "#P......#",
            "#.......#",
            "#########",
        ]
    )
    state = GameState(maze, ai_enabled=True, ai_q_table_path=str(tmp_path / "q.json"))
    state.ghosts.clear()
    starting_x = state.pacman.x

    for _ in range(45):
        state.update()

    assert state.ai_enabled
    assert state.pacman.x > starting_x
    assert state.ai_player.learner.q_values
    state.save_ai()
    assert (tmp_path / "q.json").exists()


def test_pacman_movement_stops_at_wall_and_reaches_exact_tile_centers():
    maze = Maze(["#####", "#...#", "#####"])
    pacman = Pacman(1, 1)
    pacman.set_next_direction(Direction.RIGHT)

    for _ in range(100):
        pacman.update(maze)
        assert maze.is_walkable(pacman.col, pacman.row)

    assert (pacman.col, pacman.row) == (3, 1)
    assert pacman.x == 3.5 * TILE_SIZE


def test_minimax_respects_legal_actions_and_prunes_branches():
    maze = Maze(
        [
            "#######",
            "#.....#",
            "#.....#",
            "#.....#",
            "#######",
        ]
    )
    pacman = Pacman(3, 2)
    ghost = Ghost(5, 2, ghost_type=GhostType.HUNTER)
    planner = MinimaxPlanner(depth=2, ghost_branch_limit=2)
    planner._distance_cache.clear()
    route = RiskAwareAStar().route_to_pellet(maze, (3, 2), [(ghost.col, ghost.row)])

    action, scores = planner.choose_action(
        maze,
        (3, 2),
        [ghost],
        pacman.current_dir,
        route,
    )

    assert action in (Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT)
    assert set(scores) == {
        Direction.UP,
        Direction.DOWN,
        Direction.LEFT,
        Direction.RIGHT,
    }
    assert planner.nodes_visited > 0
    assert planner.pruned_branches > 0


def test_minimax_avoids_immediate_ghost_collision_but_uses_power_pellet():
    maze = Maze(["#######", "#....o#", "#######"])
    ghost = Ghost(3, 1, ghost_type=GhostType.HUNTER)
    planner = MinimaxPlanner(depth=1)
    route = [(2, 1), (3, 1), (4, 1)]

    action, scores = planner.choose_action(
        maze,
        (2, 1),
        [ghost],
        Direction.NONE,
        route,
    )
    assert action == Direction.LEFT
    assert scores[Direction.RIGHT] == -1000

    power_maze = Maze(["#######", "#..o..#", "#######"])
    power_maze.dots.remove((2, 1))
    power_ghost = Ghost(3, 1, ghost_type=GhostType.HUNTER)
    power_route = RiskAwareAStar().route_to_pellet(
        power_maze, (2, 1), [(power_ghost.col, power_ghost.row)]
    )
    power_action, power_scores = planner.choose_action(
        power_maze,
        (2, 1),
        [power_ghost],
        Direction.NONE,
        power_route,
    )
    assert power_action == Direction.RIGHT
    assert power_scores[Direction.RIGHT] > -1000
