# AI Pac-Man: The Adaptive Maze Challenge

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Pygame](https://img.shields.io/badge/pygame-2.6.1-green.svg)](https://www.pygame.org/)
[![Testing](https://img.shields.io/badge/tests-pytest-yellow.svg)](https://docs.pytest.org/)
[![Course](https://img.shields.io/badge/course-AISC-purple.svg)](#academic-demonstrability)

An undergraduate **Artificial Intelligence and Soft Computing (AISC)** course project upgrading classic arcade Pac-Man with **Minimax with Alpha-Beta Pruning ($\alpha$-$\beta$ search)** for both ghost adversarial planning and autonomous Pac-Man decision-making.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [AI Algorithm: Minimax with Alpha-Beta Pruning](#ai-algorithm-minimax-with-alpha-beta-pruning)
4. [Progressive Level Design](#progressive-level-design)
5. [Project Architecture](#project-architecture)
6. [Prerequisites & Installation](#prerequisites--installation)
7. [Running the Game](#running-the-game)
8. [Controls & Gameplay](#controls--gameplay)
9. [Automated Testing](#automated-testing)
10. [Academic Demonstrability](#academic-demonstrability)

---

## 1. Project Overview

Traditional Pac-Man relies on simple deterministic tile-targeting rules. **AI Pac-Man: The Adaptive Maze Challenge** transforms the environment into an adversarial multi-agent system powered by **Minimax with Alpha-Beta Pruning**.

The game is designed with a strict separation of concerns:
- **Game Engine**: Pure Python & Pygame with procedural vector graphics (runs standalone without external image or sound assets).
- **Physics & Grid Navigation**: Sub-pixel floating point positioning with perpendicular corner snapping and direction buffering.
- **AI Core**: Independent, unit-testable modules for Ghost and Pac-Man decision-making using $\alpha$-$\beta$ pruned adversarial search.

---

## 2. Key Features

- **Procedural Retro Arcade Aesthetics**: Full vector rendering of classic maze walls, animated Pac-Man chomping, skirted ghosts with directional pupils, pulsing power pellets, and retro HUD overlays.
- **Adversarial Ghost AI ($\alpha$-$\beta$ Pruned Minimax)**: Each ghost has its own Minimax planner with Alpha-Beta Pruning to simulate legal responses while respecting power-pellet vulnerability.
- **Autonomous Pac-Man**: Run with `--ai` to let Pac-Man navigate using Minimax with Alpha-Beta Pruning, balancing survival, escape routes, power pellets, and collectible clearing.
- **High Search Efficiency**: Alpha-Beta pruning drastically reduces explored game tree nodes from $\mathcal{O}(b^d)$ towards $\mathcal{O}(b^{d/2})$, allowing responsive lookahead without frame lag.
- **Collision & Movement System**: Grid-based spatial checks preventing wall penetration while allowing seamless 180° reversals and smooth corner turns.
- **Adaptive Difficulty**: A bounded, smoothed performance controller gradually adjusts ghost speed; the current tier is shown in the HUD.
- **Multi-Modal Game State**: Robust state transitions (`MENU`, `PLAYING`, `PAUSED`, `LEVEL_TRANSITION`, `GAME_OVER`, `VICTORY`).

---

## 3. AI Algorithm: Minimax with Alpha-Beta Pruning

The core intelligence driving agent behavior is **Minimax Search with Alpha-Beta ($\alpha$-$\beta$) Pruning**.

### A. Minimax Search Formulation
- **Zero-Sum Adversarial Tree**:
  - In Ghost Search: The Ghost is the **MAX** player seeking capture; Pac-Man is the **MIN** player seeking evasion.
  - In Autonomous Pac-Man Search: Pac-Man is the **MAX** player optimizing survival and dots; active ghosts are **MIN** players.
- **Alternating Plies**: The simulation recursively explores legal cardinal moves on the maze grid up to a configured depth limit.

### B. Alpha-Beta ($\alpha$-$\beta$) Pruning
Alpha-Beta pruning tracks two bounds during tree recursion:
- $\alpha$: The minimum score that the maximizing player is assured of (highest value seen so far on MAX nodes).
- $\beta$: The maximum score that the minimizing player is assured of (lowest value seen so far on MIN nodes).
- **Cutoff Condition**: Whenever $\beta \le \alpha$, the current branch is pruned because the opponent would never allow this state to be reached. This eliminates useless branches while preserving exact optimal decisions.

### C. Heuristic Evaluation Functions
Leaf nodes are evaluated through comprehensive multi-factor heuristics:
- **Capture & Survival**: Large terminal rewards/penalties for captures, game over, or clearing the level.
- **Distance Metrics**: Manhattan distance between agents, nearest dot distance, and nearest power pellet.
- **Spatial Control**: Dead-end penalties and available escape exits.
- **Ghost Separation**: Evaluates distances between ghosts to avoid clumping without sacrificing pursuit.

---

## 4. Progressive Level Design

| Level | Name | Theme & Challenge |
|:---:|---|---|
| **Level 1** | **Learning the Maze** | Original expanded maze; collect all dots and power pellets while avoiding four independently positioned ghosts. |
| **Level 2** | **Maze Challenge** | A different 25×25 layout with staggered barriers, narrower passages, four power pellets, and four spread-out ghost spawns. |

After the final Level 1 collectible is collected, the game enters a brief transition pause, then loads Level 2 while preserving score and lives.

---

## 5. Project Architecture

```
ai-pacman/
├── main.py                 # Pygame entry point & event dispatch loop
├── settings.py             # Constants, speeds, dimensions, color palettes
├── maze.py                 # Grid representation, wall checks, dots & pellets
├── pacman.py               # Player entity, corner snapping, mouth animation
├── ghost.py                # Ghost entities, movement timing, collision bounds
├── ghost_minimax.py        # Ghost move selection using Minimax with Alpha-Beta Pruning
├── pacman_ai.py            # Autonomous Pac-Man using Minimax with Alpha-Beta Pruning
├── game_state.py           # Game loop logic, scoring, lives, state machine
├── renderer.py             # Geometric arcade renderer, HUD, modal overlays
├── level_manager.py        # Level 1/2 layouts and maze construction
├── pytest.ini              # Pytest configuration
├── requirements.txt        # Python dependency specifications
└── tests/                  # Automated pytest test suites
    ├── test_game_state.py
    ├── test_ghost_logic.py
    ├── test_ghost_minimax.py
    └── test_pacman_ai.py
```

---

## 6. Prerequisites & Installation

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

To play manually:
```powershell
python main.py
```

To run autonomous Pac-Man using Minimax with Alpha-Beta Pruning:
```powershell
python main.py --ai
```

Optional flags:
- `--minimax-depth N`: Set Pac-Man's lookahead depth in plies (default: 6).
- `--ghost-minimax-depth N`: Set ghosts' lookahead depth in plies (default: 4).
- `--ai-debug`: Display real-time candidate scores, nodes visited, and pruned branches.
- `--seed N`: Set a deterministic random seed for reproducible gameplay.
- `--headless --frames N`: Run headless simulation for automated benchmarks without opening an OS window.

---

## 8. Controls & Gameplay

| Key | Action |
|---|---|
| **Arrow Keys** / **W, A, S, D** | Steer Pac-Man (buffered turns) |
| **P** / **Spacebar** | Pause / Resume game |
| **R** | Restart game |
| **ESC** | Exit application |

---

## 9. Automated Testing

Run all unit tests using `pytest`:
```powershell
pytest
```
To run with verbose output:
```powershell
pytest -v
```

---

## License

Developed for educational purposes under the Artificial Intelligence and Soft Computing (AISC) course curriculum.
