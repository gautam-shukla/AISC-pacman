"""Behavioral tests for Minimax-controlled ghost decisions."""
from ghost_minimax import GhostMinimaxPlanner
from game_state import GameState
from maze import Maze
from settings import Direction


def test_ghost_pursues_pacman_in_a_safe_corridor():
    maze = Maze(["#####", "#...#", "#####"])
    planner = GhostMinimaxPlanner(depth=4, random_seed=4)

    action = planner.choose_action(
        maze,
        pacman=(3, 1),
        ghost=(1, 1),
        ghost_direction=Direction.RIGHT,
    )

    assert action == Direction.RIGHT


def test_ghost_replans_when_pacman_changes_direction():
    maze = Maze(
        [
            "#####",
            "#...#",
            "#...#",
            "#...#",
            "#####",
        ]
    )
    planner = GhostMinimaxPlanner(depth=1)

    first_action = planner.choose_action(
        maze, (3, 2), (1, 2), Direction.RIGHT
    )
    changed_action = planner.choose_action(
        maze, (1, 1), (2, 2), Direction.RIGHT
    )

    assert first_action == Direction.RIGHT
    assert changed_action == Direction.UP


def test_ghost_only_selects_legal_moves_and_does_not_reverse_at_intersection():
    maze = Maze(
        [
            "#####",
            "#...#",
            "#...#",
            "#...#",
            "#####",
        ]
    )
    planner = GhostMinimaxPlanner(depth=3)

    action = planner.choose_action(
        maze, (3, 2), (2, 2), Direction.RIGHT
    )

    assert action in (Direction.UP, Direction.DOWN, Direction.RIGHT)
    assert maze.is_walkable(2 + action[0], 2 + action[1])


def test_ghost_avoids_pacman_while_vulnerable():
    maze = Maze(["#######", "#.....#", "#######"])
    planner = GhostMinimaxPlanner(depth=4)

    action = planner.choose_action(
        maze,
        pacman=(1, 1),
        ghost=(3, 1),
        ghost_direction=Direction.LEFT,
        power_active=True,
    )

    assert action == Direction.RIGHT
    assert planner.last_scores[action] > planner.last_scores[Direction.LEFT]


def test_powered_ghost_does_not_reverse_back_and_forth_at_dead_end():
    maze = Maze(
        [
            "#########",
            "#.......#",
            "#.#####.#",
            "#.#...#.#",
            "#.#.#.#.#",
            "#...#...#",
            "#########",
        ]
    )
    planner = GhostMinimaxPlanner(depth=4, random_seed=4)

    first_action = planner.choose_action(
        maze,
        pacman=(1, 1),
        ghost=(3, 4),
        ghost_direction=Direction.UP,
        power_active=True,
    )
    second_action = planner.choose_action(
        maze,
        pacman=(1, 1),
        ghost=(3, 3),
        ghost_direction=first_action,
        power_active=True,
    )

    assert first_action == Direction.UP
    assert second_action == Direction.RIGHT


def test_ghost_with_no_legal_moves_stops_safely():
    maze = Maze(["###", "#.#", "###"])
    planner = GhostMinimaxPlanner(depth=4)

    action = planner.choose_action(
        maze,
        pacman=(1, 1),
        ghost=(1, 1),
        ghost_direction=Direction.NONE,
    )

    assert action == Direction.NONE
    assert planner.last_scores == {}


def test_pacman_with_no_legal_moves_is_evaluated_without_crashing():
    maze = Maze(
        [
            "#########",
            "#.###...#",
            "#########",
        ]
    )
    planner = GhostMinimaxPlanner(depth=3)

    action = planner.choose_action(
        maze,
        pacman=(1, 1),
        ghost=(6, 1),
        ghost_direction=Direction.LEFT,
    )

    assert action in (Direction.LEFT, Direction.RIGHT)


def test_ghost_minimax_uses_other_ghost_positions_in_simulated_collisions():
    maze = Maze(["#########", "#.......#", "#########"])
    planner = GhostMinimaxPlanner(depth=2)

    action = planner.choose_action(
        maze,
        pacman=(4, 1),
        ghost=(2, 1),
        ghost_direction=Direction.RIGHT,
        other_ghosts=((5, 1),),
    )
    score_with_other_ghost = planner.last_scores[action]
    planner.choose_action(
        maze,
        pacman=(4, 1),
        ghost=(2, 1),
        ghost_direction=Direction.RIGHT,
    )

    assert action == Direction.RIGHT
    assert score_with_other_ghost == 1000.0
    assert planner.last_scores[Direction.RIGHT] < score_with_other_ghost


