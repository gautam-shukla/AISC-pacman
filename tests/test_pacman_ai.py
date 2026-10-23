"""Tests for autonomous Pac-Man's plain Minimax planner."""

from game_state import GameState
from ghost import Ghost
from maze import Maze
from pacman import Pacman
from pacman_ai import MinimaxPlanner, PacmanAI, SearchState
from settings import Direction, MINIMAX_GHOST_COLLISION_PENALTY, TILE_SIZE


def test_minimax_uses_configurable_depth_without_pruning():
    planner = MinimaxPlanner(depth=5)

    assert planner.depth == 5
    assert not hasattr(planner, "pruned_branches")


def test_minimax_prioritizes_survival_more_when_fewer_lives_remain():
    planner = MinimaxPlanner(depth=1)

    assert planner._death_score(1) < planner._death_score(3)


def test_minimax_selects_only_legal_moves_and_handles_no_moves():
    maze = Maze(
        [
            "#####",
            "#...#",
            "#####",
        ]
    )
    planner = MinimaxPlanner(depth=2)
    action, scores = planner.choose_action(maze, (2, 1), [])

    assert action in (Direction.LEFT, Direction.RIGHT)
    assert set(scores) == {Direction.LEFT, Direction.RIGHT}

    trapped_maze = Maze(["###", "#P#", "###"])
    trapped_action, trapped_scores = planner.choose_action(
        trapped_maze,
        trapped_maze.pacman_spawn,
        [],
    )
    assert trapped_action == Direction.NONE
    assert trapped_scores == {}


def test_minimax_chooses_escape_from_a_closing_ghost():
    maze = Maze(
        [
            "#########",
            "#.......#",
            "#..PG...#",
            "#.......#",
            "#########",
        ]
    )
    agent = PacmanAI(minimax_depth=4)
    ghost = Ghost(*maze.ghost_spawns[0])
    ghost_position = (ghost.x, ghost.y, ghost.current_dir)

    action = agent.choose_action(
        maze,
        maze.pacman_spawn,
        [ghost],
        current_direction=Direction.NONE,
    )

    assert action != Direction.RIGHT
    assert (ghost.x, ghost.y, ghost.current_dir) == ghost_position
    assert agent.minimax.nodes_visited > 0


def test_minimax_takes_a_power_pellet_instead_of_avoiding_ghost_forever():
    maze = Maze(["#######", "#..o..#", "#######"])
    planner = MinimaxPlanner(depth=3)

    action, scores = planner.choose_action(
        maze,
        (2, 1),
        [(3, 1)],
    )

    assert action == Direction.RIGHT
    assert scores[action] > -MINIMAX_GHOST_COLLISION_PENALTY


def test_minimax_rewards_pellet_progress_and_level_completion():
    maze = Maze(["#######", "#P...##", "#######"])
    planner = MinimaxPlanner(depth=3)
    action, _ = planner.choose_action(maze, maze.pacman_spawn, [])

    assert action == Direction.RIGHT

    winning_state = SearchState(
        pacman=(4, 1),
        ghosts=(),
        dots=frozenset(),
        power_pellets=frozenset(),
        power_active=False,
        lives=3,
        recent_tiles=(),
    )
    assert planner.evaluate_state(maze, winning_state) > 0


def test_minimax_penalizes_recently_repeated_positions():
    maze = Maze(["#####", "#...#", "#####"])
    planner = MinimaxPlanner(depth=1)
    state = SearchState(
        pacman=(2, 1),
        ghosts=(),
        dots=frozenset({(3, 1)}),
        power_pellets=frozenset(),
        power_active=False,
        lives=3,
        recent_tiles=(),
    )
    repeated_state = SearchState(
        pacman=state.pacman,
        ghosts=state.ghosts,
        dots=state.dots,
        power_pellets=state.power_pellets,
        power_active=state.power_active,
        lives=state.lives,
        recent_tiles=((2, 1), (2, 1)),
    )

    assert planner.evaluate_state(maze, repeated_state) < planner.evaluate_state(
        maze, state
    )


def test_ai_game_completes_level_one_without_ghosts_and_starts_transition():
    maze = Maze(
        [
            "########",
            "#P....##",
            "########",
        ]
    )
    state = GameState(maze, ai_enabled=True, minimax_depth=4)
    state.ghosts.clear()

    for _ in range(600):
        state.update()
        if state.mode.name == "LEVEL_TRANSITION":
            break

    assert state.mode.name == "LEVEL_TRANSITION"
    assert state.lives == 3
    assert state.maze.remaining_dots_count() == 0


def test_ai_game_makes_progress_on_default_level():
    state = GameState(ai_enabled=True, minimax_depth=6)
    initial_dots = state.maze.remaining_dots_count()

    for _ in range(6000):
        state.update()
        if state.mode.name != "PLAYING":
            break

    assert state.mode.name in {"GAME_OVER", "LEVEL_TRANSITION"}
    assert state.score > 0
    assert state.maze.remaining_dots_count() < initial_dots


def test_ai_game_survives_the_first_escape_from_a_closing_ghost():
    maze = Maze(
        [
            "#########",
            "#.......#",
            "#..PG...#",
            "#.......#",
            "#########",
        ]
    )
    state = GameState(maze, ai_enabled=True, minimax_depth=4)

    for _ in range(12):
        state.update()

    assert state.lives == 3
    assert (state.pacman.col, state.pacman.row) != maze.pacman_spawn


def test_pacman_movement_stops_at_walls_and_reaches_tile_centers():
    maze = Maze(["#####", "#...#", "#####"])
    pacman = Pacman(1, 1)
    pacman.set_next_direction(Direction.RIGHT)

    for _ in range(100):
        pacman.update(maze)
        assert maze.is_walkable(pacman.col, pacman.row)

    assert (pacman.col, pacman.row) == (3, 1)
    assert pacman.x == 3.5 * TILE_SIZE


def test_minimax_depth_six_is_responsive_on_the_default_maze():
    maze = Maze()
    planner = MinimaxPlanner(depth=6)
    action, scores = planner.choose_action(
        maze,
        maze.pacman_spawn,
        [Ghost(*spawn) for spawn in maze.ghost_spawns],
    )

    assert action in scores
    assert planner.nodes_visited < 100_000
