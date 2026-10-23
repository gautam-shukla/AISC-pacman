"""
main.py - Entry point for AI Pac-Man: The Adaptive Maze Challenge.
"""
import sys
import argparse
import pygame
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    Direction,
    MINIMAX_SEARCH_DEPTH,
    GHOST_MINIMAX_SEARCH_DEPTH,
)
from game_state import GameState
from renderer import Renderer


def main():
    parser = argparse.ArgumentParser(description="AI Pac-Man: The Adaptive Maze Challenge")
    parser.add_argument("--headless", action="store_true", help="Run without opening an OS window")
    parser.add_argument("--frames", type=int, default=0, help="Exit after N frames (useful for smoke tests)")
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Use autonomous Minimax Pac-Man",
    )
    parser.add_argument(
        "--minimax-depth",
        type=int,
        default=MINIMAX_SEARCH_DEPTH,
        help="Pac-Man Minimax lookahead depth in plies (default: %(default)s)",
    )
    parser.add_argument(
        "--ghost-minimax-depth",
        type=int,
        default=GHOST_MINIMAX_SEARCH_DEPTH,
        help="Ghost Minimax lookahead depth in plies (default: %(default)s)",
    )
    parser.add_argument(
        "--ai-debug",
        action="store_true",
        help="Print Minimax candidate scores, node count, and chosen move",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed AI tie-breaking for reproducible gameplay",
    )
    args = parser.parse_args()
    if args.minimax_depth < 1:
        parser.error("--minimax-depth must be at least 1")
    if args.ghost_minimax_depth < 1:
        parser.error("--ghost-minimax-depth must be at least 1")

    # Initialize Pygame
    pygame.init()
    pygame.display.set_caption("AI Pac-Man: The Adaptive Maze Challenge")

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    game_state = GameState(
        ai_enabled=args.ai,
        minimax_depth=args.minimax_depth,
        ai_debug=args.ai_debug,
        ghost_minimax_depth=args.ghost_minimax_depth,
        random_seed=args.seed,
    )
    renderer = Renderer(screen)

    running = True
    frame_count = 0

    while running:
        frame_count += 1
        if args.frames > 0 and frame_count >= args.frames:
            break

        # Event processing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_p, pygame.K_SPACE):
                    game_state.toggle_pause()
                elif event.key == pygame.K_r:
                    game_state.restart_game()
                # Direction controls (Arrow keys + WASD) are reserved for manual play.
                elif not game_state.ai_enabled and event.key in (pygame.K_UP, pygame.K_w):
                    game_state.pacman.set_next_direction(Direction.UP)
                elif not game_state.ai_enabled and event.key in (pygame.K_DOWN, pygame.K_s):
                    game_state.pacman.set_next_direction(Direction.DOWN)
                elif not game_state.ai_enabled and event.key in (pygame.K_LEFT, pygame.K_a):
                    game_state.pacman.set_next_direction(Direction.LEFT)
                elif not game_state.ai_enabled and event.key in (pygame.K_RIGHT, pygame.K_d):
                    game_state.pacman.set_next_direction(Direction.RIGHT)

        # Update simulation logic
        game_state.update()

        # Render display
        renderer.render(game_state)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
