"""
test_game_state.py - Unit tests for Phase 2 gameplay rules, collisions, scoring, and win/loss states.
"""
import os
import pytest

# Ensure headless execution in CI / terminal
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()

from settings import (
    GameMode,
    Direction,
    INITIAL_LIVES,
    DOT_POINTS,
    DIFFICULTY_MAX,
    DIFFICULTY_MIN,
    DIFFICULTY_STEP,
    DIFFICULTY_EVALUATION_FRAMES,
    POWER_PELLET_POINTS,
    RESPAWN_INVULNERABILITY_TICKS,
    TILE_SIZE,
)
from maze import Maze
from pacman import Pacman
from ghost import Ghost
from game_state import GameState


# Small simple 5x5 test maze layout
# #####
# #P.G#
# #.o.#
# #...#
# #####
SIMPLE_MAZE = [
    "#####",
    "#P.G#",
    "#.o.#",
    "#...#",
    "#####",
]


@pytest.fixture
def test_maze():
    return Maze(SIMPLE_MAZE)


@pytest.fixture
def game_state(test_maze):
    return GameState(test_maze)


def test_maze_initialization(test_maze):
    """Verifies parsing of walls, dots, power pellets, and spawn points."""
    assert test_maze.is_wall(0, 0)
    assert not test_maze.is_wall(1, 1)  # Pacman spawn is walkable
    assert test_maze.pacman_spawn == (1, 1)
    assert (3, 1) in test_maze.ghost_spawns
    assert (2, 1) in test_maze.dots
    assert (2, 2) in test_maze.power_pellets
    assert test_maze.total_dots_count() > 0


def test_pacman_wall_collision(game_state):
    """Pac-Man must not penetrate walls."""
    pacman = game_state.pacman
    maze = game_state.maze

    # Pac-man spawns at (1, 1). Tile (0, 1) is a wall.
    pacman.set_next_direction(Direction.LEFT)
    for _ in range(15):
        pacman.update(maze)

    # Position must stay in column 1 (cannot enter column 0)
    assert pacman.col == 1
    assert pacman.x >= 0.5 * TILE_SIZE


def test_pacman_eats_dot_and_scores(game_state):
    """Pac-Man collects dots, increments score, and decrements dots remaining."""
    pacman = game_state.pacman
    initial_dots = game_state.maze.remaining_dots_count()
    initial_score = game_state.score

    # Move right towards (2, 1) where a dot is located
    pacman.set_next_direction(Direction.RIGHT)
    for _ in range(10):
        game_state.update()

    assert game_state.score == initial_score + DOT_POINTS
    assert game_state.maze.remaining_dots_count() == initial_dots - 1


def test_ghost_collision_decrements_lives(game_state):
    """Collision with a ghost reduces lives and pauses for respawn."""
    assert game_state.lives == INITIAL_LIVES

    # Move Pac-Man and Ghost onto the exact same coordinates
    game_state.pacman.x = 2.0 * TILE_SIZE
    game_state.pacman.y = 1.0 * TILE_SIZE
    game_state.ghosts[0].x = 2.0 * TILE_SIZE
    game_state.ghosts[0].y = 1.0 * TILE_SIZE

    game_state.update()

    assert game_state.lives == INITIAL_LIVES - 1
    assert game_state.difficulty_multiplier == 1.0 - DIFFICULTY_STEP
    assert game_state.death_pause_ticks > 0


def test_game_over_when_lives_exhausted(game_state):
    """When lives reach 0, game state switches to GAME_OVER."""
    game_state.lives = 1
    game_state.pacman.x = 2.0 * TILE_SIZE
    game_state.pacman.y = 1.0 * TILE_SIZE
    game_state.ghosts[0].x = 2.0 * TILE_SIZE
    game_state.ghosts[0].y = 1.0 * TILE_SIZE

    game_state.update()

    assert game_state.lives == 0
    assert game_state.mode == GameMode.GAME_OVER


def test_victory_when_all_dots_eaten(game_state):
    """Clearing all collectibles triggers VICTORY state."""
    # Clear all dots except one
    game_state.maze.dots.clear()
    game_state.maze.power_pellets.clear()
    game_state.maze.dots.add((2, 1))

    # Move Pac-Man to eat the last dot
    game_state.pacman.x = (2 + 0.5) * TILE_SIZE
    game_state.pacman.y = (1 + 0.5) * TILE_SIZE
    game_state.pacman.col = 2
    game_state.pacman.row = 1

    game_state.update()

    assert game_state.maze.remaining_dots_count() == 0
    assert game_state.mode == GameMode.VICTORY


