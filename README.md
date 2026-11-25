# Interactive Deterministic Finite Automaton (DFA) Simulator

A zero-dependency desktop application built in Python (`tkinter`) for constructing, validating, minimizing, and simulating **Deterministic Finite Automata (DFA)** in real time. 

Developed as part of the **CSET302 — Automata Theory and Computability** coursework at **Bennett University, Greater Noida**.

---

## 👥 Authors
* **Shubh Pratap Singh Parihar** (`S24CSEU0941`)
* **Harshiv Batra** (`S24CSEU1536`)

---

## ✨ Key Features

* **Interactive Vector Graph Canvas:**
  * Double-click anywhere on the canvas to add states (`q0`, `q1`, ...), drag states freely, and double-click a state to toggle its accepting status.
  * Smooth pan (drag empty canvas), cursor-anchored scroll-wheel zoom, and one-click **Fit-to-View** scaling.
  * Collision-free quadratic Bezier arcs for bidirectional edges ($q_i \leftrightarrow q_j$) and elevated splines for self-loops.
  * Right-click context menu for setting start states, toggling accept states, renaming states, and editing/deleting edges.
  * 40-step deep-copy **Undo** history (`Ctrl+Z`).
* **Two-Way Synchronized Formal Definition & Transition Table ($\delta$):**
  * Live display of the formal 5-tuple $M = (Q, \Sigma, \delta, q_0, F)$.
  * Bidirectional sync: updating any cell in the transition table immediately updates the visual graph, and drawing edges updates the table.
  * Real-time completeness and determinism validation with visual error rings on incomplete or non-deterministic states.
* **One-Click Trap State Completion (`+ Trap State`):**
  * Automatically detects all missing $(q, a) \in Q \times \Sigma$ transitions, creates a non-accepting dead state (`q_dead`) with self-loops on $\Sigma$, and routes every undefined transition to it.
* **Regular Expression $\rightarrow$ DFA Compiler (`Formula → DFA`):**
  * Compiles regular expressions supporting union (`|`), Kleene star (`*`), plus (`+`), optional (`?`), grouping (`( )`), and empty string (`ε`).
  * Implements **Thompson's Construction**, **$\epsilon$-closure Subset Construction**, and **Hopcroft-style Partition Refinement** minimization.
* **Step-by-Step Tape Simulation & Batch Testing:**
  * Character-by-character visual tape highlighting consumed, active, and errored symbols alongside a live transition trace and adjustable auto-play speed.
  * Multi-line **Batch Test** runner supporting inline `: accept` and `: reject` assertions with pass/fail summaries.

---

## 🛠️ Tech Stack & Requirements

* **Language:** Python 3.8+
* **Dependencies:** Standard library only (`tkinter`, `math`, `json`, `re`, `random`) — **no `pip install` packages required**.

---

## 🚀 How to Run

1. Clone or download this repository:
   ```bash
   git clone [https://github.com/your-username/dfa-simulator.git](https://github.com/your-username/dfa-simulator.git)
   cd dfa-simulator
