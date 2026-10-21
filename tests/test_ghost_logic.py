"""Regression tests for role-based ghost navigation and power-pellet behavior."""
import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

pygame.init()

from game_state import GameState
from ghost import Ghost
from maze import Maze
from pacman import Pacman
from settings import (
    COLOR_GHOST_FLEE,
    GHOST_POINTS,
    GhostState,
    GhostType,
    INITIAL_LIVES,
)


def test_hunter_chases_player_through_walkable_corridor():
    maze = Maze(["#####", "#...#", "#####"])
    ghost = Ghost(1, 1, ghost_type=GhostType.HUNTER)
    pacman = Pacman(3, 1)

    ghost.update(maze, pacman)

    assert ghost.current_dir == (1, 0)
    assert ghost.state == GhostState.CHASE


def test_ambusher_targets_ahead_of_player():
    maze = Maze(["#######", "#.....#", "#######"])
    ghost = Ghost(1, 1, ghost_type=GhostType.AMBUSHER)
    pacman = Pacman(4, 1)
    pacman.current_dir = (1, 0)

    ghost.update(maze, pacman)

    assert ghost.current_dir == (1, 0)


def test_powered_ghost_flees_and_uses_frightened_color():
    maze = Maze(["#######", "#.....#", "#######"])
    ghost = Ghost(3, 1, ghost_type=GhostType.HUNTER)
    pacman = Pacman(1, 1)

    ghost.update(maze, pacman, protection=1.0)

    assert ghost.state == GhostState.FLEE
    assert ghost.color == COLOR_GHOST_FLEE
    assert ghost.current_dir == (1, 0)


def test_powered_collision_scores_ghost_without_losing_life():
    maze = Maze(["#####", "#P.G#", "#...#", "#####"])
    state = GameState(maze)
    ghost = state.ghosts[0]
    state.power_ticks_remaining = 10
    state.pacman.x = ghost.x
    state.pacman.y = ghost.y
    state.pacman.col = ghost.col
    state.pacman.row = ghost.row
    initial_score = state.score

    state.update()

    assert state.score == initial_score + GHOST_POINTS
    assert state.lives == INITIAL_LIVES
    assert (ghost.col, ghost.row) == (ghost.spawn_col, ghost.spawn_row)