def test_pause_and_restart(game_state):
    """Tests pause toggle and restart functionality."""
    assert game_state.mode == GameMode.PLAYING
    game_state.toggle_pause()
    assert game_state.mode == GameMode.PAUSED
    game_state.toggle_pause()
    assert game_state.mode == GameMode.PLAYING

    # Modify state then restart
    game_state.score = 500
    game_state.lives = 1
    game_state.restart_game()
    assert game_state.score == 0
    assert game_state.lives == INITIAL_LIVES
    assert game_state.mode == GameMode.PLAYING


def test_life_loss_resets_entities_but_preserves_progress(game_state):
    game_state.score = 500
    pacman = game_state.pacman
    ghost = game_state.ghosts[0]
    pacman.col, pacman.row = 2, 1
    pacman.x, pacman.y = 2.5 * TILE_SIZE, 1.5 * TILE_SIZE
    pacman.current_dir = Direction.RIGHT
    pacman.next_dir = Direction.UP
    ghost.col, ghost.row = 2, 1
    ghost.x, ghost.y = pacman.x, pacman.y
    dots_before = game_state.maze.remaining_dots_count()

    game_state.update()

    assert game_state.lives == INITIAL_LIVES - 1
    assert game_state.score >= 500
    assert game_state.maze.remaining_dots_count() < dots_before
    assert (pacman.col, pacman.row) == game_state.maze.pacman_spawn
    assert pacman.current_dir == Direction.NONE
    assert pacman.next_dir == Direction.NONE
    assert (ghost.col, ghost.row) == (ghost.spawn_col, ghost.spawn_row)
    assert game_state.death_pause_ticks > 0
    assert game_state.respawn_invulnerability_ticks == RESPAWN_INVULNERABILITY_TICKS


def test_life_loss_resets_every_ghost_to_its_own_spawn():
    maze = Maze(["#######", "#P.G.G#", "#.....#", "#######"])
    state = GameState(maze)
    assert len(state.ghosts) == 2
    for ghost in state.ghosts:
        ghost.col, ghost.row = state.pacman.col, state.pacman.row
        ghost.x, ghost.y = state.pacman.x, state.pacman.y
        ghost.current_dir = Direction.UP

    state.update()

    assert state.lives == INITIAL_LIVES - 1
    for ghost in state.ghosts:
        assert (ghost.col, ghost.row) == (ghost.spawn_col, ghost.spawn_row)
        assert ghost.x == (ghost.spawn_col + 0.5) * TILE_SIZE
        assert ghost.y == (ghost.spawn_row + 0.5) * TILE_SIZE
        assert ghost.current_dir == Direction.LEFT


def test_respawn_invulnerability_prevents_immediate_collision(game_state):
    game_state.respawn_invulnerability_ticks = 1
    game_state.pacman.current_dir = Direction.NONE
    ghost = game_state.ghosts[0]
    ghost.col, ghost.row = game_state.pacman.col, game_state.pacman.row
    ghost.x, ghost.y = game_state.pacman.x, game_state.pacman.y

    game_state.update()

    assert game_state.lives == INITIAL_LIVES
    assert game_state.respawn_invulnerability_ticks == 0


def test_difficulty_adjusts_gradually_within_limits(game_state):
    game_state._difficulty_lives_lost = 1
    game_state._evaluate_difficulty()
    assert game_state.difficulty_multiplier == 1.0 - DIFFICULTY_STEP

    game_state._difficulty_lives_lost = 0
    for _ in range(20):
        game_state._evaluate_difficulty()
    assert game_state.difficulty_multiplier <= DIFFICULTY_MAX
    assert game_state.difficulty_multiplier > 1.0
    assert game_state.difficulty_label == "Hard"

    for _ in range(40):
        game_state._difficulty_lives_lost = 1
        game_state._evaluate_difficulty()
    assert game_state.difficulty_multiplier >= DIFFICULTY_MIN
    assert game_state.difficulty_label == "Easy"


def test_restart_resets_difficulty_tracking(game_state):
    game_state.difficulty_multiplier = 1.2
    game_state.difficulty_elapsed_frames = 900

    game_state.restart_game()

    assert game_state.difficulty_multiplier == 1.0
    assert game_state.difficulty_elapsed_frames == 0
    assert game_state.difficulty_label == "Normal"


def test_survival_updates_difficulty_on_configured_interval(game_state):
    game_state._difficulty_frames = DIFFICULTY_EVALUATION_FRAMES - 1

    game_state.update()

    assert game_state.difficulty_elapsed_frames == 1
    assert game_state.difficulty_multiplier == 1.0 + DIFFICULTY_STEP