def test_ghost_minimax_penalizes_clustering_with_other_ghosts():
    maze = Maze(
        [
            "#######",
            "#.....#",
            "#.....#",
            "#.....#",
            "#.....#",
            "#.....#",
            "#######",
        ]
    )
    planner = GhostMinimaxPlanner(depth=1)

    clustered_score = planner._evaluate(
        maze,
        pacman=(5, 5),
        ghost=(3, 3),
        other_ghosts=((3, 4),),
        power_active=False,
        player_lives=3,
    )
    separated_score = planner._evaluate(
        maze,
        pacman=(5, 5),
        ghost=(3, 3),
        other_ghosts=((1, 1),),
        power_active=False,
        player_lives=3,
    )

    assert separated_score > clustered_score


def test_ghost_tie_breaking_is_seeded_and_stays_with_equal_scores():
    maze = Maze(
        [
            "#########",
            "#.......#",
            "#.#####.#",
            "#.#...#.#",
            "#.#.#.#.#",
            "#...#...#",
            "#########",
        ]
    )
    actions = []
    for seed in (0, 0, 1):
        planner = GhostMinimaxPlanner(depth=4, random_seed=seed)
        actions.append(
            planner.choose_action(
                maze,
                pacman=(1, 1),
                ghost=(3, 4),
                ghost_direction=Direction.UP,
                power_active=True,
            )
        )
        assert len(set(planner.last_scores.values())) == 1

    assert actions[0] == actions[1]
    assert actions[0] != actions[2]


def test_ghost_search_uses_current_speed_when_power_is_about_to_expire():
    maze = Maze(["#####", "#...#", "#####"])
    scores = []
    for speed in (32.0, 1.0):
        planner = GhostMinimaxPlanner(depth=1, random_seed=2)
        planner.choose_action(
            maze,
            pacman=(2, 1),
            ghost=(1, 1),
            ghost_direction=Direction.RIGHT,
            power_active=True,
            power_ticks_remaining=5,
            ghost_speed=speed,
        )
        scores.append(planner.last_scores[Direction.RIGHT])

    assert scores == [-1000.0, 1000.0]


def test_default_ghosts_have_separate_minimax_state_and_spread_spawns():
    state = GameState()
    spawns = [(ghost.spawn_col, ghost.spawn_row) for ghost in state.ghosts]
    planners = [ghost.minimax for ghost in state.ghosts]

    assert len(spawns) == 4
    assert len(set(spawns)) == len(spawns)
    assert len({id(planner) for planner in planners}) == len(planners)
    assert all(
        abs(first[0] - second[0]) + abs(first[1] - second[1]) >= 10
        for index, first in enumerate(spawns)
        for second in spawns[index + 1 :]
    )


def test_clearing_the_last_collectible_is_a_terminal_win_for_pacman():
    maze = Maze(["#####", "#G.P#", "#####"])
    maze.dots = {(2, 1)}
    planner = GhostMinimaxPlanner(depth=2)

    planner.choose_action(
        maze,
        pacman=(3, 1),
        ghost=(1, 1),
        ghost_direction=Direction.RIGHT,
    )

    assert planner.last_scores[Direction.RIGHT] == -1000.0


def test_game_state_configures_depth_for_each_ghost():
    maze = Maze(["#####", "#P.G#", "#####"])

    state = GameState(maze, ghost_minimax_depth=5)

    assert state.ghosts[0].minimax.depth == 5


def test_last_remaining_life_is_scored_as_game_over():
    maze = Maze(["#####", "#...#", "#####"])
    planner = GhostMinimaxPlanner(depth=1)

    planner.choose_action(
        maze,
        pacman=(2, 1),
        ghost=(1, 1),
        ghost_direction=Direction.RIGHT,
        player_lives=1,
    )

    assert planner.last_scores[Direction.RIGHT] == 2000.0


def test_ghost_minimax_alpha_beta_pruning_tracks_pruned_branches():
    maze = Maze(
        [
            "#######",
            "#.....#",
            "#.###.#",
            "#.....#",
            "#######",
        ]
    )
    planner = GhostMinimaxPlanner(depth=4)
    action = planner.choose_action(
        maze,
        pacman=(3, 3),
        ghost=(1, 1),
        ghost_direction=Direction.RIGHT,
    )
    assert action in (Direction.RIGHT, Direction.DOWN)
    assert planner.nodes_visited > 0
    assert hasattr(planner, "pruned_branches")
