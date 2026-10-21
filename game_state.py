"""
game_state.py - Core game loop state, scoring, lives, and collision resolution.
"""
from typing import List, Optional
import pygame
from settings import (
    GameMode,
    GhostType,
    GHOST_POINTS,
    INITIAL_LIVES,
    POWER_PELLET_DURATION,
    DIFFICULTY_MIN,
    DIFFICULTY_MAX,
    DIFFICULTY_STEP,
    DIFFICULTY_EVALUATION_FRAMES,
    DIFFICULTY_EMA_ALPHA,
    DIFFICULTY_EASY_THRESHOLD,
    DIFFICULTY_HARD_THRESHOLD,
    RESPAWN_PAUSE_TICKS,
    RESPAWN_INVULNERABILITY_TICKS,
    AI_PENALTY_DANGER,
    AI_PENALTY_DEAD_END,
    AI_PENALTY_LIFE_LOST,
    AI_REWARD_DOT,
    AI_REWARD_GHOST_EATEN,
    AI_REWARD_POWER_PELLET,
    AI_REWARD_SURVIVAL,
    TILE_SIZE,
    MINIMAX_SEARCH_DEPTH,
)
from maze import Maze
from pacman import Pacman
from ghost import Ghost


class GameState:
    """Encapsulates the runtime state, collision detection, and win/loss rules."""

    def __init__(
        self,
        maze: Optional[Maze] = None,
        ai_enabled: bool = False,
        ai_q_table_path: Optional[str] = None,
        minimax_depth: int = MINIMAX_SEARCH_DEPTH,
        ai_debug: bool = False,
    ):
        self.maze = maze or Maze()
        self.score = 0
        self.lives = INITIAL_LIVES
        self.level = 1
        self.mode = GameMode.PLAYING
        self.power_ticks_remaining = 0
        self.respawn_invulnerability_ticks = 0
        self.difficulty_multiplier = 1.0
        self.difficulty_performance = 0.0
        self.difficulty_elapsed_frames = 0
        self._difficulty_frames = 0
        self._difficulty_lives_lost = 0
        self._difficulty_score_checkpoint = 0
        self.ai_enabled = ai_enabled
        self.ai_player = None
        if ai_enabled:
            from pacman_ai import PacmanAI

            self.ai_player = PacmanAI(
                q_table_path=ai_q_table_path,
                minimax_depth=minimax_depth,
                debug=ai_debug,
            )

        # Entities
        p_col, p_row = self.maze.pacman_spawn
        self.pacman = Pacman(p_col, p_row)

        self.ghosts: List[Ghost] = []
        ghost_types = list(GhostType)
        for index, (g_col, g_row) in enumerate(self.maze.ghost_spawns):
            ghost_type = ghost_types[index % len(ghost_types)]
            self.ghosts.append(Ghost(g_col, g_row, ghost_type=ghost_type))

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
        self.power_ticks_remaining = 0
        self.death_pause_ticks = 0
        self.respawn_invulnerability_ticks = 0
        self._reset_difficulty_tracking()
        if self.ai_player is not None:
            self.ai_player.previous_state = None
            self.ai_player.previous_action = None
            self.ai_player.last_decision_tile = None
            self.ai_player.pending_reward = 0.0
        self.maze.reset_collectibles()
        self.reset_positions()
        self.mode = GameMode.PLAYING

    def reset_positions(self) -> None:
        """Resets Pac-Man and all ghosts to their spawn tiles."""
        self.power_ticks_remaining = 0
        self.pacman.reset_position()
        for ghost in self.ghosts:
            ghost.reset_position()

    @property
    def difficulty_label(self) -> str:
        if self.difficulty_multiplier < DIFFICULTY_EASY_THRESHOLD:
            return "Easy"
        if self.difficulty_multiplier > DIFFICULTY_HARD_THRESHOLD:
            return "Hard"
        return "Normal"

    def _reset_difficulty_tracking(self) -> None:
        self.difficulty_multiplier = 1.0
        self.difficulty_performance = 0.0
        self.difficulty_elapsed_frames = 0
        self._difficulty_frames = 0
        self._difficulty_lives_lost = 0
        self._difficulty_score_checkpoint = self.score

    def _evaluate_difficulty(self) -> None:
        """Smoothly tune difficulty using survival, recent losses, and score."""
        score_gained = max(0, self.score - self._difficulty_score_checkpoint)
        score_bonus = min(score_gained / 1000.0, 0.5)
        interval_performance = 1.0 - (2.0 * self._difficulty_lives_lost) + score_bonus
        self.difficulty_performance = (
            (1.0 - DIFFICULTY_EMA_ALPHA) * self.difficulty_performance
            + DIFFICULTY_EMA_ALPHA * interval_performance
        )

        if self.difficulty_performance >= 0.25:
            self.difficulty_multiplier = min(
                DIFFICULTY_MAX,
                self.difficulty_multiplier + DIFFICULTY_STEP,
            )
        elif self.difficulty_performance <= -0.25:
            self.difficulty_multiplier = max(
                DIFFICULTY_MIN,
                self.difficulty_multiplier - DIFFICULTY_STEP,
            )

        self._difficulty_frames = 0
        self._difficulty_lives_lost = 0
        self._difficulty_score_checkpoint = self.score

    def update(self) -> None:
        """Executes one frame of game logic."""
        if self.mode != GameMode.PLAYING:
            return

        if self.death_pause_ticks > 0:
            self.death_pause_ticks -= 1
            return

        self.difficulty_elapsed_frames += 1
        self._difficulty_frames += 1
        if self._difficulty_frames >= DIFFICULTY_EVALUATION_FRAMES:
            self._evaluate_difficulty()

        invulnerability_was_active = self.respawn_invulnerability_ticks > 0
        ai_reward = AI_REWARD_SURVIVAL
        life_lost_this_frame = False

        if self.ai_player is not None:
            self._choose_ai_direction()

        if self.ai_player is not None:
            tile = (self.pacman.col, self.pacman.row)
            legal = self.ai_player.planner.legal_actions(self.maze, tile)
            ghost_tiles = [(ghost.col, ghost.row) for ghost in self.ghosts]
            if any(
                abs(tile[0] - ghost_col) + abs(tile[1] - ghost_row) <= 2
                for ghost_col, ghost_row in ghost_tiles
            ):
                ai_reward -= AI_PENALTY_DANGER
            if len(legal) <= 1 and any(
                abs(tile[0] - ghost_col) + abs(tile[1] - ghost_row) <= 4
                for ghost_col, ghost_row in ghost_tiles
            ):
                ai_reward -= AI_PENALTY_DEAD_END

        # 1. Update Pac-Man
        self.pacman.update(self.maze)

        # 2. Collect dots and power pellets
        earned = self.maze.eat_dot(self.pacman.col, self.pacman.row)
        if earned > 0:
            self.score += earned
            ai_reward += AI_REWARD_DOT

        pellet_earned = self.maze.eat_power_pellet(self.pacman.col, self.pacman.row)
        if pellet_earned > 0:
            self.score += pellet_earned
            self.power_ticks_remaining = POWER_PELLET_DURATION
            ai_reward += AI_REWARD_POWER_PELLET

        # 3. Check victory condition (all dots cleared)
        if self.maze.remaining_dots_count() == 0:
            self.mode = GameMode.VICTORY
            if self.ai_player is not None:
                self.ai_player.learn(
                    ai_reward,
                    self.maze,
                    (self.pacman.col, self.pacman.row),
                    [(ghost.col, ghost.row) for ghost in self.ghosts],
                    terminal=True,
                )
            return

        # 4. Update ghosts and check collisions
        pacman_rect = self.pacman.get_rect()
        for ghost in self.ghosts:
            ghost.update(
                self.maze,
                self.pacman,
                self.lives,
                self.power_ticks_remaining / POWER_PELLET_DURATION,
                self.difficulty_multiplier,
            )

            # Check collision between Pac-Man and Ghost
            if (
                self.respawn_invulnerability_ticks == 0
                and pacman_rect.colliderect(ghost.get_rect())
            ):
                if self.power_ticks_remaining > 0:
                    self.score += GHOST_POINTS
                    ai_reward += AI_REWARD_GHOST_EATEN
                    ghost.reset_position()
                else:
                    self._handle_player_hit()
                    life_lost_this_frame = True
                    ai_reward -= AI_PENALTY_LIFE_LOST
                    break

        if pellet_earned == 0 and self.power_ticks_remaining > 0:
            self.power_ticks_remaining -= 1
        if invulnerability_was_active:
            self.respawn_invulnerability_ticks -= 1
        if self.ai_player is not None:
            self.ai_player.learn(
                ai_reward,
                self.maze,
                (self.pacman.col, self.pacman.row),
                [(ghost.col, ghost.row) for ghost in self.ghosts],
                terminal=life_lost_this_frame or self.mode != GameMode.PLAYING,
            )

    def _choose_ai_direction(self) -> None:
        """Make one learned, risk-aware movement choice per tile."""
        if self.ai_player is None:
            return
        tile = (self.pacman.col, self.pacman.row)
        if self.ai_player.last_decision_tile == tile:
            return
        center_x = (self.pacman.col + 0.5) * TILE_SIZE
        center_y = (self.pacman.row + 0.5) * TILE_SIZE
        if (
            abs(self.pacman.x - center_x) > self.pacman.speed * 1.5
            or abs(self.pacman.y - center_y) > self.pacman.speed * 1.5
        ):
            return
        action = self.ai_player.choose_action(
            self.maze,
            tile,
            self.ghosts,
            power_active=self.power_ticks_remaining > 0,
            current_direction=self.pacman.current_dir,
        )
        if action != (0, 0):
            self.pacman.set_next_direction(action)
        self.ai_player.last_decision_tile = tile

    def save_ai(self) -> None:
        """Persist Q-values when autonomous mode is enabled."""
        if self.ai_player is not None:
            self.ai_player.save()

    def _handle_player_hit(self) -> None:
        """Handles Pac-Man losing a life or triggering Game Over."""
        self.lives -= 1
        self._difficulty_lives_lost += 1
        self.difficulty_multiplier = max(
            DIFFICULTY_MIN,
            self.difficulty_multiplier - DIFFICULTY_STEP,
        )
        self.power_ticks_remaining = 0
        if self.lives <= 0:
            self.mode = GameMode.GAME_OVER
        else:
            if self.ai_player is not None:
                self.ai_player.last_decision_tile = None
            self.reset_positions()
            self.death_pause_ticks = RESPAWN_PAUSE_TICKS
            self.respawn_invulnerability_ticks = RESPAWN_INVULNERABILITY_TICKS
