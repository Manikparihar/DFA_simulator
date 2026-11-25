import json
import math
import random
import re
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

R = 24  # State circle radius


def parse_syms(s: str):
    seen = set()
    out = []
    for part in s.split(","):
        t = part.strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def make_preset(names, pos, start, acc, transitions):
    states = [{"id": n, "name": n, "x": float(pos[i][0]), "y": float(pos[i][1])} for i, n in enumerate(names)]
    edges = []
    edge_counter = 1
    for f, a, t in transitions:
        existing = next((e for e in edges if e["from"] == f and e["to"] == t), None)
        if not existing:
            existing = {"id": f"e{edge_counter}", "from": f, "to": t, "syms": []}
            edge_counter += 1
            edges.append(existing)
        if a not in existing["syms"]:
            existing["syms"].append(a)
    return {"states": states, "edges": edges, "start": start, "acc": list(acc)}


PRESETS = [
    (
        "Strings over {0,1} ending with 01",
        "1101",
        lambda: make_preset(
            ["q0", "q1", "q2"],
            [[130, 220], [310, 220], [490, 220]],
            "q0",
            ["q2"],
            [
                ["q0", "0", "q1"],
                ["q0", "1", "q0"],
                ["q1", "0", "q1"],
                ["q1", "1", "q2"],
                ["q2", "0", "q1"],
                ["q2", "1", "q0"],
            ],
        ),
    ),
    (
        "Even number of 0s and even number of 1s",
        "0110",
        lambda: make_preset(
            ["q0", "q1", "q2", "q3"],
            [[170, 130], [410, 130], [170, 320], [410, 320]],
            "q0",
            ["q0"],
            [
                ["q0", "0", "q1"],
                ["q1", "0", "q0"],
                ["q2", "0", "q3"],
                ["q3", "0", "q2"],
                ["q0", "1", "q2"],
                ["q2", "1", "q0"],
                ["q1", "1", "q3"],
                ["q3", "1", "q1"],
            ],
        ),
    ),
    (
        "Binary numbers divisible by 3",
        "1001",
        lambda: make_preset(
            ["q0", "q1", "q2"],
            [[140, 220], [320, 220], [500, 220]],
            "q0",
            ["q0"],
            [
                ["q0", "0", "q0"],
                ["q0", "1", "q1"],
                ["q1", "0", "q2"],
                ["q1", "1", "q0"],
                ["q2", "0", "q1"],
                ["q2", "1", "q2"],
            ],
        ),
    ),
    (
        "Strings over {a,b} containing substring aba",
        "baba",
        lambda: make_preset(
            ["q0", "q1", "q2", "q3"],
            [[110, 220], [260, 220], [410, 220], [560, 220]],
            "q0",
            ["q3"],
            [
                ["q0", "a", "q1"],
                ["q0", "b", "q0"],
                ["q1", "a", "q1"],
                ["q1", "b", "q2"],
                ["q2", "a", "q3"],
                ["q2", "b", "q0"],
                ["q3", "a", "q3"],
                ["q3", "b", "q3"],
            ],
        ),
    ),
]


def delta_targets(m, state_id, sym):
    out = []
    for e in m["edges"]:
        if e["from"] == state_id and sym in e["syms"] and e["to"] not in out:
            out.append(e["to"])
    return out


def state_name(m, state_id):
    for s in m["states"]:
        if s["id"] == state_id:
            return s["name"]
    return state_id or ""


def simulate_dfa(m, input_str):
    chars = list(input_str)
    trace = []
    dead = ""
    cur = m["start"]
    if not cur:
        return {"chars": chars, "tr": trace, "dead": "No start state", "acc": False}
    for ch in chars:
        targets = delta_targets(m, cur, ch)
        if len(targets) != 1:
            if targets:
                dead = f"Non-deterministic on '{ch}' from {state_name(m, cur)}"
            else:
                dead = f"No transition from {state_name(m, cur)} on '{ch}'"
            break
        nxt = targets[0]
        edge = next(e for e in m["edges"] if e["from"] == cur and e["to"] == nxt and ch in e["syms"])
        trace.append({"from": cur, "to": nxt, "ch": ch, "edge": edge["id"]})
        cur = nxt
    accepted = (not dead) and (cur in m["acc"])
    return {"chars": chars, "tr": trace, "dead": dead, "acc": accepted}


