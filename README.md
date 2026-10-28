# AI Pac-Man: Minimax with Alpha-Beta Pruning

### Artificial Intelligence & Soft Computing (AISC) Challenge

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Pygame](https://img.shields.io/badge/pygame-2.6.1-green.svg)](https://www.pygame.org/)
[![Testing](https://img.shields.io/badge/tests-pytest-yellow.svg)](https://docs.pytest.org/)
[![Course](https://img.shields.io/badge/course-AISC-purple.svg)](#algorithm-overview)

An undergraduate **Artificial Intelligence and Soft Computing (AISC)** project that upgrades classic arcade Pac-Man using **Minimax Search with Alpha-Beta (α-β) Pruning**.

The project implements adversarial AI to help ghosts anticipate Pac-Man's possible counter-moves and make strategic pursuit decisions. It also supports autonomous Pac-Man gameplay, allowing the AI's decision-making behavior to be observed and evaluated.

---

## 1. Algorithm Overview

### Minimax with Alpha-Beta (α-β) Pruning

- **Type:** Classical Multi-Agent Adversarial Search.
- **Concept:** The ghost looks ahead a specified number of steps, simulating possible future moves by both the ghost and Pac-Man.
- **Minimax Strategy:** The ghost selects a move that maximizes its expected evaluation score, assuming Pac-Man responds optimally to minimize the ghost's advantage.
- **Alpha-Beta Pruning:** Maintains bounds \([\alpha,\beta]\). If a branch cannot improve the current decision, the algorithm stops exploring that branch.
- **Behavior:** Strategic, calculated, and capable of anticipating potential escapes and unfavorable future positions.

### How Alpha-Beta Pruning Works

Alpha-Beta Pruning optimizes Minimax by eliminating branches that cannot influence the final decision.

- **Alpha (α):** The best score MAX can guarantee so far.
- **Beta (β):** The best score MIN can guarantee so far.
- **Pruning condition:** When \(\alpha \geq \beta\), further exploration of that branch is unnecessary.

The optimization reduces the number of nodes evaluated without changing the result of the underlying Minimax search, assuming the same evaluation function and search depth.

### Computational Complexity

Let \(b\) be the average branching factor and \(d\) be the search depth.

- **Minimax:** \(O(b^d)\) in the worst case.
- **Minimax with Alpha-Beta Pruning:** Can approach \(O(b^{d/2})\) with favorable move ordering, while retaining \(O(b^d)\) worst-case complexity.

This makes Alpha-Beta Pruning useful for real-time decision-making, where the AI must balance strategic lookahead with computational cost.

---

## 2. Why Manhattan Distance Is Used

The AI uses Manhattan Distance as a heuristic for evaluating positions in the grid-based maze.

The formula is:

\[
d((x_1,y_1),(x_2,y_2))
=|x_1-x_2|+|y_1-y_2|
\]

Manhattan Distance is useful because:

1. **Grid-based movement:** Pac-Man and the ghosts move horizontally or vertically rather than diagonally.
2. **Computational efficiency:** The heuristic requires only basic arithmetic operations, making it inexpensive to evaluate across many search-tree nodes.
3. **Distance estimation:** It estimates the minimum number of orthogonal steps between two positions when obstacles are ignored.
4. **Evaluation function:** It helps estimate whether a ghost's position is favorable relative to Pac-Man.

**Important limitation:** Manhattan Distance does not account for walls or blocked corridors. Therefore, it may underestimate the actual shortest path through the maze. It is a heuristic estimate, not necessarily the true distance.

---

## 3. How to Run the Game

### Prerequisites

Ensure Python 3.12 is installed and available from your terminal.

Install the required dependencies:

```powershell
pip install -r requirements.txt
```

### 1. Manual Gameplay Against Minimax Ghosts

Control Pac-Man manually while the ghosts use the Minimax AI.

```powershell
python main.py
```

### 2. Autonomous Pac-Man Gameplay

Watch the autonomous Pac-Man AI play against the Minimax-controlled ghosts.

```powershell
python main.py --ai
```

### 3. Real-Time AI Debug Mode

Display AI debugging information, including candidate scores, visited nodes, and pruned branches, in the terminal.

```powershell
python main.py --ai --ai-debug
```

The exact debug output depends on the information implemented in the project's AI modules.

---

## 4. Controls

| Key | Action |
|---|---|
| **Arrow Keys / W, A, S, D** | Steer Pac-Man using corner-snapped buffered turns |
| **P / Spacebar** | Pause or resume the game |
| **R** | Restart the game |
| **ESC** | Exit the game |

---

## 5. Automated Unit Tests

Run the automated test suite using pytest:

```powershell
python -m pytest -v
```

The original project README reports 59 unit tests. After removing Simulated Annealing, verify the actual test count and ensure all remaining tests pass.

The relevant test coverage includes:

- **Minimax and Alpha-Beta Pruning:** Search correctness, pruning behavior, and branch cutoffs.
- **Pac-Man AI:** Autonomous decision-making and evaluation behavior.
- **Game State:** Game-state transitions, gameplay logic, and state management.
- **Collision Physics:** Sub-pixel collision handling and respawn invulnerability.

Relevant test files may include:

- `test_ghost_minimax.py`
- `test_pacman_ai.py`
- `test_game_state.py`

The exact filenames and test coverage should match the current repository.

---

## 6. Project Objectives

The project demonstrates the application of classical AI techniques to a real-time arcade game.

Its main objectives are:

1. Implement adversarial decision-making using Minimax.
2. Improve search efficiency through Alpha-Beta Pruning.
3. Apply heuristic evaluation to grid-based game states.
4. Support both manual and autonomous Pac-Man gameplay.
5. Evaluate AI behavior using debugging tools and automated unit tests.

---

## 7. Conclusion

This project demonstrates how **Minimax with Alpha-Beta Pruning** can be used to develop strategic ghost behavior in Pac-Man.

By evaluating future game states and anticipating possible counter-moves, the AI can make more informed decisions than a purely reactive movement strategy. Alpha-Beta Pruning reduces unnecessary search while preserving the Minimax result for the chosen search horizon.

The project provides a practical demonstration of adversarial search, heuristic evaluation, search-tree optimization, and AI-driven gameplay as part of the Artificial Intelligence and Soft Computing course.
