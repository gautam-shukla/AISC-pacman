"""Behavioral unit tests for Simulated Annealing ghost decision-making."""
from ghost_sa import GhostSimulatedAnnealingPlanner
from game_state import GameState
from ghost import Ghost
from maze import Maze
from settings import Direction


def test_sa_planner_initialization_and_cooling():
    planner = GhostSimulatedAnnealingPlanner(initial_temp=5.0, cooling_rate=0.9)
    assert planner.temp == 5.0
    assert planner.steps == 0

    maze = Maze(["#####", "#...#", "#####"])
    action = planner.choose_action(maze, pacman=(3, 1), ghost=(1, 1), ghost_direction=Direction.RIGHT)

    assert action == Direction.RIGHT
    assert planner.steps == 1
    assert planner.temp == 5.0 * 0.9  # 4.5


def test_sa_planner_reset_restores_temperature():
    planner = GhostSimulatedAnnealingPlanner(initial_temp=5.0, cooling_rate=0.5)
    maze = Maze(["#####", "#...#", "#####"])
    planner.choose_action(maze, (3, 1), (1, 1), Direction.RIGHT)
    assert planner.temp == 2.5

    planner.reset()
    assert planner.temp == 5.0
    assert planner.steps == 0


def test_sa_cold_temperature_picks_greedy_optimal_move():
    maze = Maze(
        [
            "#####",
            "#...#",
            "#...#",
            "#...#",
            "#####",
        ]
    )
    # At very cold temp (e.g. 0.001), SA must pick the highest scoring move greedily
    planner = GhostSimulatedAnnealingPlanner(initial_temp=0.001, min_temp=0.001, random_seed=42)
    action = planner.choose_action(maze, pacman=(2, 3), ghost=(2, 1), ghost_direction=Direction.DOWN)

    assert action == Direction.DOWN
    # Down should have ~100% of the probability mass
    assert planner.last_probabilities[Direction.DOWN] > 0.99


def test_sa_frightened_ghost_runs_away():
    maze = Maze(["#######", "#.....#", "#######"])
    planner = GhostSimulatedAnnealingPlanner(initial_temp=0.01, min_temp=0.01, random_seed=1)
    action = planner.choose_action(
        maze,
        pacman=(2, 1),
        ghost=(3, 1),
        ghost_direction=Direction.LEFT,
        power_active=True,
    )
    assert action == Direction.RIGHT


def test_game_state_supports_sa_and_alternate_modes():
    # Test pure SA mode
    state_sa = GameState(ghost_algo="sa")
    assert state_sa.current_ghost_algo == "sa"
    assert state_sa.ghost_algo_label == "Simulated Annealing"
    assert isinstance(state_sa.ghosts[0].planner, GhostSimulatedAnnealingPlanner)

    # Test alternate mode (Round 1: Minimax, Round 2: SA)
    state_alt = GameState(ghost_algo="alternate")
    assert state_alt.level == 1
    assert state_alt.current_ghost_algo == "minimax"
    assert "Minimax" in state_alt.ghost_algo_label

    # Simulate transition to Level 2
    state_alt._load_level(2)
    assert state_alt.level == 2
    assert state_alt.current_ghost_algo == "sa"
    assert "Simulated Annealing" in state_alt.ghost_algo_label
    assert isinstance(state_alt.ghosts[0].planner, GhostSimulatedAnnealingPlanner)

    # Test dynamic real-time toggle
    state_alt.toggle_ghost_algo()
    assert state_alt.current_ghost_algo == "minimax"
    assert hasattr(state_alt.ghosts[0].planner, "depth")


def test_sa_simulation_runs_frames_without_crashing():
    state = GameState(ghost_algo="sa", ai_enabled=True, random_seed=10)
    for _ in range(60):
        state.update()
    assert state.lives == 3
    assert state.score > 0
