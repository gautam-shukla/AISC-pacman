# AI Pac-Man: The Adaptive Maze Challenge

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Pygame](https://img.shields.io/badge/pygame-2.6.1-green.svg)](https://www.pygame.org/)
[![Testing](https://img.shields.io/badge/tests-pytest-yellow.svg)](https://docs.pytest.org/)
[![Course](https://img.shields.io/badge/course-AISC-purple.svg)](#academic-demonstrability)

An undergraduate **Artificial Intelligence and Soft Computing (AISC)** course project that upgrades the classic arcade Pac-Man with:
- **Graph Search & Pathfinding**: Breadth-First Search (BFS) and $A^*$ algorithms.
- **Behavioral Modeling**: Finite-State Machines (FSMs) for distinct ghost archetypes.
- **Soft Computing**: Mamdani Fuzzy Inference System (FIS) for dynamic ghost aggression.
- **Puzzle Mechanics**: Locked passages, keys, switches, power pellets, and progressive mazes.
- **Empirical Benchmarking**: Automated headless experimental pipeline comparing search algorithms and behavioral models.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [AI & Soft Computing Components](#ai--soft-computing-components)
4. [Progressive Level Design](#progressive-level-design)
5. [Project Architecture](#project-architecture)
6. [Prerequisites & Installation](#prerequisites--installation)
7. [Running the Game](#running-the-game)
8. [Controls & Gameplay](#controls--gameplay)
9. [Automated Testing](#automated-testing)
10. [Academic Demonstrability](#academic-demonstrability)

---

## 1. Project Overview

Traditional Pac-Man relies on simple deterministic tile-targeting rules. **AI Pac-Man: The Adaptive Maze Challenge** transforms the environment into an adaptive multi-agent system. Ghost agents evaluate environmental state and player vulnerabilities, dynamically adjusting their pursuit strategies using graph search and fuzzy decision logic.

The game is designed with a strict separation of concerns:
- **Game Engine**: Pure Python & Pygame with procedural vector graphics (runs standalone without external image or sound assets).
- **Physics & Grid Navigation**: Sub-pixel floating point positioning with perpendicular corner snapping and direction buffering.
- **AI Core**: Independent, unit-testable modules for pathfinding and fuzzy inference.

---

## 2. Key Features

- **Procedural Retro Arcade Aesthetics**: Full vector rendering of classic maze walls, animated Pac-Man chomping, skirted ghosts with directional pupils, pulsing power pellets, and retro HUD overlays.
- **Collision & Movement System**: Grid-based spatial checks preventing wall penetration while allowing seamless 180° reversals and smooth corner turns.
- **Adaptive Difficulty**: A bounded, smoothed performance controller gradually adjusts ghost speed and pursuit range; the current tier is shown in the HUD.
- **Expanded Maze**: The 21×21 base maze is surrounded by a connected collectible corridor, producing a 25×25 playable grid sized to fit the display.
- **Safe Respawning**: Losing a life preserves score and maze progress, resets entity positions, and provides a pause plus brief collision immunity.
- **Configurable Maze Environments**: JSON-based level configurations supporting dynamic obstacles, keys, switches, and ghost gates.
- **Multi-Modal Game State**: Robust state transitions (`MENU`, `PLAYING`, `PAUSED`, `GAME_OVER`, `VICTORY`).

---

## 3. AI & Soft Computing Components

### A. Graph Search Algorithms
1. **Breadth-First Search (BFS)**:
   - Computes the unweighted shortest path on the 4-connected grid.
   - Serves as the rigorous benchmark baseline for expanded node counts and search runtime.
2. **$A^*$ Search Algorithm**:
   - Uses evaluation function $f(n) = g(n) + h(n)$.
   - Admissible Manhattan distance heuristic:
     $$h(n) = |x_n - x_{\text{goal}}| + |y_n - y_{\text{goal}}|$$
   - Optimally finds shortest paths while drastically reducing expanded nodes in open corridors.

### B. Ghost Archetypes & Finite-State Machines
Each ghost operates under a Finite-State Machine with distinct states: `CHASE`, `PATROL`, `FLEE`, and `SEARCH`.
- **Hunter (Red / Blinky)**: Relentlessly computes direct $A^*$ paths to Pac-Man's exact coordinates.
- **Ambusher (Pink / Pinky)**: Anticipates player trajectory, targeting 3–4 tiles ahead along Pac-Man's heading vector.
- **Guard (Orange / Clyde)**: Patrols vital junctions, keys, or level exits; shifts into pursuit when Pac-Man enters its perimeter.
- **Patrol / Random (Cyan / Inky)**: Explores corridors through controlled stochastic arbitration at intersections.

### C. Fuzzy Logic Controller (Soft Computing)
A Mamdani Fuzzy Inference System determines real-time ghost **Aggression Scores** ($0 - 100$):
- **Fuzzy Inputs**:
  1. *Distance to Pac-Man* (Near, Medium, Far)
  2. *Pellet Protection Status* (Vulnerable, Expiring, Protected)
  3. *Player Lives / Vulnerability* (Critical, Moderate, Healthy)
- **Fuzzy Inference & Defuzzification**:
  - Rule base evaluated using Min-Max aggregation.
  - Centroid defuzzification yields a continuous aggression score that modulates ghost movement speed and chase persistence.

---

## 4. Progressive Level Design

| Level | Name | Theme & Challenge |
|:---:|---|---|
| **Level 1** | **Learning the Maze** | Introductory layout; collect required dots and reach the exit while avoiding a solitary basic ghost. |
| **Level 2** | **Locked Passages** | Introduces color-coded keys, locked barrier doors, and toggle switches controlling corridor gates. |
| **Level 3** | **Survival Challenge** | Multi-ghost coordination (Hunter + Ambusher), limited sight radius / fog-of-war, and scarce power pellets. |
| **Level 4** | **Final Escape** | Large multi-chamber maze with timed hazard barriers, puzzle switches, guarding ghosts, and a sealed exit requiring all objectives. |

---

## 5. Project Architecture

```
ai-pacman/
├── main.py                 # Pygame entry point & event dispatch loop
├── settings.py             # Constants, speeds, dimensions, color palettes
├── maze.py                 # Grid representation, wall checks, dots & pellets
├── pacman.py               # Player entity, corner snapping, mouth animation
├── ghost.py                # Ghost agents, movement arbitration, collision bounds
├── game_state.py           # Game loop logic, scoring, lives, state machine
├── renderer.py             # Geometric arcade renderer, HUD, modal overlays
├── pathfinding.py          # BFS and A* search algorithm implementations
├── fuzzy_controller.py     # Mamdani Fuzzy Inference System for ghost aggression
├── level_manager.py        # JSON level loader and objective verification
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
│   ├── test_pathfinding.py
│   └── test_fuzzy_controller.py
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
   - Survival times and level completion rates under fixed vs. fuzzy-controlled ghost aggression.
3. **Reproducibility**: Experiments run headlessly with deterministic seeds, producing clean CSV output and publication-quality Matplotlib comparison plots.

---

## License

Developed for educational purposes under the Artificial Intelligence and Soft Computing (AISC) course curriculum.
