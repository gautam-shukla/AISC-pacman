# AI Pac-Man: The Adaptive Maze Challenge

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Pygame](https://img.shields.io/badge/pygame-2.6.1-green.svg)](https://www.pygame.org/)
[![Testing](https://img.shields.io/badge/tests-pytest-yellow.svg)](https://docs.pytest.org/)
[![Course](https://img.shields.io/badge/course-AISC-purple.svg)](#academic-demonstrability)

An undergraduate **Artificial Intelligence and Soft Computing (AISC)** course project that upgrades the classic arcade Pac-Man with:
- **Graph Search & Pathfinding**: Breadth-First Search (BFS) and $A^*$ utilities, separate from ghost move selection.
- **Adversarial Search**: Plain Minimax controls ghost moves against Pac-Man's responses.
- **Puzzle Mechanics**: Locked passages, keys, switches, power pellets, and progressive mazes.
- **Empirical Benchmarking**: Automated headless experimental pipeline comparing search algorithms and behavioral models.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [AI Components](#ai-components)
4. [Progressive Level Design](#progressive-level-design)
5. [Project Architecture](#project-architecture)
6. [Prerequisites & Installation](#prerequisites--installation)
7. [Running the Game](#running-the-game)
8. [Controls & Gameplay](#controls--gameplay)
9. [Automated Testing](#automated-testing)
10. [Academic Demonstrability](#academic-demonstrability)

---

## 1. Project Overview

Traditional Pac-Man relies on simple deterministic tile-targeting rules. **AI Pac-Man: The Adaptive Maze Challenge** transforms the environment into an adaptive multi-agent system. Ghost agents use plain Minimax to reason about legal Pac-Man responses while respecting power-pellet vulnerability.

The game is designed with a strict separation of concerns:
- **Game Engine**: Pure Python & Pygame with procedural vector graphics (runs standalone without external image or sound assets).
- **Physics & Grid Navigation**: Sub-pixel floating point positioning with perpendicular corner snapping and direction buffering.
- **AI Core**: Independent, unit-testable modules for ghost Minimax and Pac-Man decision-making.

---

## 2. Key Features

- **Procedural Retro Arcade Aesthetics**: Full vector rendering of classic maze walls, animated Pac-Man chomping, skirted ghosts with directional pupils, pulsing power pellets, and retro HUD overlays.
- **Collision & Movement System**: Grid-based spatial checks preventing wall penetration while allowing seamless 180° reversals and smooth corner turns.
- **Adaptive Difficulty**: A bounded, smoothed performance controller gradually adjusts ghost speed; the current tier is shown in the HUD.
- **Expanded Maze**: The 21×21 base maze is surrounded by a connected collectible corridor, producing a 25×25 playable grid sized to fit the display.
- **Safe Respawning**: Losing a life preserves score and maze progress, resets entity positions, and provides a pause plus brief collision immunity.
- **Minimax Ghost AI**: Ghosts use plain Minimax against Pac-Man's possible tile moves. Search depth is configurable with `--ghost-minimax-depth` (default: 4 plies); other ghosts remain stationary in an individual ghost's search, matching the game's sequential ghost updates. Power pellets reverse the ghost's evaluation so vulnerable ghosts avoid Pac-Man.
- **Independent Ghost Spacing**: Ghosts retain separate Minimax planners and positions; their evaluation discourages clustering without forcing a different move when it would be illegal or tactically worse.
- **Autonomous Pac-Man**: `--ai` uses plain Minimax to balance survival, escape options, power pellets, and clearing the remaining collectibles.
- **Automatic Level Progression**: Clearing Level 1 pauses play for a brief completion message, then loads a distinct Level 2 while preserving score and lives.
- **Configurable Maze Environments**: JSON-based level configurations supporting dynamic obstacles, keys, switches, and ghost gates.
- **Multi-Modal Game State**: Robust state transitions (`MENU`, `PLAYING`, `PAUSED`, `GAME_OVER`, `VICTORY`).

---

## 3. AI Components

### A. Graph Search Algorithms
1. **Breadth-First Search (BFS)**:
   - Computes the unweighted shortest path on the 4-connected grid.
   - Serves as the rigorous benchmark baseline for expanded node counts and search runtime.
2. **$A^*$ Search Algorithm**:
   - Uses evaluation function $f(n) = g(n) + h(n)$.
   - Admissible Manhattan distance heuristic:
     $$h(n) = |x_n - x_{\text{goal}}| + |y_n - y_{\text{goal}}|$$
   - Optimally finds shortest paths while drastically reducing expanded nodes in open corridors.

### B. Minimax Ghost Controller
Ghost movement is selected by `GhostMinimaxPlanner` in `ghost_minimax.py`. Each ghost is the MAX player and tries to catch Pac-Man; Pac-Man is the MIN player and chooses the response that avoids capture. Search simulates legal cardinal moves on the existing maze, alternates one ghost move with one Pac-Man move, and evaluates the resulting state using Manhattan distance, capture/lives, dead-end, Pac-Man escape options, and terminal collectible completion. Search uses plain Minimax without alpha-beta pruning or pathfinding.

Decisions are recalculated at tile centers, preserving the existing movement timing. Reversals are avoided when another legal move exists, while frightened ghosts can reverse to escape. When multiple ghosts exist, only the active ghost moves in the search; the other ghosts' current tile positions are held fixed, in keeping with the game's sequential update loop.

Ghost colors and ghost-type assignments remain unchanged, but role-specific A* targeting and patrol routing no longer select ghost moves.

### C. Autonomous Pac-Man Minimax
When `--ai` is enabled, Pac-Man is MAX and active ghosts are MIN. The search simulates Pac-Man actions followed by each ghost's legal move in the same sequential order as the game update; frightened ghosts instead flee as in the live game. It uses plain Minimax without pruning, A*, BFS, or reinforcement learning. The default depth is six plies and can be changed with `--minimax-depth`.

The immutable search state tracks Pac-Man and ghost positions, remaining dots and power pellets, vulnerability, lives, and recent Pac-Man tiles. The evaluation assigns terminal priority to level completion and capture, then scores collectible progress, distance to remaining collectibles, ghost danger, escape options, dead ends, and repeated positions. Immediate root moves also account for pixel-level collisions that can occur before the next tile-center decision. Only the selected legal action is applied to the live game.

---

## 4. Progressive Level Design

| Level | Name | Theme & Challenge |
|:---:|---|---|
| **Level 1** | **Learning the Maze** | Original expanded maze; collect all dots and power pellets while avoiding four independently positioned ghosts. |
| **Level 2** | **Maze Challenge** | A different 25×25 layout with staggered barriers, narrower passages, four power pellets, and four spread-out ghost spawns. |

After the final Level 1 collectible is collected, the game freezes movement and collisions during a two-second “LEVEL COMPLETE!” overlay, then loads Level 2. Score and remaining lives carry over; level-specific entities, power state, and Pac-Man decision history reset. Clearing Level 2 ends the game in VICTORY.

---

## 5. Project Architecture

```
ai-pacman/
├── main.py                 # Pygame entry point & event dispatch loop
├── settings.py             # Constants, speeds, dimensions, color palettes
├── maze.py                 # Grid representation, wall checks, dots & pellets
├── pacman.py               # Player entity, corner snapping, mouth animation
├── ghost.py                # Ghost entities, movement timing, collision bounds
├── ghost_minimax.py        # Plain Minimax ghost move selection
├── game_state.py           # Game loop logic, scoring, lives, state machine
├── renderer.py             # Geometric arcade renderer, HUD, modal overlays
├── pathfinding.py          # BFS and A* utilities (not used by ghost movement)
├── level_manager.py        # Level 1/2 layouts and maze construction
├── pytest.ini              # Pytest configuration
├── requirements.txt        # Python dependency specifications
├── README.md               # Project documentation
├── levels/                 # Level layout configurations
│   ├── level1.json
│   ├── level2.json
│   ├── level3.json
│   └── level4.json
├── tests/                  # Automated pytest test suites
│   ├── test_game_state.py
│   ├── test_ghost_minimax.py
│   ├── test_pathfinding.py
├── experiments/            # AISC experimental evaluation suite
│   ├── run_experiments.py
│   ├── analyze_results.py
│   └── results.csv
└── docs/                   # Architectural & theoretical documentation
    ├── architecture.md
    └── algorithms.md
```

---

## 6. Prerequisites & Installation

### Prerequisites
- **Python 3.12** is required (provides confirmed prebuilt binary wheels for Pygame and numerical libraries on Windows, macOS, and Linux).

### 1. Clone the Repository
```powershell
git clone https://github.com/<your-username>/<your-repo-name>.git
cd ai-pacman
```

### 2. Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 7. Running the Game

To launch the desktop game:
```powershell
python main.py
```

To run autonomous Pac-Man:
```powershell
python main.py --ai
```
Use `--minimax-depth N` to configure Pac-Man's Minimax search and `--ai-debug` to print candidate scores, visited node count, and the selected move.

Configure the ghost search depth independently:
```powershell
python main.py --ghost-minimax-depth 4
```
The depth is measured in plies (one ghost or Pac-Man move per ply), and must be at least 1. The default is 4. Manual play remains the default; use the arrow keys or WASD to steer Pac-Man.

### Command-Line Arguments
- Run headless smoke tests:
  ```powershell
  python main.py --headless --frames 120
  ```

---

## 8. Controls & Gameplay

| Key | Action |
|---|---|
| **Arrow Keys** / **W, A, S, D** | Steer Pac-Man (buffered turns) |
| **P** / **Spacebar** | Pause / Resume game |
| **R** | Restart game |
| **ESC** | Exit application |

### Objective & Scoring
- **Dots**: $+10\text{ pts}$
- **Power Pellets**: $+50\text{ pts}$ (temporarily weakens ghosts)
- **Ghost Elimination**: $+200\text{ pts}$
- **Lives**: You start with $3$ lives. Colliding with an active ghost costs $1$ life.

---

## 9. Automated Testing

The project uses `pytest` for automated unit and regression testing.

Run all tests:
```powershell
pytest tests
```

To run with verbose output:
```powershell
pytest -v
```

---

## 10. Academic Demonstrability

This project is tailored for undergraduate AISC evaluation:
1. **Theoretical Clarity**: Every algorithm is implemented cleanly with clear time and space complexity considerations.
2. **Empirical Benchmarks**: Built-in experiment scripts measure:
   - Node expansions: BFS vs. $A^*$.
   - Search execution runtime in milliseconds across identical maze configurations.
   - Survival times and level completion rates under Minimax-controlled ghost movement.
3. **Reproducibility**: Experiments run headlessly with deterministic seeds, producing clean CSV output and publication-quality Matplotlib comparison plots.

---

## License

Developed for educational purposes under the Artificial Intelligence and Soft Computing (AISC) course curriculum.
