"""
game_state.py - Core game loop state, scoring, lives, and collision resolution.
"""
from typing import List, Optional
import pygame
from settings import (
    GameMode,
    INITIAL_LIVES,
    COLOR_GHOST_RED,
)
from maze import Maze
from pacman import Pacman
from ghost import Ghost


class GameState:
    """Encapsulates the runtime state, collision detection, and win/loss rules."""

    def __init__(self, maze: Optional[Maze] = None):
        self.maze = maze or Maze()
        self.score = 0
        self.lives = INITIAL_LIVES
        self.level = 1
        self.mode = GameMode.PLAYING

        # Entities
        p_col, p_row = self.maze.pacman_spawn
        self.pacman = Pacman(p_col, p_row)

        self.ghosts: List[Ghost] = []
        for g_col, g_row in self.maze.ghost_spawns:
            self.ghosts.append(Ghost(g_col, g_row, COLOR_GHOST_RED))

        # Death respawn delay counter
        self.death_pause_ticks = 0

    def toggle_pause(self) -> None:
        """Toggles between PLAYING and PAUSED modes."""
        if self.mode == GameMode.PLAYING:
            self.mode = GameMode.PAUSED
        elif self.mode == GameMode.PAUSED:
            self.mode = GameMode.PLAYING

    def restart_game(self) -> None:
        """Fully resets the game to initial state."""
        self.score = 0
        self.lives = INITIAL_LIVES
        self.maze.reset_collectibles()
        self.reset_positions()
        self.mode = GameMode.PLAYING

    def reset_positions(self) -> None:
        """Resets Pac-Man and all ghosts to their spawn tiles."""
        self.pacman.reset_position()
        for ghost in self.ghosts:
            ghost.reset_position()

    def update(self) -> None:
        """Executes one frame of game logic."""
        if self.mode != GameMode.PLAYING:
            return

        if self.death_pause_ticks > 0:
            self.death_pause_ticks -= 1
            if self.death_pause_ticks == 0:
                self.reset_positions()
            return

        # 1. Update Pac-Man
        self.pacman.update(self.maze)

        # 2. Collect dots and power pellets
        earned = self.maze.eat_dot(self.pacman.col, self.pacman.row)
        if earned > 0:
            self.score += earned

        pellet_earned = self.maze.eat_power_pellet(self.pacman.col, self.pacman.row)
        if pellet_earned > 0:
            self.score += pellet_earned

        # 3. Check victory condition (all dots cleared)
        if self.maze.remaining_dots_count() == 0:
            self.mode = GameMode.VICTORY
            return

        # 4. Update ghosts and check collisions
        pacman_rect = self.pacman.get_rect()
        for ghost in self.ghosts:
            ghost.update(self.maze)

            # Check collision between Pac-Man and Ghost
            if pacman_rect.colliderect(ghost.get_rect()):
                self._handle_player_hit()
                break

    def _handle_player_hit(self) -> None:
        """Handles Pac-Man losing a life or triggering Game Over."""
        self.lives -= 1
        if self.lives <= 0:
            self.mode = GameMode.GAME_OVER
        else:
            # Short freeze before respawn
            self.death_pause_ticks = 30
