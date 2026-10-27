# AI Pac-Man: Minimax & Simulated Annealing
### Artificial Intelligence & Soft Computing (AISC) Challenge

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Pygame](https://img.shields.io/badge/pygame-2.6.1-green.svg)](https://www.pygame.org/)
[![Testing](https://img.shields.io/badge/tests-pytest-yellow.svg)](https://docs.pytest.org/)
[![Course](https://img.shields.io/badge/course-AISC-purple.svg)](#algorithms-overview)

An undergraduate **Artificial Intelligence and Soft Computing (AISC)** project upgrading classic arcade Pac-Man to compare two fundamentally distinct paradigms:
1. **Classical Adversarial AI**: Minimax Search with Alpha-Beta ($\alpha$-$\beta$) Pruning.
2. **Soft Computing / Metaheuristic**: Simulated Annealing (Boltzmann Softmax Exploration).

You can run them individually or in **alternating rounds** (e.g., Round 1 uses Minimax; Round 2 uses Simulated Annealing).

---

## 1. Algorithms Overview

### Algorithm A: Minimax with Alpha-Beta ($\alpha$-$\beta$) Pruning
- **Type**: Classical Multi-Agent Adversarial Search.
- **Concept**: The Ghost looks ahead $d$ steps into the future, simulating Pac-Man's optimal counter-moves at every step.
- **Alpha-Beta Pruning**: Maintains bounds $[\alpha, \beta]$. If a branch is discovered to be worse than an already guaranteed outcome ($\beta \le \alpha$), the search immediately cuts off that branch.
- **Behavior**: Cold, calculated, and trap-setting. Guarantees optimal pursuit within the lookahead horizon.

---

### Algorithm B: Simulated Annealing (Boltzmann Exploration)
- **Type**: Soft Computing / Physics-Inspired Metaheuristic.
- **Concept**: Inspired by the heating and controlled cooling of metals in metallurgy.
  - **Temperature ($T$)**: Starts hot ($T_0 = 5.0$) at the beginning of each life/round, then smoothly cools down ($T \leftarrow T \times 0.995$).
  - **Metropolis-Boltzmann Probability**: The probability of picking action $a$ is proportional to its Boltzmann energy weight:
    $$P(a) = \frac{e^{\frac{\text{Score}(a) - \text{MaxScore}}{T}}}{\sum_j e^{\frac{\text{Score}(a_j) - \text{MaxScore}}{T}}}$$
  - **High Temperature (Hot)**: All moves have comparable probabilities. Ghosts explore unpredictable routes, preventing dead-end locks.
  - **Low Temperature (Cold)**: As $T \to 0$, $P(\text{best move}) \to 1.0$. The ghosts settle into greedy, aggressive pursuit.
- **Behavior**: Erratic, organic, and unpredictable early on; tightly focused and aggressive later.

---

### Comparing the Two Paradigms (AISC Study)

| Feature | Minimax with $\alpha$-$\beta$ Pruning | Simulated Annealing (SA) |
| :--- | :---: | :---: |
| **Category** | Classical Adversarial AI | Soft Computing / Metaheuristic |
| **Lookahead Horizon** | Multi-step tree ($d$ plies) | 1-step thermodynamic sampling |
| **Opponent Modeling** | Anticipates rational counter-moves | Stochastically explores maze state |
| **Local Trap Recovery** | Requires loop penalties | Naturally breaks loops at high $T$ |
| **Computation Cost** | $\mathcal{O}(b^{d/2})$ node evaluations | $\mathcal{O}(1)$ instantaneous evaluations |

---

## 2. Why Manhattan Distance Is Used

Both algorithms use an evaluation function to score future tiles. In a grid-based maze, **Manhattan Distance** ($|x_1 - x_2| + |y_1 - y_2|$) is used because:
1. **Pac-Man Moves on a Grid**: Characters cannot walk diagonally through walls. Manhattan distance counts actual orthogonal grid steps.
2. **Nanosecond Speed**: Computing Manhattan distance takes 2 subtractions and 1 addition. Doing full graph search (like BFS or $A^*$) inside hundreds of tree nodes would drop frame rates.
3. **Admissible Metric**: It represents the theoretical minimum number of moves to reach a tile without overestimating.

---

## 3. How to Run the Game

### Prerequisites
```powershell
pip install -r requirements.txt
```

### 1. Alternating Round Mode (Minimax in Round 1, Simulated Annealing in Round 2)
```powershell
python main.py --ghost-algo alternate
```

### 2. Standard Minimax Alpha-Beta Mode
```powershell
# Play manually against Minimax ghosts
python main.py

# Watch autonomous Pac-Man play against Minimax ghosts
python main.py --ai
```

### 3. Pure Simulated Annealing Mode
```powershell
# Play against Simulated Annealing ghosts
python main.py --ghost-algo sa

# Watch autonomous Pac-Man play against SA ghosts
python main.py --ai --ghost-algo sa
```

### 4. Real-time Debug Mode
Shows candidate scores, visited nodes, and pruned branches in your terminal:
```powershell
python main.py --ai --ai-debug
```

---

## 4. Controls

| Key | Action |
|---|---|
| **Arrow Keys / W, A, S, D** | Steer Pac-Man (corner-snapped buffered turns) |
| **P / Spacebar** | Pause / Resume |
| **R** | Full Restart |
| **ESC** | Exit Game |

---

## 5. Automated Unit Tests

Run the full automated test suite (59 unit tests):
```powershell
python -m pytest -v
```
All tests verify:
- Minimax Alpha-Beta pruning correctness and branch cutoffs (`test_ghost_minimax.py`, `test_pacman_ai.py`).
- Simulated Annealing temperature cooling, Boltzmann convergence, and reset logic (`test_ghost_sa.py`).
- Alternating algorithm transitions between Level 1 and Level 2 (`test_game_state.py`).
- Spatial sub-pixel collision physics and respawn invulnerability.