def regex_to_dfa(pattern: str, minimize: bool, plus_union: bool):
    s = [c for c in pattern if c.strip() != ""]
    if not s:
        raise ValueError("Enter a regular expression first.")
    if plus_union:
        s = ["|" if (c == "+" and (k == 0 or s[k - 1] != "\\")) else c for k, c in enumerate(s)]

    idx = 0
    nfa = []
    alpha = set()

    def new_state():
        nfa.append([])
        return len(nfa) - 1

    def add_edge(a, b, ch):
        nfa[a].append((ch, b))

    def parse_atom():
        nonlocal idx
        if idx >= len(s):
            raise ValueError("Unexpected end of formula")
        c = s[idx]
        idx += 1
        if c == "(":
            frag = parse_alt()
            if idx >= len(s) or s[idx] != ")":
                raise ValueError("Missing closing ')'")
            idx += 1
            return frag
        if c in "*+?|) ":
            raise ValueError(f"Unexpected '{c}'")
        a, b = new_state(), new_state()
        if c == "ε":
            add_edge(a, b, None)
            return (a, b)
        ch = c
        if c == "\\":
            if idx >= len(s):
                raise ValueError("Dangling escape '\\'")
            ch = s[idx]
            idx += 1
        alpha.add(ch)
        add_edge(a, b, ch)
        return (a, b)

    def parse_rep():
        nonlocal idx
        frag = parse_atom()
        while idx < len(s) and s[idx] in "*+?":
            op = s[idx]
            idx += 1
            a, b = new_state(), new_state()
            add_edge(a, frag[0], None)
            add_edge(frag[1], b, None)
            if op != "+":
                add_edge(a, b, None)
            if op != "?":
                add_edge(frag[1], frag[0], None)
            frag = (a, b)
        return frag

    def parse_cat():
        frag = None
        while idx < len(s) and s[idx] not in "|)":
            nxt = parse_rep()
            if frag is None:
                frag = nxt
            else:
                add_edge(frag[1], nxt[0], None)
                frag = (frag[0], nxt[1])
        if frag is None:
            a = new_state()
            return (a, a)
        return frag

    def parse_alt():
        nonlocal idx
        frag = parse_cat()
        while idx < len(s) and s[idx] == "|":
            idx += 1
            nxt = parse_cat()
            a, b = new_state(), new_state()
            add_edge(a, frag[0], None)
            add_edge(a, nxt[0], None)
            add_edge(frag[1], b, None)
            add_edge(nxt[1], b, None)
            frag = (a, b)
        return frag

    frag = parse_alt()
    if idx < len(s):
        raise ValueError("Unmatched ')'")

    syms = sorted(alpha)

    def eps_closure(states):
        stack = list(states)
        res = set(states)
        while stack:
            u = stack.pop()
            for ch, v in nfa[u]:
                if ch is None and v not in res:
                    res.add(v)
                    stack.append(v)
        return frozenset(res)

    start_set = eps_closure([frag[0]])
    dfa_sets = [start_set]
    set_index = {start_set: 0}
    dtrans = []

    k = 0
    while k < len(dfa_sets):
        row = []
        for c in syms:
            nxt = set()
            for u in dfa_sets[k]:
                for ch, v in nfa[u]:
                    if ch == c:
                        nxt.add(v)
            clo = eps_closure(nxt)
            if clo not in set_index:
                set_index[clo] = len(dfa_sets)
                dfa_sets.append(clo)
            row.append(set_index[clo])
        dtrans.append(row)
        k += 1

    accepting = [frag[1] in st for st in dfa_sets]
    part = [1 if a else 0 for a in accepting]
    if minimize:
        num_parts = len(set(part))
        while True:
            sigs = [f"{part[i]}|" + ",".join(str(part[t]) for t in dtrans[i]) for i in range(len(dfa_sets))]
            mp = {}
            new_part = []
            for sg in sigs:
                if sg not in mp:
                    mp[sg] = len(mp)
                new_part.append(mp[sg])
            part = new_part
            if len(mp) == num_parts:
                break
            num_parts = len(mp)
    else:
        part = list(range(len(dfa_sets)))

    rep = {}
    for i, c in enumerate(part):
        if c not in rep:
            rep[c] = i

    order = [part[0]]
    name_map = {part[0]: "q0"}
    q_idx = 0
    while q_idx < len(order):
        c = order[q_idx]
        for t in dtrans[rep[c]]:
            tc = part[t]
            if tc not in name_map:
                name_map[tc] = f"q{len(order)}"
                order.append(tc)
        q_idx += 1

    names = [name_map[c] for c in order]
    cols = max(3, math.ceil(math.sqrt(len(order))))
    pos = [[120 + (i % cols) * 165, 120 + (i // cols) * 145] for i in range(len(order))]
    transitions = []
    for c in order:
        for j, t in enumerate(dtrans[rep[c]]):
            transitions.append([name_map[c], syms[j], name_map[part[t]]])
    acc_names = [name_map[c] for c in order if accepting[rep[c]]]

    info = f"NFA {len(nfa)} states → DFA {len(dfa_sets)} states" + (
        f" → minimized to {len(order)}" if minimize else ""
    )
    return make_preset(names, pos, "q0", acc_names, transitions), info


class DFASimulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DFA Simulator")
        self.geometry("1280x800")
        self.configure(bg="#f1f5f9")

        self.m = PRESETS[0][2]()
        self.history = []
        self.extra_alpha = []
        self.tool = "select"  # "select", "connect", or "rename"
        self.pending_from = None
        self.edge_counter = 100

        # Viewport pan/zoom
        self.vx = 0.0
        self.vy = 0.0
        self.vk = 1.0

        # Interaction state
        self.drag_state = None
        self.pan_origin = None

        # Simulation state
        self.step_idx = 0
        self.playing = False
        self.play_after_id = None

        self._build_ui()
        self.bind_all("<Control-z>", lambda e: self._on_ctrl_z(e))
        self.refresh_all()

    def _on_ctrl_z(self, event):
        if isinstance(event.widget, (tk.Entry, tk.Text, ttk.Combobox)):
            return
        self.undo()

    def push_history(self, snapshot=None):
        snap = snapshot if snapshot is not None else json.loads(json.dumps(self.m))
        if not self.history or self.history[-1] != snap:
            self.history.append(snap)
            if len(self.history) > 40:
                self.history.pop(0)
        self.undo_btn.config(state="normal" if self.history else "disabled")

    def undo(self):
        if not self.history:
            return
        self.m = self.history.pop()
        self.pending_from = None
        self.undo_btn.config(state="normal" if self.history else "disabled")
        self.reset_sim()
        self.refresh_all()

    def _build_ui(self):
        # Top Header
        header = tk.Frame(self, bg="#f1f5f9", pady=8, padx=14)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg="#f1f5f9")
        title_box.pack(side="left")
        tk.Label(title_box, text="DFA Simulator", font=("Segoe UI", 16, "bold"), bg="#f1f5f9", fg="#0f172a").pack(
            anchor="w"
        )
        tk.Label(
            title_box,
            text="Build, validate and step through deterministic finite automata",
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg="#64748b",
        ).pack(anchor="w")

        right_hdr = tk.Frame(header, bg="#f1f5f9")
        right_hdr.pack(side="right")

        self.preset_var = tk.StringVar(value="Load preset DFA…")
        preset_names = [p[0] for p in PRESETS]
        self.preset_cb = ttk.Combobox(
            right_hdr, textvariable=self.preset_var, values=preset_names, state="readonly", width=36
        )
        self.preset_cb.pack(side="left")
        self.preset_cb.bind("<<ComboboxSelected>>", self.on_preset_selected)

        # Main Split Body
        body = tk.Frame(self, bg="#f1f5f9", padx=14, pady=4)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Left Column: Canvas + Simulation
        left_col = tk.Frame(body, bg="#f1f5f9")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_col.rowconfigure(0, weight=1)
        left_col.columnconfigure(0, weight=1)

        # Graph Card
        graph_card = tk.Frame(left_col, bg="white", bd=1, relief="solid", highlightbackground="#cbd5e1")
        graph_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        toolbar = tk.Frame(graph_card, bg="white", padx=8, pady=6)
        toolbar.pack(fill="x")

        self.btn_select = tk.Button(
            toolbar, text="↖ Select / Move", command=lambda: self.set_tool("select"), relief="groove", padx=8
        )
        self.btn_select.pack(side="left", padx=2)

        self.btn_connect = tk.Button(
            toolbar, text="→ Add Transition", command=lambda: self.set_tool("connect"), relief="groove", padx=8
        )
        self.btn_connect.pack(side="left", padx=2)

        self.btn_rename = tk.Button(
            toolbar, text="✎ Rename State", command=lambda: self.set_tool("rename"), relief="groove", padx=8
        )
        self.btn_rename.pack(side="left", padx=2)

        tk.Button(toolbar, text="+ Add State", command=self.add_state_random, bg="white", relief="groove", padx=8).pack(
            side="left", padx=2
        )

        tk.Button(
            toolbar, text="+ Trap State", command=self.complete_with_trap_state, bg="white", relief="groove", padx=8
        ).pack(side="left", padx=2)

        self.undo_btn = tk.Button(
            toolbar, text="↶ Undo", command=self.undo, state="disabled", bg="white", relief="groove", padx=8
        )
        self.undo_btn.pack(side="left", padx=2)

        self.fit_btn = tk.Button(toolbar, text="⛶ Fit (100%)", command=self.fit_view, bg="white", relief="groove", padx=8)
        self.fit_btn.pack(side="left", padx=2)

        tk.Button(toolbar, text="🗑 Clear", command=self.clear_all, bg="white", relief="groove", padx=8).pack(
            side="left", padx=2
        )

        self.hint_lbl = tk.Label(
            graph_card,
            text="Double-click canvas: new state · drag canvas: pan · scroll: zoom · double-click state: toggle accept · right-click: menu",
            font=("Segoe UI", 8),
            bg="white",
            fg="#64748b",
            anchor="w",
            padx=10,
        )
        self.hint_lbl.pack(fill="x")

        self.canvas = tk.Canvas(graph_card, bg="#f8fafc", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=6, pady=6)

        self.canvas.bind("<Configure>", lambda e: self.redraw_canvas())
        self.canvas.bind("<Button-1>", self.on_canvas_down)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_up)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_dblclick)
        self.canvas.bind("<Button-3>", self.on_canvas_rightclick)
        self.canvas.bind("<Motion>", self.on_canvas_move)
        self.canvas.bind("<MouseWheel>", self.on_canvas_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.zoom_at(e.x, e.y, 1.12))
        self.canvas.bind("<Button-5>", lambda e: self.zoom_at(e.x, e.y, 1 / 1.12))

        # Simulation Card
        sim_card = tk.Frame(left_col, bg="white", bd=1, relief="solid", padx=12, pady=10)
        sim_card.grid(row=1, column=0, sticky="ew")

        tk.Label(sim_card, text="Simulation", font=("Segoe UI", 11, "bold"), bg="white", fg="#0f172a").pack(anchor="w")

        ctrl_row = tk.Frame(sim_card, bg="white", pady=6)
        ctrl_row.pack(fill="x")

        self.input_var = tk.StringVar(value=PRESETS[0][1])
        self.input_var.trace_add("write", lambda *_: self.reset_sim())
        self.input_entry = tk.Entry(ctrl_row, textvariable=self.input_var, font=("Consolas", 11), width=24, relief="solid", bd=1)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=3)

        self.btn_back = tk.Button(ctrl_row, text="⏮ Back", command=self.step_back, bg="white", relief="groove", padx=8)
        self.btn_back.pack(side="left", padx=2)

        self.btn_play = tk.Button(
            ctrl_row, text="▶ Auto-play", command=self.toggle_play, bg="#4f46e5", fg="white", relief="flat", padx=10
        )
        self.btn_play.pack(side="left", padx=2)

        self.btn_fwd = tk.Button(ctrl_row, text="Step ⏭", command=self.step_fwd, bg="white", relief="groove", padx=8)
        self.btn_fwd.pack(side="left", padx=2)

        tk.Button(ctrl_row, text="↺ Reset", command=self.reset_sim, bg="white", relief="groove", padx=8).pack(
            side="left", padx=2
        )

        speed_row = tk.Frame(sim_card, bg="white")
        speed_row.pack(fill="x", pady=(0, 6))
        tk.Label(speed_row, text="Speed:", font=("Segoe UI", 8), bg="white", fg="#64748b").pack(side="left")
        self.speed_var = tk.IntVar(value=900)
        tk.Scale(
            speed_row,
            from_=150,
            to=1800,
            orient="horizontal",
            variable=self.speed_var,
            showvalue=False,
            length=160,
            bg="white",
            highlightthickness=0,
        ).pack(side="left", padx=6)

        # Tape Canvas
        self.tape_canvas = tk.Canvas(sim_card, height=54, bg="white", highlightthickness=0)
        self.tape_canvas.pack(fill="x", pady=4)

        self.trace_lbl = tk.Label(
            sim_card,
            text="q0",
            font=("Consolas", 9),
            bg="#f8fafc",
            fg="#0f172a",
            anchor="w",
            justify="left",
            wraplength=680,
            padx=8,
            pady=6,
            relief="solid",
            bd=1,
        )
        self.trace_lbl.pack(fill="x", pady=(4, 4))

        self.verdict_lbl = tk.Label(sim_card, text="", font=("Segoe UI", 10, "bold"), pady=6)
        self.verdict_lbl.pack(fill="x")

        # Right Column: Notebook Tabs
        right_col = tk.Frame(body, bg="#f1f5f9")
        right_col.grid(row=0, column=1, sticky="nsew")

        self.notebook = ttk.Notebook(right_col)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Definition & Transition Table
        tab_def = tk.Frame(self.notebook, bg="#f1f5f9", padx=4, pady=6)
        self.notebook.add(tab_def, text="  Definition & δ Table  ")

        def_card = tk.Frame(tab_def, bg="white", bd=1, relief="solid", padx=12, pady=10)
        def_card.pack(fill="x", pady=(0, 10))
        tk.Label(def_card, text="Formal Definition", font=("Segoe UI", 11, "bold"), bg="white").pack(anchor="w")
        self.formal_lbl = tk.Label(
            def_card, text="", font=("Consolas", 9), bg="white", fg="#1e293b", justify="left", anchor="w"
        )
        self.formal_lbl.pack(fill="x", pady=4)

        self.status_lbl = tk.Label(
            def_card, text="", font=("Segoe UI", 9), justify="left", anchor="w", wraplength=420, padx=8, pady=6
        )
        self.status_lbl.pack(fill="x")

        table_card = tk.Frame(tab_def, bg="white", bd=1, relief="solid", padx=12, pady=10)
        table_card.pack(fill="both", expand=True)

        tbl_hdr = tk.Frame(table_card, bg="white")
        tbl_hdr.pack(fill="x", pady=(0, 6))
        tk.Label(tbl_hdr, text="Transition Table (δ)", font=("Segoe UI", 11, "bold"), bg="white").pack(side="left")

        sym_box = tk.Frame(tbl_hdr, bg="white")
        sym_box.pack(side="right")
        self.add_sym_var = tk.StringVar()
        sym_entry = tk.Entry(sym_box, textvariable=self.add_sym_var, width=10, font=("Consolas", 9), relief="solid", bd=1)
        sym_entry.pack(side="left", padx=4)
        sym_entry.bind("<Return>", lambda e: self.add_symbol())
        tk.Button(sym_box, text="+ Symbol", command=self.add_symbol, bg="white", relief="groove", font=("Segoe UI", 8)).pack(
            side="left"
        )

        tbl_scroll_wrap = tk.Frame(table_card, bg="white")
        tbl_scroll_wrap.pack(fill="both", expand=True)
        self.tbl_canvas = tk.Canvas(tbl_scroll_wrap, bg="white", highlightthickness=0)
        tbl_vscroll = ttk.Scrollbar(tbl_scroll_wrap, orient="vertical", command=self.tbl_canvas.yview)
        self.tbl_inner = tk.Frame(self.tbl_canvas, bg="white")
        self.tbl_inner.bind("<Configure>", lambda e: self.tbl_canvas.configure(scrollregion=self.tbl_canvas.bbox("all")))
        self.tbl_canvas.create_window((0, 0), window=self.tbl_inner, anchor="nw")
        self.tbl_canvas.configure(yscrollcommand=tbl_vscroll.set)
        self.tbl_canvas.pack(side="left", fill="both", expand=True)
        tbl_vscroll.pack(side="right", fill="y")

        # Tab 2: Formula -> DFA
        tab_re = tk.Frame(self.notebook, bg="white", padx=14, pady=12)
        self.notebook.add(tab_re, text="  Formula → DFA  ")

        tk.Label(tab_re, text="Regular Expression → DFA", font=("Segoe UI", 11, "bold"), bg="white").pack(anchor="w")
        tk.Label(
            tab_re,
            text="Operators: | union, * zero or more, + one or more, ? optional, ( ) grouping, ε empty string.",
            font=("Segoe UI", 8),
            bg="white",
            fg="#64748b",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(2, 8))

        self.re_var = tk.StringVar(value="(0|1)*01")
        re_entry = tk.Entry(tab_re, textvariable=self.re_var, font=("Consolas", 11), relief="solid", bd=1)
        re_entry.pack(fill="x", ipady=4)
        re_entry.bind("<Return>", lambda e: self.compile_regex())

        ex_frame = tk.Frame(tab_re, bg="white", pady=6)
        ex_frame.pack(fill="x")
        for ex in ["(0|1)*01", "(a|b)*abb", "1(0|1)*0", "(00|11)*", "a*b+", "(0|1)*1(0|1)"]:
            tk.Button(
                ex_frame,
                text=ex,
                font=("Consolas", 8),
                bg="#f8fafc",
                relief="groove",
                command=lambda x=ex: (self.re_var.set(x), self.re_plus_var.set(False)),
            ).pack(side="left", padx=2, pady=2)

        self.re_min_var = tk.BooleanVar(value=True)
        self.re_plus_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tab_re, text="Minimize the DFA (Hopcroft partition refinement)", variable=self.re_min_var, bg="white").pack(
            anchor="w", pady=(4, 0)
        )
        tk.Checkbutton(
            tab_re, text="Treat '+' as union (textbook notation)", variable=self.re_plus_var, bg="white"
        ).pack(anchor="w")

        tk.Button(
            tab_re, text="▶ Generate DFA", command=self.compile_regex, bg="#4f46e5", fg="white", relief="flat", padx=12, pady=5
        ).pack(anchor="w", pady=10)

        self.re_msg_lbl = tk.Label(tab_re, text="", font=("Segoe UI", 9), bg="white", wraplength=420, justify="left")
        self.re_msg_lbl.pack(fill="x")

        # Tab 3: Batch Test
        tab_batch = tk.Frame(self.notebook, bg="white", padx=14, pady=12)
        self.notebook.add(tab_batch, text="  Batch Test  ")

        tk.Label(tab_batch, text="Batch String Testing", font=("Segoe UI", 11, "bold"), bg="white").pack(anchor="w")
        tk.Label(
            tab_batch,
            text="One string per line (use ε for empty). Optional: append ': accept' or ': reject'. Click any result to load.",
            font=("Segoe UI", 8),
            bg="white",
            fg="#64748b",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(2, 6))

        self.batch_text = tk.Text(tab_batch, height=7, font=("Consolas", 10), relief="solid", bd=1)
        self.batch_text.insert("1.0", "01\n1101\n0\nε\n1001 : accept\n111 : reject")
        self.batch_text.pack(fill="x")

        tk.Button(
            tab_batch, text="▶ Run All", command=self.run_batch, bg="#4f46e5", fg="white", relief="flat", padx=12, pady=4
        ).pack(anchor="w", pady=8)

        self.batch_summary_lbl = tk.Label(tab_batch, text="", font=("Segoe UI", 9, "bold"), bg="white")
        self.batch_summary_lbl.pack(anchor="w")

        self.batch_list_frame = tk.Frame(tab_batch, bg="white")
        self.batch_list_frame.pack(fill="both", expand=True, pady=4)

        self.set_tool("select")

    def set_tool(self, tool):
        self.tool = tool
        self.pending_from = None
        for btn in (self.btn_select, self.btn_connect, self.btn_rename):
            btn.config(bg="white", fg="#0f172a")

        if tool == "select":
            self.btn_select.config(bg="#0f172a", fg="white")
            self.hint_lbl.config(
                text="Double-click canvas: new state · drag canvas: pan · scroll: zoom · double-click state: toggle accept · right-click: menu"
            )
        elif tool == "connect":
            self.btn_connect.config(bg="#0f172a", fg="white")
            self.hint_lbl.config(text="Click source state, then click target state (click same state for self-loop)")
        elif tool == "rename":
            self.btn_rename.config(bg="#0f172a", fg="white")
            self.hint_lbl.config(text="Click any state on the canvas to rename it")
        self.redraw_canvas()

    def screen_to_world(self, sx, sy):
        return (sx - self.vx) / self.vk, (sy - self.vy) / self.vk

    def world_to_screen(self, wx, wy):
        return wx * self.vk + self.vx, wy * self.vk + self.vy

    def find_state_at(self, sx, sy):
        wx, wy = self.screen_to_world(sx, sy)
        for s in reversed(self.m["states"]):
            if math.hypot(wx - s["x"], wy - s["y"]) <= R + 3:
                return s
        return None

    def on_canvas_wheel(self, event):
        factor = 1.12 if event.delta > 0 else 1 / 1.12
        self.zoom_at(event.x, event.y, factor)

    def zoom_at(self, sx, sy, factor):
        nk = min(2.5, max(0.25, self.vk * factor))
        self.vx = sx - (sx - self.vx) * (nk / self.vk)
        self.vy = sy - (sy - self.vy) * (nk / self.vk)
        self.vk = nk
        self.fit_btn.config(text=f"⛶ Fit ({round(self.vk * 100)}%)")
        self.redraw_canvas()

    def fit_view(self):
        states = self.m["states"]
        if not states:
            self.vx, self.vy, self.vk = 0.0, 0.0, 1.0
            self.fit_btn.config(text="⛶ Fit (100%)")
            self.redraw_canvas()
            return
        w = max(300, self.canvas.winfo_width())
        h = max(300, self.canvas.winfo_height())
        xs = [s["x"] for s in states]
        ys = [s["y"] for s in states]
        min_x, max_x = min(xs) - 80, max(xs) + 80
        min_y, max_y = min(ys) - 95, max(ys) + 70
        bw, bh = max(120, max_x - min_x), max(120, max_y - min_y)
        self.vk = min(1.25, max(0.3, min(w / bw, h / bh)))
        self.vx = (w - bw * self.vk) / 2 - min_x * self.vk
        self.vy = (h - bh * self.vk) / 2 - min_y * self.vk
        self.fit_btn.config(text=f"⛶ Fit ({round(self.vk * 100)}%)")
        self.redraw_canvas()

    def on_canvas_down(self, event):
        st = self.find_state_at(event.x, event.y)
        if self.tool == "rename":
            if st:
                self.rename_state(st["id"])
            self.set_tool("select")
            return

        if self.tool == "connect":
            if st:
                if self.pending_from is None:
                    self.pending_from = st["id"]
                    self.hint_lbl.config(text=f"Source: {st['name']} — click target state (same state for self-loop)")
                else:
                    src, dst = self.pending_from, st["id"]
                    self.pending_from = None
                    self.set_tool("select")
                    self.prompt_new_edge(src, dst)
            else:
                self.pending_from = None
            self.redraw_canvas()
            return

        if st:
            wx, wy = self.screen_to_world(event.x, event.y)
            self.drag_state = {
                "id": st["id"],
                "dx": wx - st["x"],
                "dy": wy - st["y"],
                "snap": json.loads(json.dumps(self.m)),
                "moved": False,
            }
        else:
            self.pan_origin = (event.x, event.y, self.vx, self.vy)

    def on_canvas_move(self, event):
        if self.tool == "connect" and self.pending_from:
            self.redraw_canvas(mouse_xy=(event.x, event.y))

    def on_canvas_drag(self, event):
        if self.drag_state:
            wx, wy = self.screen_to_world(event.x, event.y)
            for s in self.m["states"]:
                if s["id"] == self.drag_state["id"]:
                    s["x"] = wx - self.drag_state["dx"]
                    s["y"] = wy - self.drag_state["dy"]
                    self.drag_state["moved"] = True
                    break
            self.redraw_canvas()
        elif self.pan_origin:
            sx, sy, ovx, ovy = self.pan_origin
            self.vx = ovx + (event.x - sx)
            self.vy = ovy + (event.y - sy)
            self.redraw_canvas()

    def on_canvas_up(self, event):
        if self.drag_state:
            if self.drag_state["moved"]:
                self.push_history(self.drag_state["snap"])
            self.drag_state = None
        self.pan_origin = None

    def on_canvas_dblclick(self, event):
        st = self.find_state_at(event.x, event.y)
        if st:
            self.toggle_accept(st["id"])
        else:
            wx, wy = self.screen_to_world(event.x, event.y)
            self.add_state(wx, wy)

    def on_canvas_rightclick(self, event):
        st = self.find_state_at(event.x, event.y)
        menu = tk.Menu(self, tearoff=0)
        if st:
            sid = st["id"]
            menu.add_command(label="Set as start state", command=lambda: self.set_start(sid))
            menu.add_command(label="Toggle accept state", command=lambda: self.toggle_accept(sid))
            menu.add_command(label="Rename state", command=lambda: self.rename_state(sid))
            menu.add_separator()
            menu.add_command(label="Delete state", command=lambda: self.delete_state(sid))
            menu.tk_popup(event.x_root, event.y_root)
            return

        wx, wy = self.screen_to_world(event.x, event.y)
        for e in self.m["edges"]:
            a = next((s for s in self.m["states"] if s["id"] == e["from"]), None)
            b = next((s for s in self.m["states"] if s["id"] == e["to"]), None)
            if not a or not b:
                continue
            rev = e["from"] != e["to"] and any(o["from"] == e["to"] and o["to"] == e["from"] for o in self.m["edges"])
            _, _, _, _, lx, ly = self.edge_geometry(e, a, b, rev)
            if math.hypot(wx - lx, wy - ly) <= 24:
                eid = e["id"]
                menu.add_command(label="Edit transition symbols", command=lambda: self.edit_edge(eid))
                menu.add_command(label="Delete transition", command=lambda: self.delete_edge(eid))
                menu.tk_popup(event.x_root, event.y_root)
                return

    def next_state_name(self):
        i = 0
        existing = {s["name"] for s in self.m["states"]} | {s["id"] for s in self.m["states"]}
        while f"q{i}" in existing:
            i += 1
        return f"q{i}"

    def add_state_random(self):
        wx, wy = self.screen_to_world(140 + random.randint(0, 340), 120 + random.randint(0, 240))
        self.add_state(wx, wy)

    def add_state(self, wx, wy):
        self.push_history()
        name = self.next_state_name()
        self.m["states"].append({"id": name, "name": name, "x": wx, "y": wy})
        if self.m["start"] is None:
            self.m["start"] = name
        self.refresh_all()

    def complete_with_trap_state(self):
        if not self.m["states"]:
            messagebox.showinfo("No States", "Add at least one state before completing the DFA.")
            return
        alpha = self.get_alphabet()
        if not alpha:
            messagebox.showinfo("Empty Alphabet", "Add at least one transition symbol (Σ) first.")
            return

        missing = []
        for s in self.m["states"]:
            for sym in alpha:
                if len(delta_targets(self.m, s["id"], sym)) == 0:
                    missing.append((s["id"], sym))

        if not missing:
            messagebox.showinfo("Already Complete", "Every state already has outgoing transitions for all symbols in Σ.")
            return

        self.push_history()

        trap_state = next(
            (s for s in self.m["states"] if s["name"].lower() in ("q_dead", "dead", "trap", "q_trap")), None
        )
        if trap_state is None:
            existing_ids = {s["id"] for s in self.m["states"]} | {s["name"] for s in self.m["states"]}
            trap_name = "q_dead"
            idx = 1
            while trap_name in existing_ids:
                trap_name = f"q_dead{idx}"
                idx += 1

            avg_x = sum(s["x"] for s in self.m["states"]) / len(self.m["states"])
            max_y = max(s["y"] for s in self.m["states"])
            trap_state = {"id": trap_name, "name": trap_name, "x": avg_x, "y": max_y + 130.0}
            self.m["states"].append(trap_state)
            for sym in alpha:
                missing.append((trap_state["id"], sym))
        else:
            for sym in alpha:
                if len(delta_targets(self.m, trap_state["id"], sym)) == 0 and (trap_state["id"], sym) not in missing:
                    missing.append((trap_state["id"], sym))

        trap_id = trap_state["id"]
        for src_id, sym in missing:
            ex = next((e for e in self.m["edges"] if e["from"] == src_id and e["to"] == trap_id), None)
            if ex:
                if sym not in ex["syms"]:
                    ex["syms"].append(sym)
            else:
                self.edge_counter += 1
                self.m["edges"].append({"id": f"e{self.edge_counter}", "from": src_id, "to": trap_id, "syms": [sym]})

        self.reset_sim()
        self.refresh_all()
        self.fit_view()

    def set_start(self, sid):
        self.push_history()
        self.m["start"] = sid
        self.reset_sim()
        self.refresh_all()

    def toggle_accept(self, sid):
        self.push_history()
        if sid in self.m["acc"]:
            self.m["acc"].remove(sid)
        else:
            self.m["acc"].append(sid)
        self.refresh_all()

    def rename_state(self, sid):
        cur = state_name(self.m, sid)
        new_name = simpledialog.askstring("Rename State", f"New name for '{cur}':", initialvalue=cur, parent=self)
        if not new_name:
            return
        new_name = new_name.strip()
        if not new_name:
            return
        if any(s["id"] != sid and s["name"] == new_name for s in self.m["states"]):
            messagebox.showerror("Duplicate Name", f"A state named '{new_name}' already exists.")
            return
        self.push_history()
        for s in self.m["states"]:
            if s["id"] == sid:
                s["name"] = new_name
        self.refresh_all()

    def delete_state(self, sid):
        self.push_history()
        self.m["states"] = [s for s in self.m["states"] if s["id"] != sid]
        self.m["edges"] = [e for e in self.m["edges"] if e["from"] != sid and e["to"] != sid]
        if self.m["start"] == sid:
            self.m["start"] = None
        self.m["acc"] = [a for a in self.m["acc"] if a != sid]
        self.reset_sim()
        self.refresh_all()

    def prompt_new_edge(self, src, dst):
        raw = simpledialog.askstring(
            "Add Transition",
            f"Input symbols for {state_name(self.m, src)} → {state_name(self.m, dst)} (comma-separated):",
            initialvalue="0, 1",
            parent=self,
        )
        if raw is None:
            return
        syms = parse_syms(raw)
        if not syms:
            return
        self.push_history()
        ex = next((e for e in self.m["edges"] if e["from"] == src and e["to"] == dst), None)
        if ex:
            for c in syms:
                if c not in ex["syms"]:
                    ex["syms"].append(c)
        else:
            self.edge_counter += 1
            self.m["edges"].append({"id": f"e{self.edge_counter}", "from": src, "to": dst, "syms": syms})
        self.reset_sim()
        self.refresh_all()

    def edit_edge(self, eid):
        edge = next((e for e in self.m["edges"] if e["id"] == eid), None)
        if not edge:
            return
        raw = simpledialog.askstring(
            "Edit Transition",
            f"Symbols for {state_name(self.m, edge['from'])} → {state_name(self.m, edge['to'])}:",
            initialvalue=", ".join(edge["syms"]),
            parent=self,
        )
        if raw is None:
            return
        syms = parse_syms(raw)
        self.push_history()
        if not syms:
            self.m["edges"] = [e for e in self.m["edges"] if e["id"] != eid]
        else:
            edge["syms"] = syms
        self.reset_sim()
        self.refresh_all()

    def delete_edge(self, eid):
        self.push_history()
        self.m["edges"] = [e for e in self.m["edges"] if e["id"] != eid]
        self.reset_sim()
        self.refresh_all()

    def clear_all(self):
        self.push_history()
        self.m = {"states": [], "edges": [], "start": None, "acc": []}
        self.extra_alpha = []
        self.vx, self.vy, self.vk = 0.0, 0.0, 1.0
        self.reset_sim()
        self.refresh_all()

    def add_symbol(self):
        syms = parse_syms(self.add_sym_var.get())
        if syms:
            for c in syms:
                if c not in self.extra_alpha:
                    self.extra_alpha.append(c)
            self.add_sym_var.set("")
            self.refresh_all()

    def get_alphabet(self):
        syms = set(self.extra_alpha)
        for e in self.m["edges"]:
            syms.update(e["syms"])
        return sorted(syms)

    def validate_dfa(self):
        alpha = self.get_alphabet()
        issues = []
        bad_states = set()
        if not self.m["states"]:
            issues.append("No states defined")
        elif not self.m["start"]:
            issues.append("Missing start state")
        for s in self.m["states"]:
            for a in alpha:
                t = delta_targets(self.m, s["id"], a)
                if len(t) == 0:
                    issues.append(f"Missing transition: δ({s['name']}, {a})")
                    bad_states.add(s["id"])
                elif len(t) > 1:
                    t_names = ", ".join(state_name(self.m, x) for x in t)
                    issues.append(f"Non-deterministic: δ({s['name']}, {a}) → {{{t_names}}}")
                    bad_states.add(s["id"])
        return issues, bad_states

    def edge_geometry(self, e, a, b, rev):
        if e["from"] == e["to"]:
            pts = [
                (a["x"] - 12, a["y"] - R + 2),
                (a["x"] - 36, a["y"] - R - 46),
                (a["x"] + 36, a["y"] - R - 46),
                (a["x"] + 12, a["y"] - R + 2),
            ]
            return "loop", pts, a["x"] + 12, a["y"] - R + 2, a["x"], a["y"] - R - 44

        dx, dy = b["x"] - a["x"], b["y"] - a["y"]
        dist = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / dist, dx / dist
        offset = 32.0 if rev else 0.0
        cx = (a["x"] + b["x"]) / 2 + nx * offset * 2
        cy = (a["y"] + b["y"]) / 2 + ny * offset * 2

        da = math.hypot(cx - a["x"], cy - a["y"]) or 1.0
        db = math.hypot(cx - b["x"], cy - b["y"]) or 1.0
        sx = a["x"] + (cx - a["x"]) / da * R
        sy = a["y"] + (cy - a["y"]) / da * R
        ex = b["x"] + (cx - b["x"]) / db * (R + 2)
        ey = b["y"] + (cy - b["y"]) / db * (R + 2)

        lx = 0.25 * sx + 0.5 * cx + 0.25 * ex + nx * 13
        ly = 0.25 * sy + 0.5 * cy + 0.25 * ey + ny * 13
        return "quad", [(sx, sy), (cx, cy), (ex, ey)], ex, ey, lx, ly

    def redraw_canvas(self, mouse_xy=None):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()

        step = max(14, int(24 * self.vk))
        ox = int(self.vx) % step
        oy = int(self.vy) % step
        for gx in range(ox, w, step):
            for gy in range(oy, h, step):
                c.create_oval(gx - 1, gy - 1, gx + 1, gy + 1, fill="#cbd5e1", outline="")

        run = simulate_dfa(self.m, self.input_var.get())
        active_state = self.m["start"] if self.step_idx == 0 else run["tr"][self.step_idx - 1]["to"]
        active_edge = run["tr"][self.step_idx - 1]["edge"] if self.step_idx > 0 else None
        _, bad_states = self.validate_dfa()

        for e in self.m["edges"]:
            a = next((s for s in self.m["states"] if s["id"] == e["from"]), None)
            b = next((s for s in self.m["states"] if s["id"] == e["to"]), None)
            if not a or not b:
                continue
            rev = e["from"] != e["to"] and any(o["from"] == e["to"] and o["to"] == e["from"] for o in self.m["edges"])
            kind, pts, ex, ey, lx, ly = self.edge_geometry(e, a, b, rev)
            is_on = e["id"] == active_edge
            color = "#ea580c" if is_on else "#475569"
            width = 3.0 if is_on else 2.0

            s_pts = [self.world_to_screen(px, py) for px, py in pts]
            flat = [coord for pt in s_pts for coord in pt]
            c.create_line(*flat, smooth=True, fill=color, width=width, arrow="last", arrowshape=(10, 12, 5))

            slx, sly = self.world_to_screen(lx, ly)
            lbl_text = ",".join(e["syms"])
            font_sz = max(8, int(10 * self.vk))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                c.create_text(slx + dx, sly + dy, text=lbl_text, fill="white", font=("Segoe UI", font_sz, "bold"))
            c.create_text(
                slx, sly, text=lbl_text, fill="#c2410c" if is_on else "#0f172a", font=("Segoe UI", font_sz, "bold")
            )

        if self.pending_from and mouse_xy:
            src = next((s for s in self.m["states"] if s["id"] == self.pending_from), None)
            if src:
                sx, sy = self.world_to_screen(src["x"], src["y"])
                c.create_line(sx, sy, mouse_xy[0], mouse_xy[1], fill="#6366f1", width=2, dash=(5, 4))

        sr = R * self.vk
        for s in self.m["states"]:
            sx, sy = self.world_to_screen(s["x"], s["y"])
            is_active = s["id"] == active_state
            is_acc = s["id"] in self.m["acc"]

            if self.m["start"] == s["id"]:
                c.create_line(
                    sx - sr - 30 * self.vk,
                    sy,
                    sx - sr - 2,
                    sy,
                    fill="#475569",
                    width=2,
                    arrow="last",
                    arrowshape=(9, 11, 5),
                )

            if s["id"] in bad_states:
                c.create_oval(
                    sx - sr - 5, sy - sr - 5, sx + sr + 5, sy + sr + 5, outline="#ef4444", width=2, dash=(4, 3)
                )

            fill = "#fed7aa" if is_active else ("#e0e7ff" if self.pending_from == s["id"] else "#ffffff")
            outline = "#ea580c" if is_active else "#334155"
            c.create_oval(sx - sr, sy - sr, sx + sr, sy + sr, fill=fill, outline=outline, width=3 if is_active else 2)

            if is_acc:
                ir = max(4, sr - 5 * self.vk)
                c.create_oval(sx - ir, sy - ir, sx + ir, sy + ir, outline=outline, width=2)

            c.create_text(
                sx, sy, text=s["name"], fill="#0f172a", font=("Segoe UI", max(8, int(11 * self.vk)), "bold")
            )

    def refresh_simulation_ui(self):
        run = simulate_dfa(self.m, self.input_var.get())
        total = len(run["tr"])
        if self.step_idx > total:
            self.step_idx = total
        done = self.step_idx >= total and (bool(run["dead"]) or total == len(run["chars"]))

        self.btn_back.config(state="normal" if self.step_idx > 0 else "disabled")
        self.btn_fwd.config(state="normal" if self.step_idx < total else "disabled")

        tc = self.tape_canvas
        tc.delete("all")
        chars = run["chars"]
        if not chars:
            tc.create_text(10, 26, text="ε (empty string)", anchor="w", fill="#94a3b8", font=("Segoe UI", 10, "italic"))
        else:
            x = 6
            for i, ch in enumerate(chars):
                if i < self.step_idx:
                    bg, bd, fg = "#e2e8f0", "#cbd5e1", "#94a3b8"
                elif i == self.step_idx:
                    if run["dead"] and self.step_idx == total:
                        bg, bd, fg = "#fee2e2", "#ef4444", "#b91c1c"
                    else:
                        bg, bd, fg = "#fef3c7", "#f59e0b", "#92400e"
                else:
                    bg, bd, fg = "#ffffff", "#cbd5e1", "#0f172a"
                tc.create_rectangle(x, 6, x + 36, 46, fill=bg, outline=bd, width=2)
                tc.create_text(x + 18, 26, text=ch, fill=fg, font=("Consolas", 13, "bold"))
                x += 42

        start_nm = state_name(self.m, self.m["start"]) if self.m["start"] else "—"
        steps_str = "".join(f" --({t['ch']})--> {state_name(self.m, t['to'])}" for t in run["tr"][: self.step_idx])
        self.trace_lbl.config(text=start_nm + steps_str)

        active = self.m["start"] if self.step_idx == 0 else run["tr"][self.step_idx - 1]["to"]
        if done:
            if run["acc"]:
                self.verdict_lbl.config(
                    text=f"ACCEPTED — Ended in accept state {state_name(self.m, active)}", bg="#dcfce7", fg="#166534"
                )
            else:
                reason = run["dead"] if run["dead"] else f"Ended in non-accepting state {state_name(self.m, active)}"
                self.verdict_lbl.config(text=f"REJECTED — {reason}", bg="#fee2e2", fg="#991b1b")
        else:
            self.verdict_lbl.config(text="", bg="white")

    def refresh_definition_and_table(self):
        alpha = self.get_alphabet()
        q_str = ", ".join(s["name"] for s in self.m["states"])
        s_str = ", ".join(alpha)
        q0_str = state_name(self.m, self.m["start"]) if self.m["start"] else "undefined"
        f_str = ", ".join(state_name(self.m, a) for a in self.m["acc"])

        self.formal_lbl.config(
            text=f"M = (Q, Σ, δ, q₀, F)\nQ  = {{{q_str}}}\nΣ  = {{{s_str}}}\nq₀ = {q0_str}\nF  = {{{f_str}}}"
        )

        issues, _ = self.validate_dfa()
        if issues:
            preview = "\n".join(f"• {x}" for x in issues[:6])
            if len(issues) > 6:
                preview += f"\n• ...and {len(issues) - 6} more"
            self.status_lbl.config(text=f"{len(issues)} issue(s):\n{preview}", bg="#fef2f2", fg="#991b1b")
        else:
            self.status_lbl.config(text="✓ Valid complete DFA", bg="#f0fdf4", fg="#166534")

        for w in self.tbl_inner.winfo_children():
            w.destroy()

        if not self.m["states"]:
            tk.Label(
                self.tbl_inner, text="Double-click the canvas to add a state.", bg="white", fg="#94a3b8", pady=8
            ).grid(row=0, column=0)
            return

        headers = ["Start", "Acc", "State (click to rename)"] + alpha
        for col, h_text in enumerate(headers):
            tk.Label(self.tbl_inner, text=h_text, font=("Segoe UI", 8, "bold"), bg="white", fg="#64748b", padx=6).grid(
                row=0, column=col, pady=(0, 4)
            )

        state_names = [s["name"] for s in self.m["states"]]

        for row_idx, s in enumerate(self.m["states"], start=1):
            sid = s["id"]
            is_start = self.m["start"] == sid
            rb = tk.Radiobutton(
                self.tbl_inner,
                value=sid,
                variable=tk.StringVar(value=self.m["start"] or ""),
                command=lambda x=sid: self.set_start(x),
                bg="white",
            )
            if is_start:
                rb.select()
            rb.grid(row=row_idx, column=0)

            acc_var = tk.BooleanVar(value=(sid in self.m["acc"]))
            tk.Checkbutton(
                self.tbl_inner, variable=acc_var, command=lambda x=sid: self.toggle_accept(x), bg="white"
            ).grid(row=row_idx, column=1)

            name_btn = tk.Button(
                self.tbl_inner,
                text=f"{s['name']} ✎",
                font=("Consolas", 10, "bold"),
                bg="#f8fafc",
                fg="#0f172a",
                relief="groove",
                padx=6,
                cursor="hand2",
                command=lambda x=sid: self.rename_state(x),
            )
            name_btn.grid(row=row_idx, column=2, sticky="w", padx=4, pady=2)

            for col_idx, sym in enumerate(alpha, start=3):
                targets = delta_targets(self.m, sid, sym)
                if len(targets) == 0:
                    cur_val = "—"
                elif len(targets) == 1:
                    cur_val = state_name(self.m, targets[0])
                else:
                    cur_val = ",".join(state_name(self.m, t) for t in targets) + " ⚠"

                cb = ttk.Combobox(self.tbl_inner, values=["—"] + state_names, width=7, state="readonly")
                cb.set(cur_val)
                cb.grid(row=row_idx, column=col_idx, padx=3, pady=2)
                cb.bind(
                    "<<ComboboxSelected>>",
                    lambda e, st_id=sid, a_sym=sym, box=cb: self.on_table_cell_change(st_id, a_sym, box.get()),
                )

    def on_table_cell_change(self, state_id, sym, selected_name):
        self.push_history()
        new_edges = []
        for e in self.m["edges"]:
            if e["from"] == state_id:
                rem = [x for x in e["syms"] if x != sym]
                if rem:
                    e["syms"] = rem
                    new_edges.append(e)
            else:
                new_edges.append(e)
        self.m["edges"] = new_edges

        if selected_name and selected_name != "—":
            target_st = next((s for s in self.m["states"] if s["name"] == selected_name), None)
            if target_st:
                ex = next((e for e in self.m["edges"] if e["from"] == state_id and e["to"] == target_st["id"]), None)
                if ex:
                    ex["syms"].append(sym)
                else:
                    self.edge_counter += 1
                    self.m["edges"].append(
                        {"id": f"e{self.edge_counter}", "from": state_id, "to": target_st["id"], "syms": [sym]}
                    )

        self.reset_sim()
        self.refresh_all()

    def refresh_all(self):
        self.redraw_canvas()
        self.refresh_simulation_ui()
        self.refresh_definition_and_table()

    # Simulation Controls
    def step_fwd(self):
        run = simulate_dfa(self.m, self.input_var.get())
        if self.step_idx < len(run["tr"]):
            self.step_idx += 1
            self.redraw_canvas()
            self.refresh_simulation_ui()

    def step_back(self):
        if self.step_idx > 0:
            self.step_idx -= 1
            self.redraw_canvas()
            self.refresh_simulation_ui()

    def reset_sim(self):
        self.playing = False
        if self.play_after_id:
            self.after_cancel(self.play_after_id)
            self.play_after_id = None
        self.btn_play.config(text="▶ Auto-play")
        self.step_idx = 0
        self.redraw_canvas()
        self.refresh_simulation_ui()

    def toggle_play(self):
        if self.playing:
            self.playing = False
            if self.play_after_id:
                self.after_cancel(self.play_after_id)
                self.play_after_id = None
            self.btn_play.config(text="▶ Auto-play")
        else:
            run = simulate_dfa(self.m, self.input_var.get())
            if self.step_idx >= len(run["tr"]):
                self.step_idx = 0
                self.redraw_canvas()
                self.refresh_simulation_ui()
            self.playing = True
            self.btn_play.config(text="⏸ Pause")
            self._auto_tick()

    def _auto_tick(self):
        if not self.playing:
            return
        run = simulate_dfa(self.m, self.input_var.get())
        if self.step_idx < len(run["tr"]):
            self.step_idx += 1
            self.redraw_canvas()
            self.refresh_simulation_ui()
            self.play_after_id = self.after(self.speed_var.get(), self._auto_tick)
        else:
            self.playing = False
            self.btn_play.config(text="▶ Auto-play")

    # Presets, Regex & Batch
    def on_preset_selected(self, event):
        idx = self.preset_cb.current()
        if idx >= 0:
            self.push_history()
            _, sample_in, builder = PRESETS[idx]
            self.m = builder()
            self.extra_alpha = []
            self.input_var.set(sample_in)
            self.reset_sim()
            self.refresh_all()
            self.fit_view()

    def compile_regex(self):
        try:
            dfa, info = regex_to_dfa(self.re_var.get(), self.re_min_var.get(), self.re_plus_var.get())
            self.push_history()
            self.m = dfa
            self.extra_alpha = []
            self.re_msg_lbl.config(text="✓ " + info, fg="#166534")
            self.reset_sim()
            self.refresh_all()
            self.fit_view()
        except Exception as exc:
            self.re_msg_lbl.config(text="✗ " + str(exc), fg="#991b1b")

    def run_batch(self):
        for w in self.batch_list_frame.winfo_children():
            w.destroy()

        lines = [l for l in self.batch_text.get("1.0", "end").splitlines() if l.strip()]
        acc_cnt = rej_cnt = pass_cnt = fail_cnt = 0

        for line in lines:
            mt = re.match(r"^(.*?)\s*:\s*(accept|reject)\s*$", line, re.IGNORECASE)
            raw = (mt.group(1) if mt else line).strip()
            test_str = "" if raw == "ε" else raw
            res = simulate_dfa(self.m, test_str)
            exp = (mt.group(2).lower() == "accept") if mt else None

            if res["acc"]:
                acc_cnt += 1
            else:
                rej_cnt += 1
            passed = None if exp is None else (exp == res["acc"])
            if passed is True:
                pass_cnt += 1
            elif passed is False:
                fail_cnt += 1

            row = tk.Frame(self.batch_list_frame, bg="#f8fafc", bd=1, relief="solid", padx=6, pady=3)
            row.pack(fill="x", pady=2)
            disp = raw if raw else "ε"
            lbl = tk.Label(row, text=disp, font=("Consolas", 9), bg="#f8fafc", anchor="w", cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True)
            lbl.bind("<Button-1>", lambda e, s=test_str: self.input_var.set(s))

            if passed is not None:
                p_bg = "#16a34a" if passed else "#dc2626"
                tk.Label(row, text="PASS" if passed else "FAIL", font=("Segoe UI", 7, "bold"), bg=p_bg, fg="white", padx=5).pack(
                    side="right", padx=2
                )

            v_bg = "#dcfce7" if res["acc"] else "#fee2e2"
            v_fg = "#166534" if res["acc"] else "#991b1b"
            tk.Label(
                row, text="ACCEPT" if res["acc"] else "REJECT", font=("Segoe UI", 7, "bold"), bg=v_bg, fg=v_fg, padx=5
            ).pack(side="right", padx=2)

        summary = f"{acc_cnt} accepted · {rej_cnt} rejected"
        if pass_cnt + fail_cnt > 0:
            summary += f" · {pass_cnt} pass / {fail_cnt} fail"
        self.batch_summary_lbl.config(text=summary)


if __name__ == "__main__":
    app = DFASimulatorApp()
    app.mainloop()