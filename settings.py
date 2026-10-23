"""
settings.py - Global constants, configurations, and color definitions.
"""
from enum import Enum, auto
from typing import List


class GameMode(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    LEVEL_TRANSITION = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class GhostType(Enum):
    HUNTER = auto()
    AMBUSHER = auto()
    PATROL = auto()
    GUARD = auto()


class GhostState(Enum):
    CHASE = auto()
    PATROL = auto()
    FLEE = auto()
    SEARCH = auto()


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
HUD_HEIGHT = 64
FPS = 60

# Speeds (pixels per frame at 60 FPS)
# 4.0 pixels/frame allows cleanly dividing 32px tiles
PACMAN_SPEED = 3.5
GHOST_SPEED = 2.5
POWER_PELLET_DURATION = 60 * 8

# Dynamic difficulty and respawn tuning
DIFFICULTY_MIN = 0.75
DIFFICULTY_MAX = 1.35
DIFFICULTY_STEP = 0.04
DIFFICULTY_EVALUATION_FRAMES = FPS * 10
DIFFICULTY_EMA_ALPHA = 0.5
DIFFICULTY_EASY_THRESHOLD = 0.96
DIFFICULTY_HARD_THRESHOLD = 1.06
RESPAWN_PAUSE_TICKS = 30
RESPAWN_INVULNERABILITY_TICKS = FPS * 2
GHOST_PROXIMITY_RANGE_TILES = 8
GHOST_PROXIMITY_SPEED_BONUS = 0.2
GHOST_LOW_LIVES_SPEED_REDUCTION = 0.03
GHOST_MAX_LIVES_SPEED_REDUCTION = 0.06
GHOST_GUARD_CHASE_RANGE = 5
GHOST_SEARCH_RANGE = 7
MAZE_EXPANSION_MARGIN = 2

# Pac-Man Minimax evaluation and search configuration
MINIMAX_SEARCH_DEPTH = 6
MINIMAX_GHOST_COLLISION_PENALTY = 100000.0
MINIMAX_LIFE_LOSS_WEIGHT = 1000.0
MINIMAX_WIN_REWARD = 100000.0
MINIMAX_COLLECTIBLE_REWARD = 18.0
MINIMAX_REMAINING_COLLECTIBLE_WEIGHT = 12.0
MINIMAX_PELLET_DISTANCE_WEIGHT = 3.0
MINIMAX_GHOST_DANGER_RANGE = 5
MINIMAX_GHOST_RISK_WEIGHT = 20.0
MINIMAX_ESCAPE_OPTION_WEIGHT = 5.0
MINIMAX_DEAD_END_PENALTY = 30.0
MINIMAX_POWER_PELLET_REWARD = 40.0
MINIMAX_LOOP_PENALTY = 20.0
MINIMAX_TIE_TOLERANCE = 0.01
GHOST_MINIMAX_SEARCH_DEPTH = 4
GHOST_MINIMAX_DEAD_END_PENALTY = 8.0
GHOST_MINIMAX_ESCAPE_OPTION_WEIGHT = 1.5
GHOST_MINIMAX_CLUSTER_PENALTY = 6.0
GHOST_MINIMAX_SEPARATION_WEIGHT = 1.5
GHOST_MINIMAX_TIE_TOLERANCE = 0.01
LEVEL_TRANSITION_TICKS = FPS * 2

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

# Default baseline 21x21 maze layout, expanded with an outer collectible corridor.
# Legend:
# '#' = Wall
# '.' = Dot
# 'o' = Power Pellet
# ' ' = Empty space
# 'P' = Pac-Man Spawn
# 'G' = Ghost Spawn
# '=' = Ghost gate / barrier (walkable by ghost, solid to pacman initially)
_BASE_MAZE = [
    "#####################",
    "#G........#........G#",
    "#.###.###.#.###.###.#",
    "#o###.###.#.###.###o#",
    "#.###.###.#.###.###.#",
    "#...................#",
    "#.###.#.#####.#.###.#",
    "#.###.#.#####.#.###.#",
    "#.....#...#...#.....#",
    "#####.### # ###.#####",
    "    #.#       #.#    ",
    "#####.# ##### #.#####",
    "#.........#.........#",
    "#.###.###.#.###.###.#",
    "#o..#.....P.....#..o#",
    "###.#.#.#####.#.#.###",
    "#.....#...#...#.....#",
    "#.#######.#.#######.#",
    "#...................#",
    "#G#################G#",
    "#####################",
]


def _expand_maze(layout: List[str], margin: int) -> List[str]:
    """Add a connected, collectible perimeter corridor around the base maze."""
    rows = len(layout)
    cols = len(layout[0])
    expanded = [["#"] * (cols + margin * 2) for _ in range(rows + margin * 2)]

    for row, line in enumerate(layout):
        for col, tile in enumerate(line):
            expanded[row + margin][col + margin] = tile

    last_col = cols + margin - 1
    last_row = rows + margin - 1
    for col in range(margin - 1, last_col + 1):
        expanded[margin - 1][col] = "."
        expanded[last_row][col] = "."
    for row in range(margin - 1, last_row + 1):
        expanded[row][margin - 1] = "."
        expanded[row][last_col] = "."

    # Four doorways connect the new perimeter to the original maze.
    gates = (
        (margin + cols // 2, margin),
        (margin + cols // 2, margin + rows - 1),
        (margin, margin + rows // 2),
        (margin + cols - 1, margin + rows // 2),
    )
    for col, row in gates:
        expanded[row][col] = "."

    return ["".join(row) for row in expanded]


DEFAULT_MAZE = _expand_maze(_BASE_MAZE, margin=MAZE_EXPANSION_MARGIN)
GRID_COLS = len(DEFAULT_MAZE[0])
GRID_ROWS = len(DEFAULT_MAZE)
SCREEN_WIDTH = GRID_COLS * TILE_SIZE
SCREEN_HEIGHT = (GRID_ROWS * TILE_SIZE) + HUD_HEIGHT
