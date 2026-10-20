"""
settings.py - Global constants, configurations, and color definitions.
"""
from enum import Enum, auto


class GameMode(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class Direction:
    NONE = (0, 0)
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    OPPOSITES = {
        (0, -1): (0, 1),
        (0, 1): (0, -1),
        (-1, 0): (1, 0),
        (1, 0): (-1, 0),
        (0, 0): (0, 0),
    }


# Tile dimensions and grid
TILE_SIZE = 32
GRID_COLS = 21
GRID_ROWS = 21
HUD_HEIGHT = 64

SCREEN_WIDTH = GRID_COLS * TILE_SIZE
SCREEN_HEIGHT = (GRID_ROWS * TILE_SIZE) + HUD_HEIGHT
FPS = 60

# Speeds (pixels per frame at 60 FPS)
# 4.0 pixels/frame allows cleanly dividing 32px tiles
PACMAN_SPEED = 4.0
GHOST_SPEED = 3.0

# Gameplay rules
INITIAL_LIVES = 3
DOT_POINTS = 10
POWER_PELLET_POINTS = 50
GHOST_POINTS = 200

# Color palette (Arcade style)
COLOR_BG = (10, 10, 18)
COLOR_WALL = (33, 40, 210)
COLOR_WALL_OUTLINE = (80, 95, 255)
COLOR_WALL_INNER = (15, 18, 90)
COLOR_DOT = (255, 190, 180)
COLOR_POWER_PELLET = (255, 220, 100)
COLOR_PACMAN = (255, 220, 0)
COLOR_TEXT = (245, 245, 250)
COLOR_TEXT_DIM = (160, 160, 180)
COLOR_HUD_BG = (18, 18, 28)
COLOR_LIVES = (255, 210, 0)

# Ghost colors
COLOR_GHOST_RED = (255, 0, 0)      # Blinky / Hunter
COLOR_GHOST_PINK = (255, 140, 190) # Pinky / Ambusher
COLOR_GHOST_CYAN = (0, 220, 220)   # Inky / Patrol
COLOR_GHOST_ORANGE = (255, 165, 0) # Clyde / Guard
COLOR_GHOST_FLEE = (50, 70, 240)
COLOR_GHOST_EYES = (255, 255, 255)
COLOR_GHOST_PUPIL = (30, 40, 180)

# Default baseline 21x21 maze layout
# Legend:
# '#' = Wall
# '.' = Dot
# 'o' = Power Pellet
# ' ' = Empty space
# 'P' = Pac-Man Spawn
# 'G' = Ghost Spawn
# '=' = Ghost gate / barrier (walkable by ghost, solid to pacman initially)
DEFAULT_MAZE = [
    "#####################",
    "#.........#.........#",
    "#.###.###.#.###.###.#",
    "#o###.###.#.###.###o#",
    "#.###.###.#.###.###.#",
    "#...................#",
    "#.###.#.#####.#.###.#",
    "#.###.#.#####.#.###.#",
    "#.....#...#...#.....#",
    "#####.### # ###.#####",
    "    #.#   G   #.#    ",
    "#####.# ##### #.#####",
    "#.........#.........#",
    "#.###.###.#.###.###.#",
    "#o..#.....P.....#..o#",
    "###.#.#.#####.#.#.###",
    "#.....#...#...#.....#",
    "#.#######.#.#######.#",
    "#...................#",
    "#.#################.#",
    "#####################",
]
