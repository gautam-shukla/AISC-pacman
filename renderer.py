"""
renderer.py - Retro geometric arcade rendering for maze, Pac-Man, ghosts, and HUD.
"""
import math
from typing import Tuple
import pygame
from settings import (
    TILE_SIZE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    HUD_HEIGHT,
    COLOR_BG,
    COLOR_WALL,
    COLOR_WALL_OUTLINE,
    COLOR_WALL_INNER,
    COLOR_DOT,
    COLOR_POWER_PELLET,
    COLOR_PACMAN,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_HUD_BG,
    COLOR_GHOST_EYES,
    COLOR_GHOST_PUPIL,
    GameMode,
    Direction,
)
from game_state import GameState
from pacman import Pacman
from ghost import Ghost


class Renderer:
    """Renders game elements geometrically without requiring external sprite sheets."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        # Initialize default fonts
        pygame.font.init()
        self.font_title = pygame.font.SysFont("arial", 28, bold=True)
        self.font_hud = pygame.font.SysFont("arial", 18, bold=True)
        self.font_overlay = pygame.font.SysFont("arial", 32, bold=True)
        self.font_sub = pygame.font.SysFont("arial", 16)

        # Pre-create translucent overlay surface for pause/gameover/victory modals
        self.overlay_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Pulse timer for power pellets
        self.tick_counter = 0

    def render(self, state: GameState) -> None:
        """Renders the entire game frame: HUD, Maze, Pac-Man, Ghosts, and Overlays."""
        self.tick_counter += 1
        self.screen.fill(COLOR_BG)

        # 1. Render HUD bar at the top
        self._render_hud(state)

        # 2. Offset maze below the HUD
        maze_surface = self.screen.subsurface(pygame.Rect(0, HUD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - HUD_HEIGHT))

        # Render walls, dots, pellets
        self._render_maze(maze_surface, state)

        # Render entities
        self._render_pacman(maze_surface, state.pacman)
        for ghost in state.ghosts:
            self._render_ghost(maze_surface, ghost)

        # 3. Render state overlays (Paused, Game Over, Victory)
        if state.mode in (GameMode.PAUSED, GameMode.GAME_OVER, GameMode.VICTORY):
            self._render_overlay(state)

    def _render_hud(self, state: GameState) -> None:
        """Renders the top arcade status bar."""
        hud_rect = pygame.Rect(0, 0, SCREEN_WIDTH, HUD_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_HUD_BG, hud_rect)
        pygame.draw.line(self.screen, COLOR_WALL_OUTLINE, (0, HUD_HEIGHT - 2), (SCREEN_WIDTH, HUD_HEIGHT - 2), 2)

        # Score
        score_label = self.font_hud.render(f"SCORE: {state.score:05d}", True, COLOR_TEXT)
        self.screen.blit(score_label, (20, 12))

        # Level
        level_label = self.font_hud.render(f"LEVEL {state.level}", True, COLOR_TEXT_DIM)
        self.screen.blit(level_label, (SCREEN_WIDTH // 2 - level_label.get_width() // 2, 12))

        # Remaining dots / progress
        dots_left = state.maze.remaining_dots_count()
        total_dots = state.maze.total_dots_count()
        progress_text = self.font_sub.render(f"DOTS: {dots_left}/{total_dots}", True, COLOR_TEXT_DIM)
        self.screen.blit(progress_text, (SCREEN_WIDTH // 2 - progress_text.get_width() // 2, 36))

        # Lives icon representation
        lives_label = self.font_hud.render("LIVES:", True, COLOR_TEXT)
        self.screen.blit(lives_label, (SCREEN_WIDTH - 170, 12))

        for i in range(max(0, state.lives)):
            icon_x = SCREEN_WIDTH - 90 + (i * 26)
            icon_y = 22
            pygame.draw.circle(self.screen, COLOR_PACMAN, (icon_x, icon_y), 9)
            # Cute small mouth wedge
            wedge = [
                (icon_x, icon_y),
                (icon_x + 9, icon_y - 5),
                (icon_x + 9, icon_y + 5),
            ]
            pygame.draw.polygon(self.screen, COLOR_HUD_BG, wedge)

    def _render_maze(self, surface: pygame.Surface, state: GameState) -> None:
        """Renders walls and collectible dots on the maze subsurface."""
        maze = state.maze

        # Render walls
        for col, row in maze.walls:
            rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            # Outer wall border
            pygame.draw.rect(surface, COLOR_WALL_OUTLINE, rect)
            # Inner fill
            inner_rect = rect.inflate(-4, -4)
            pygame.draw.rect(surface, COLOR_WALL, inner_rect)
            # Center subtle block
            center_rect = rect.inflate(-10, -10)
            pygame.draw.rect(surface, COLOR_WALL_INNER, center_rect)

        # Render standard dots
        for col, row in maze.dots:
            center = (int((col + 0.5) * TILE_SIZE), int((row + 0.5) * TILE_SIZE))
            pygame.draw.circle(surface, COLOR_DOT, center, 3)

        # Render power pellets (pulsing radius)
        pulse = abs(math.sin(self.tick_counter * 0.1)) * 2.5
        pellet_radius = int(6 + pulse)
        for col, row in maze.power_pellets:
            center = (int((col + 0.5) * TILE_SIZE), int((row + 0.5) * TILE_SIZE))
            pygame.draw.circle(surface, COLOR_POWER_PELLET, center, pellet_radius)
            pygame.draw.circle(surface, (255, 255, 255), center, max(2, pellet_radius - 3))

    def _render_pacman(self, surface: pygame.Surface, pacman: Pacman) -> None:
        """Renders Pac-Man with animated mouth wedge oriented in movement direction."""
        cx, cy = int(pacman.x), int(pacman.y)
        r = pacman.radius

        # Draw base yellow circle
        pygame.draw.circle(surface, COLOR_PACMAN, (cx, cy), r)

        # Carve out mouth using polygon slice if angle > 2 degrees
        if pacman.mouth_angle > 2.0:
            facing_deg = pacman.get_facing_angle()
            mouth_half = pacman.mouth_angle

            # Invert Y for Pygame coordinate space
            angle1 = math.radians(facing_deg - mouth_half)
            angle2 = math.radians(facing_deg + mouth_half)

            p1 = (cx, cy)
            p2 = (cx + int((r + 4) * math.cos(angle1)), cy - int((r + 4) * math.sin(angle1)))
            p3 = (cx + int((r + 4) * math.cos(angle2)), cy - int((r + 4) * math.sin(angle2)))

            pygame.draw.polygon(surface, COLOR_BG, [p1, p2, p3])

    def _render_ghost(self, surface: pygame.Surface, ghost: Ghost) -> None:
        """Renders a classic arcade ghost with rounded head, skirt, and directional eyes."""
        cx, cy = int(ghost.x), int(ghost.y)
        r = ghost.radius

        # 1. Rounded head (upper semicircle)
        head_center = (cx, cy - int(r * 0.1))
        pygame.draw.circle(surface, ghost.color, head_center, r)

        # 2. Main body torso
        torso_rect = pygame.Rect(cx - r, cy - int(r * 0.1), r * 2, int(r * 1.0))
        pygame.draw.rect(surface, ghost.color, torso_rect)

        # 3. Wavy skirt at the bottom (3 small tentacle bumps)
        skirt_y = cy + int(r * 0.9)
        skirt_width = (r * 2) / 3.0
        for i in range(3):
            tentacle_cx = int((cx - r) + (i + 0.5) * skirt_width)
            pygame.draw.circle(surface, ghost.color, (tentacle_cx, skirt_y), int(skirt_width / 2.0))

        # 4. Eyes (white sclera)
        eye_offset_x = int(r * 0.35)
        eye_offset_y = int(r * 0.2)
        eye_r = int(r * 0.32)

        left_eye_center = (cx - eye_offset_x, cy - eye_offset_y)
        right_eye_center = (cx + eye_offset_x, cy - eye_offset_y)

        pygame.draw.circle(surface, COLOR_GHOST_EYES, left_eye_center, eye_r)
        pygame.draw.circle(surface, COLOR_GHOST_EYES, right_eye_center, eye_r)

        # 5. Pupils pointing in ghost's current direction
        dx, dy = ghost.current_dir
        pupil_dx = dx * int(eye_r * 0.45)
        pupil_dy = dy * int(eye_r * 0.45)
        pupil_r = max(2, int(eye_r * 0.5))

        pygame.draw.circle(surface, COLOR_GHOST_PUPIL, (left_eye_center[0] + pupil_dx, left_eye_center[1] + pupil_dy), pupil_r)
        pygame.draw.circle(surface, COLOR_GHOST_PUPIL, (right_eye_center[0] + pupil_dx, right_eye_center[1] + pupil_dy), pupil_r)

    def _render_overlay(self, state: GameState) -> None:
        """Renders modal dialogs for Paused, Game Over, and Victory states."""
        self.overlay_surface.fill((0, 0, 0, 180))
        self.screen.blit(self.overlay_surface, (0, 0))

        box_width = 460
        box_height = 200
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2
        modal_rect = pygame.Rect(box_x, box_y, box_width, box_height)

        pygame.draw.rect(self.screen, (24, 26, 42), modal_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_WALL_OUTLINE, modal_rect, width=3, border_radius=12)

        if state.mode == GameMode.PAUSED:
            title = self.font_overlay.render("GAME PAUSED", True, (255, 230, 80))
            sub1 = self.font_hud.render("Press [P] or [SPACE] to Resume", True, COLOR_TEXT)
            sub2 = self.font_sub.render("Press [R] to Restart", True, COLOR_TEXT_DIM)
        elif state.mode == GameMode.GAME_OVER:
            title = self.font_overlay.render("GAME OVER", True, (255, 70, 70))
            sub1 = self.font_hud.render(f"Final Score: {state.score}", True, COLOR_TEXT)
            sub2 = self.font_sub.render("Press [R] to Play Again", True, COLOR_TEXT_DIM)
        elif state.mode == GameMode.VICTORY:
            title = self.font_overlay.render("LEVEL CLEARED!", True, (80, 255, 120))
            sub1 = self.font_hud.render(f"Magnificent! Score: {state.score}", True, COLOR_TEXT)
            sub2 = self.font_sub.render("Press [R] to Restart Maze", True, COLOR_TEXT_DIM)
        else:
            return

        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, box_y + 35))
        self.screen.blit(sub1, (SCREEN_WIDTH // 2 - sub1.get_width() // 2, box_y + 95))
        self.screen.blit(sub2, (SCREEN_WIDTH // 2 - sub2.get_width() // 2, box_y + 135))
