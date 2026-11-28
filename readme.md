# Interactive Deterministic Finite Automaton (DFA) Simulator

A zero-dependency desktop application built in Python (`tkinter`) for constructing, validating, minimizing, and simulating **Deterministic Finite Automata (DFA)** in real time.

Developed as part of the **CSET302 — Automata Theory and Computability** coursework at **Bennett University, Greater Noida**.

## 👥 Authors

* **Shubh Pratap Singh Parihar** — `S24CSEU0941`
* **Harshiv Batra** — `S24CSEU1536`

## ✨ Key Features

* **Interactive Vector Graph Canvas:**
  * Double-click anywhere on the grid canvas to create states (`q0`, `q1`, ...), drag states freely, and double-click a state to toggle its accepting status.
  * Smooth panning (drag empty canvas), cursor-anchored scroll-wheel zoom, and one-click **Fit (`⛶`)** auto-centering.
  * Collision-free quadratic Bezier arcs for bidirectional transitions ($q_i \leftrightarrow q_j$) and elevated splines for self-loops.
  * 40-step deep-copy **Undo** history (`Ctrl+Z`).
* **Two-Way Synchronized Formal Definition & Transition Table ($\delta$):**
  * Live display of the formal 5-tuple $M = (Q, \Sigma, \delta, q_0, F)$.
  * Bidirectional sync: modifying any cell in the transition table updates the visual graph immediately, and drawing edges updates the table.
  * Real-time completeness and determinism auditing with visual dashed red rings on incomplete or non-deterministic states.
* **One-Click Trap State Completion (`+ Trap State`):**
  * Automatically detects all undefined $(q, a) \in Q \times \Sigma$ transitions, creates a non-accepting dead state (`q_dead`) with self-loops on $\Sigma$, and routes every missing edge to it.
* **Regular Expression $\rightarrow$ Minimal DFA Compiler (`Formula → DFA`):**
  * Compiles regular expressions supporting union (`|`), Kleene star (`*`), plus (`+`), optional (`?`), grouping (`( )`), and empty string ($\varepsilon$).
  * Implements **Thompson's Construction**, **$\varepsilon$-closure Subset Construction**, and **Hopcroft-style Partition Refinement** minimization.
* **Step-by-Step Tape Simulation & Batch Testing:**
  * Character-by-character visual tape highlighting consumed, active, and errored symbols alongside a live execution trace and adjustable auto-play speed.
  * Multi-line **Batch Test** suite supporting inline `: accept` / `: reject` assertions with pass/fail summaries.

## 🚀 Step-by-Step Instructions to Run This Program

You do **not** need to install any external packages (`pip install` is not required)—everything runs using standard Python.

### Step 1: Verify Python is Installed on Your PC

1. Open your terminal or command prompt:
   * **Windows:** Press `Win + R`, type `cmd`, and press **Enter**.
   * **macOS:** Press `Cmd + Space`, type `Terminal`, and press **Enter**.
   * **Linux:** Press `Ctrl + Alt + T`.
2. Check your Python version by running:
   ```bash
   python --version
   ```
   *(If that fails on Windows, try `py --version`. On macOS/Linux, try `python3 --version`.)*
3. **If you see a version number** (such as `Python 3.10` or higher), move to **Step 2**.
4. **If Python is not installed:**
   * Download the latest Python 3 installer from [python.org/downloads](https://www.python.org/downloads/).
   * **Windows Users (Crucial):** On the first screen of the installer, check **"Add python.exe to PATH"** at the bottom before clicking **Install Now**.

### Step 2: Get the Project Code

#### Option A: Clone via Git
```bash
git clone https://github.com/Manikparihar/DFA_simulator.git
cd DFA_simulator
```

#### Option B: Download ZIP from GitHub
1. Visit [https://github.com/Manikparihar/DFA_simulator](https://github.com/Manikparihar/DFA_simulator).
2. Click the green **`<> Code`** button at the top and select **Download ZIP**.
3. Extract the ZIP folder to your Desktop (e.g., `Desktop/DFA_simulator-main`).

### Step 3: Launch the Application

#### Method 1: Run from Terminal / Command Prompt
1. Open your Command Prompt / Terminal inside the `DFA_simulator` folder:
   ```bash
   cd DFA_simulator
   ```
2. Start the simulator using the command that worked in Step 1:
   ```bash
   python dfa_simulator.py
   ```
   *or on Windows:*
   ```bash
   py dfa_simulator.py
   ```
   *or on macOS/Linux:*
   ```bash
   python3 dfa_simulator.py
   ```
3. The **DFA Simulator** desktop window will launch immediately.

#### Method 2: Run in Visual Studio Code (VS Code)
1. Open **VS Code**, click **File → Open Folder...**, and select the `DFA_simulator` folder.
2. Click `dfa_simulator.py` in the Explorer sidebar to open it.
3. Click the **Play button (`▶`)** in the top-right corner of the editor.

## 🎮 Quick Walkthrough & Controls

When the app opens, a sample DFA (*"Strings over {0,1} ending with 01"*) is pre-loaded so you can test it immediately:

| Action | How to Perform |
| :--- | :--- |
| **Test a String** | Type an input (e.g., `1101`) in the **Simulation** bar and click **`▶ Auto-play`** or **`Step ⏭`** |
| **Load Presets** | Use the **`Load preset DFA…`** dropdown in the top-right corner |
| **Start Fresh** | Click **`🗑 Clear`** on the top toolbar |
| **Add State** | Double-click empty canvas space or click **`+ Add State`** |
| **Add Transition** | Click **`→ Add Transition`** $\rightarrow$ click source state $\rightarrow$ click target state (same state = self-loop) |
| **Toggle Accept State** | Double-click a state or toggle its `Acc` checkbox in the $\delta$-table |
| **Set Start State** | Right-click a state $\rightarrow$ *Set as start state*, or select its `Start` radio button in the table |
| **Rename State** | Click the state's button (`q0 ✎`) in the $\delta$-table, use **`✎ Rename State`**, or right-click the state |
| **Complete Partial DFA** | Click **`+ Trap State`** to auto-create `q_dead` and route all missing transitions |
| **Compile Regex** | Open the **`Formula → DFA`** tab, enter a regex (e.g., `(0|1)*01`), and click **`▶ Generate DFA`** |
| **Batch Test Strings** | Open the **`Batch Test`** tab, enter one string per line (optionally with `: accept` / `: reject`), and click **`▶ Run All`** |
| **Pan, Zoom & Fit** | Drag empty canvas to pan; scroll mouse wheel to zoom; click **`⛶ Fit`** to center |
| **Undo** | Press `Ctrl+Z` or click **`↶ Undo`** |

## 🛠️ Troubleshooting

* **`'python' is not recognized as an internal or external command`:**
  Re-run the Python installer, select **Modify**, and check **"Add Python to environment variables / PATH"**, or run `py dfa_simulator.py` instead.
* **`ModuleNotFoundError: No module named 'tkinter'` (Linux only):**
  Install the system Tkinter package:
  ```bash
  sudo apt-get install python3-tk
  ```
* **Nodes appear clipped or off-screen after generating a large DFA:**
  Click the **`⛶ Fit`** button in the toolbar to automatically scale and center the entire graph.

## 📂 Repository Structure

```text
DFA_simulator/
├── dfa_simulator.py      # Complete standalone Python/Tkinter application
└── README.md             # Step-by-step setup & usage documentation
```

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).