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
    DEFAULT_MAZE,
    GHOST_POINTS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SIZE,
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


def test_expanded_default_maze_fits_screen_and_all_collectibles_are_reachable():
    maze = Maze(DEFAULT_MAZE)
    assert (maze.cols, maze.rows) == (25, 25)
    assert SCREEN_WIDTH == maze.cols * TILE_SIZE
    assert SCREEN_HEIGHT >= maze.rows * TILE_SIZE

    reachable = {maze.pacman_spawn}
    frontier = [maze.pacman_spawn]
    while frontier:
        col, row = frontier.pop()
        for neighbor in (
            (col, row - 1),
            (col, row + 1),
            (col - 1, row),
            (col + 1, row),
        ):
            if maze.is_walkable(*neighbor) and neighbor not in reachable:
                reachable.add(neighbor)
                frontier.append(neighbor)

    assert maze.dots <= reachable
    assert maze.power_pellets <= reachable
    assert set(maze.ghost_spawns) <= reachable


def test_ghost_speed_changes_gradually_without_missing_tile_centers():
    maze = Maze(["#######", "#.....#", "#######"])
    pacman = Pacman(5, 1)
    easy = Ghost(1, 1, ghost_type=GhostType.HUNTER)
    hard = Ghost(1, 1, ghost_type=GhostType.HUNTER)

    easy.update(maze, pacman, difficulty_multiplier=0.8)
    hard.update(maze, pacman, difficulty_multiplier=1.2)
    assert hard.speed > easy.speed

    ghost = Ghost(1, 1, ghost_type=GhostType.HUNTER)
    visited = {ghost.col}
    for _ in range(120):
        previous_col = ghost.col
        ghost.update(maze)
        if ghost.col != previous_col:
            assert ghost.x == (ghost.col + 0.5) * TILE_SIZE
            visited.add(ghost.col)

    assert visited == {1, 2, 3, 4, 5}
    assert ghost.y == 1.5 * TILE_SIZE
    assert 1 <= ghost.col <= 5
