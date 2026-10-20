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
    POWER_PELLET_POINTS,
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
