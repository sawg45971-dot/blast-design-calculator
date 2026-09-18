# gui_app.py — Tkinter GUI: 7-tab dark-theme blast design interface
# Requires: blast_engine.py, report_gen.py, matplotlib

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
from blast_engine import (
    BlastDesignEngine, BlastInputs, BlastResults,
    ROCK_PRESETS, EXPLOSIVE_PRESETS,
)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from report_gen import generate_pdf_report, generate_excel_report
    HAS_REPORT = True
except ImportError:
    HAS_REPORT = False


# ── Colour Tokens ──────────────────────────────────────────────────────────
T = {
    "bg":       "#1a1a2e",
    "panel":    "#16213e",
    "accent":   "#0f3460",
    "hl":       "#e94560",
    "text":     "#eaeaea",
    "text2":    "#8888aa",
    "entry":    "#0a1628",
    "green":    "#00d084",
    "yellow":   "#f6c90e",
}
ROW_COLORS = ["#e94560","#00d084","#f6c90e","#8855ee","#55aaff","#ff9944"]


class BlastCalculatorApp:

    def __init__(self, root: tk.Tk):
        self.root    = root
        self.engine  = BlastDesignEngine()
        self.inputs  = BlastInputs()
        self.results: Optional[BlastResults] = None
        self._vars:   dict = {}

        root.title("⚡ Advanced Blast Design Calculator v2.0")
        root.geometry("1300x800")
        root.configure(bg=T["bg"])
        root.minsize(1100, 700)

        self._style()
        self._header()

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._tab_inputs()
        self._tab_results()
        self._tab_pattern()
        self._tab_fragmentation()
        self._tab_vibration()
        self._tab_cost()
        self._tab_report()

    # ── Style ──────────────────────────────────────────────────────────────

    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TNotebook",     background=T["bg"],    borderwidth=0)
        s.configure("TNotebook.Tab", background=T["accent"], foreground=T["text"],
                    padding=[12, 6], font=("Segoe UI", 9, "bold"))
        s.map("TNotebook.Tab",
              background=[("selected", T["hl"])],
              foreground=[("selected", "white")])
        s.configure("TFrame",  background=T["panel"])
        s.configure("TLabel",  background=T["panel"], foreground=T["text"],
                    font=("Segoe UI", 9))
        s.configure("TScrollbar", background=T["accent"])

    def _header(self):
        h = tk.Frame(self.root, bg=T["accent"], height=52)
        h.pack(fill=tk.X)
        tk.Label(h, text="⚡  ADVANCED BLAST DESIGN CALCULATOR",
                 bg=T["accent"], fg=T["hl"],
                 font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(h, text="Kuz-Ram · Langefors-Kihlstrom · ISEE PPV · Open-Pit Edition",
                 bg=T["accent"], fg=T["text2"],
                 font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=20)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _section(self, parent, title):
        tk.Label(parent, text=title, bg=T["panel"], fg=T["hl"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 2))
        tk.Frame(parent, bg=T["hl"], height=1).pack(fill=tk.X, pady=(0, 4))

    def _entry(self, parent, label, key, default):
        f = tk.Frame(parent, bg=T["panel"])
        f.pack(fill=tk.X, pady=2)
        tk.Label(f, text=label, bg=T["panel"], fg=T["text"],
                 font=("Segoe UI", 9), width=24, anchor="w").pack(side=tk.LEFT)
        var = tk.StringVar(value=str(default))
        self._vars[key] = var
        tk.Entry(f, textvariable=var, width=11,
                 bg=T["entry"], fg=T["text"],
                 insertbackground=T["text"],
                 relief=tk.FLAT, bd=3).pack(side=tk.LEFT, padx=4)

    def _combo(self, parent, label, key, values, cb=None):
        f = tk.Frame(parent, bg=T["panel"])
        f.pack(fill=tk.X, pady=2)
        tk.Label(f, text=label, bg=T["panel"], fg=T["text"],
                 font=("Segoe UI", 9), width=24, anchor="w").pack(side=tk.LEFT)
        var = tk.StringVar(value=values[0])
        self._vars[key] = var
        w = ttk.Combobox(f, textvariable=var, values=values, width=24, state="readonly")
        w.pack(side=tk.LEFT, padx=4)
        if cb:
            w.bind("<<ComboboxSelected>>", cb)

    def _scrollable(self, parent):
        """Returns a scrollable inner frame."""
        c = tk.Canvas(parent, bg=T["panel"], highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=c.yview)
        inner = tk.Frame(c, bg=T["panel"])
        inner.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))
        c.create_window((0, 0), window=inner, anchor="nw")
        c.configure(yscrollcommand=sb.set)
        c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        return inner

    def _embed_figure(self, parent, fig):
        """Embed a matplotlib Figure in a tk parent widget."""
        for w in parent.winfo_children():
            w.destroy()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        NavigationToolbar2Tk(canvas, parent)

    # ── Preset Callbacks ───────────────────────────────────────────────────

    def _on_rock(self, _=None):
        rock = self._vars["rock_type"].get()
        if rock in ROCK_PRESETS:
            p = ROCK_PRESETS[rock]
            self._vars["rock_density"].set(str(p["density"]))
            self._vars["ucs"].set(str(p["ucs"]))
            self._vars["rock_factor"].set(str(p["rock_factor"]))

    def _on_explo(self, _=None):
        ex = self._vars["explosive_type"].get()
        if ex in EXPLOSIVE_PRESETS:
            p = EXPLOSIVE_PRESETS[ex]
            self._vars["explosive_density"].set(str(p["density"]))
            self._vars["rws"].set(str(p["rws"]))
            self._vars["rwb"].set(str(p["rwb"]))
            self._vars["vod"].set(str(p["vod"]))

    # ── Tab 1: Inputs ──────────────────────────────────────────────────────

    def _tab_inputs(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="⚙ Parameters")
        inner = self._scrollable(frame)

        c1 = tk.Frame(inner, bg=T["panel"])
        c2 = tk.Frame(inner, bg=T["panel"])
        c3 = tk.Frame(inner, bg=T["panel"])
        c1.grid(row=0, column=0, padx=12, pady=8, sticky="n")
        c2.grid(row=0, column=1, padx=12, pady=8, sticky="n")
        c3.grid(row=0, column=2, padx=12, pady=8, sticky="n")

        # Column 1 — Geometry & Rock
        self._section(c1, "📐 Bench Geometry")
        self._entry(c1, "Bench Height (m)",        "bench_height",  10.0)
        self._entry(c1, "Hole Diameter (mm)",       "hole_diameter", 115.0)
        self._entry(c1, "Drill Angle (°)",          "drill_angle",   90.0)
        self._entry(c1, "Number of Rows",           "num_rows",      3)
        self._entry(c1, "Holes per Row",            "holes_per_row", 6)

        self._section(c1, "🪨 Rock Properties")
        self._combo(c1, "Rock Type", "rock_type", list(ROCK_PRESETS.keys()), self._on_rock)
        self._entry(c1, "Rock Density (t/m³)",      "rock_density",  2.30)
        self._entry(c1, "UCS (MPa)",                "ucs",           80.0)
        self._entry(c1, "Rock Factor A (Kuz-Ram)",  "rock_factor",   7.0)

        # Column 2 — Explosive & Design Factors
        self._section(c2, "💥 Explosive Properties")
        self._combo(c2, "Explosive Type", "explosive_type",
                    list(EXPLOSIVE_PRESETS.keys()), self._on_explo)
        self._entry(c2, "Density (g/cm³)",          "explosive_density", 0.85)
        self._entry(c2, "Rel. Weight Strength",     "rws",           100.0)
        self._entry(c2, "Rel. Bulk Strength",       "rwb",           100.0)
        self._entry(c2, "VOD (m/s)",                "vod",           4500.0)

        self._section(c2, "📏 Design Factors")
        self._entry(c2, "Burden Factor Kb",         "burden_factor",      30.0)
        self._entry(c2, "Spacing Ratio S/B",        "spacing_ratio",      1.15)
        self._entry(c2, "Stemming Factor Kt",       "stemming_factor",    0.70)
        self._entry(c2, "Subdrill Factor Kj",       "subdrill_factor",    0.25)
        self._entry(c2, "Deck Charge Factor",       "charge_deck_factor", 1.00)

        # Column 3 — Vibration & Cost
        self._section(c3, "📡 Ground Vibration (ISEE)")
        self._entry(c3, "Site Constant K",          "site_constant_k",     160.0)
        self._entry(c3, "Site Exponent α",          "site_constant_alpha", -1.60)
        self._entry(c3, "Max PPV Limit (mm/s)",     "max_ppv_limit",       5.0)

        self._section(c3, "💰 Cost Parameters (USD)")
        self._entry(c3, "Explosive ($/kg)",         "explosive_cost_per_kg",    1.20)
        self._entry(c3, "Drilling ($/m)",           "drilling_cost_per_m",      8.00)
        self._entry(c3, "Initiation ($/hole)",      "initiation_cost_per_hole", 3.50)
        self._entry(c3, "Labour ($/blast)",         "labour_cost_per_blast",    500.0)

        # CALCULATE button
        btn_row = tk.Frame(inner, bg=T["panel"])
        btn_row.grid(row=1, column=0, columnspan=3, pady=18)
        tk.Button(
            btn_row,
            text="⚡   CALCULATE BLAST DESIGN",
            command=self._calculate,
            bg=T["hl"], fg="white",
            font=("Segoe UI", 13, "bold"),
            padx=35, pady=12,
            relief=tk.FLAT, cursor="hand2",
            activebackground="#c23050", activeforeground="white",
        ).pack()

    def _get_inputs(self) -> BlastInputs:
        inp = BlastInputs()
        for key, var in self._vars.items():
            val = var.get()
            if not hasattr(inp, key):
                continue
            try:
                t = type(getattr(inp, key))
                setattr(inp, key, int(float(val)) if t == int else
                                   float(val)     if t == float else val)
            except (ValueError, TypeError):
                pass
        return inp

    def _calculate(self):
        try:
            inp     = self._get_inputs()
            results = self.engine.calculate(inp)
            self.inputs  = inp
            self.results = results
            self._show_results(results)
            self._draw_all(inp, results)
            self.nb.select(1)
            if results.warnings:
                messagebox.showwarning(
                    "⚠ Design Warnings",
                    "\n".join(f"• {w}" for w in results.warnings)
                )
        except Exception as e:
            messagebox.showerror("Calculation Error", str(e))

    # ── Tab 2: Results ─────────────────────────────────────────────────────

    def _tab_results(self):
        self._res_frame = ttk.Frame(self.nb)
        self.nb.add(self._res_frame, text="📊 Results")
        tk.Label(self._res_frame,
                 text="Run calculation first  (⚙ Parameters → CALCULATE)",
                 bg=T["panel"], fg=T["text2"],
                 font=("Segoe UI", 11)).pack(expand=True)

    def _show_results(self, r: BlastResults):
        for w in self._res_frame.winfo_children():
            w.destroy()
        inner = self._scrollable(self._res_frame)

        sections = [
            ("📐 Primary Design", [
                ("Burden (B)",             f"{r.burden:.3f} m",            T["green"]),
                ("Spacing (S)",            f"{r.spacing:.3f} m",           T["green"]),
                ("Stemming (T)",           f"{r.stemming:.3f} m",          T["text"]),
                ("Subdrill (J)",           f"{r.subdrill:.3f} m",          T["text"]),
                ("Hole Depth (HD)",        f"{r.hole_depth:.3f} m",        T["text"]),
                ("Charge Length (Lc)",     f"{r.charge_length:.3f} m",     T["text"]),
                ("Langefors Burden (ref)", f"{r.langefors_burden:.3f} m",  T["yellow"]),
            ]),
            ("💥 Explosive & Charge", [
                ("Charge per Hole",        f"{r.charge_per_hole:.2f} kg",  T["green"]),
                ("Linear Charge Density",  f"{r.linear_charge_density:.3f} kg/m", T["text"]),
                ("Borehole Pressure",      f"{r.borehole_pressure:.1f} MPa", T["text"]),
                ("Total Holes",            f"{r.total_holes}",             T["text"]),
                ("Total Drill Meters",     f"{r.total_drill_meters:.1f} m", T["text"]),
                ("Total Explosives",       f"{r.total_explosives:.1f} kg", T["hl"]),
            ]),
            ("⛏ Production", [
                ("Volume per Hole",        f"{r.volume_per_hole:.2f} m³",  T["text"]),
                ("Total Blast Volume",     f"{r.total_volume:.1f} m³",     T["green"]),
                ("Total Tonnage",          f"{r.total_tonnage:.1f} t",     T["green"]),
                ("Powder Factor",          f"{r.powder_factor:.4f} kg/m³", T["yellow"]),
                ("Specific Drilling",      f"{r.specific_drilling:.5f} m/m³", T["text"]),
            ]),
            ("🪨 Fragmentation (Kuz-Ram)", [
                ("Mean Fragment X₅₀",      f"{r.x50:.1f} mm",              T["green"]),
                ("X₈₀ (80% Passing)",      f"{r.x80:.1f} mm",              T["text"]),
                ("X₂₀ (20% Passing)",      f"{r.x20:.1f} mm",              T["text"]),
                ("Uniformity Index (n)",   f"{r.uniformity_index:.3f}",    T["text"]),
                ("Fines < 50 mm",          f"{r.percent_fines:.1f} %",     T["yellow"]),
            ]),
            ("⚠ Safety", [
                ("Flyrock Distance",       f"{r.flyrock_distance:.0f} m",  T["hl"]),
                ("Min Safe Distance",      f"{r.min_safe_distance:.0f} m", T["hl"]),
                ("Critical PPV Distance",  f"{r.critical_distance:.0f} m", T["yellow"]),
                ("Air Blast Zone",         f"{r.airblast_distance:.0f} m", T["text"]),
            ]),
            ("💰 Cost (USD)", [
                ("Drilling Cost",          f"${r.drilling_cost:,.2f}",     T["text"]),
                ("Explosive Cost",         f"${r.explosive_cost_total:,.2f}", T["text"]),
                ("Initiation Cost",        f"${r.initiation_cost:,.2f}",   T["text"]),
                ("Total Blast Cost",       f"${r.total_cost:,.2f}",        T["green"]),
                ("Cost per Tonne",         f"${r.cost_per_tonne:.3f}/t",   T["yellow"]),
                ("Cost per m³",            f"${r.cost_per_m3:.3f}/m³",     T["text"]),
            ]),
        ]

        for sec_title, items in sections:
            tk.Label(inner, text=sec_title, bg=T["panel"], fg=T["hl"],
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(14, 2))
            tk.Frame(inner, bg=T["hl"], height=1).pack(fill=tk.X, padx=20)
            for label, value, color in items:
                row = tk.Frame(inner, bg=T["panel"])
                row.pack(fill=tk.X, padx=20, pady=1)
                tk.Label(row, text=label,  bg=T["panel"], fg=T["text2"],
                         font=("Segoe UI", 9), width=26, anchor="w").pack(side=tk.LEFT)
                tk.Label(row, text=value,  bg=T["panel"], fg=color,
                         font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10)

    # ── Tab 3: Blast Pattern ───────────────────────────────────────────────

    def _tab_pattern(self):
        self._pat_frame = ttk.Frame(self.nb)
        self.nb.add(self._pat_frame, text="🗺 Blast Pattern")

    # ── Tab 4: Fragmentation ───────────────────────────────────────────────

    def _tab_fragmentation(self):
        self._frag_frame = ttk.Frame(self.nb)
        self.nb.add(self._frag_frame, text="🪨 Fragmentation")

    # ── Tab 5: Vibration ───────────────────────────────────────────────────

    def _tab_vibration(self):
        self._vib_frame = ttk.Frame(self.nb)
        self.nb.add(self._vib_frame, text="📡 Vibration")

    # ── Tab 6: Cost ────────────────────────────────────────────────────────

    def _tab_cost(self):
        self._cost_frame = ttk.Frame(self.nb)
        self.nb.add(self._cost_frame, text="💰 Cost")

    # ── Tab 7: Report ──────────────────────────────────────────────────────

    def _tab_report(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="📄 Report")

        tk.Label(frame, text="Export Blast Design Report",
                 bg=T["panel"], fg=T["hl"],
                 font=("Segoe UI", 14, "bold")).pack(pady=25)

        btn = tk.Frame(frame, bg=T["panel"])
        btn.pack()
        tk.Button(btn, text="📄  Export PDF",
                  command=self._pdf,
                  bg=T["hl"], fg="white",
                  font=("Segoe UI", 11, "bold"),
                  padx=22, pady=10,
                  relief=tk.FLAT, cursor="hand2"
                  ).grid(row=0, column=0, padx=12, pady=8)
        tk.Button(btn, text="📊  Export Excel",
                  command=self._excel,
                  bg=T["green"], fg="black",
                  font=("Segoe UI", 11, "bold"),
                  padx=22, pady=10,
                  relief=tk.FLAT, cursor="hand2"
                  ).grid(row=0, column=1, padx=12, pady=8)
        tk.Label(frame,
                 text="PDF: full design report with warnings\n"
                      "Excel: all inputs & outputs in tabular format",
                 bg=T["panel"], fg=T["text2"],
                 font=("Segoe UI", 9), justify="center").pack(pady=10)

    def _pdf(self):
        if not self.results:
            return messagebox.showwarning("No Data", "Run calculation first!")
        if not HAS_REPORT:
            return messagebox.showerror("Missing", "pip install reportlab")
        p = filedialog.asksaveasfilename(defaultextension=".pdf",
                                         filetypes=[("PDF","*.pdf")],
                                         initialfile="blast_report.pdf")
        if p:
            generate_pdf_report(self.inputs, self.results, p)
            messagebox.showinfo("Saved", p)

    def _excel(self):
        if not self.results:
            return messagebox.showwarning("No Data", "Run calculation first!")
        if not HAS_REPORT:
            return messagebox.showerror("Missing", "pip install openpyxl")
        p = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                         filetypes=[("Excel","*.xlsx")],
                                         initialfile="blast_report.xlsx")
        if p:
            generate_excel_report(self.inputs, self.results, p)
            messagebox.showinfo("Saved", p)

    # ── Chart Renderers ────────────────────────────────────────────────────

    def _draw_all(self, inp: BlastInputs, r: BlastResults):
        if not HAS_MPL:
            return
        self._draw_pattern(inp, r)
        self._draw_frag(r)
        self._draw_vib(inp, r)
        self._draw_cost(r)

    def _draw_pattern(self, inp: BlastInputs, r: BlastResults):
        coords = self.engine.blast_pattern_coords(inp, r)
        fig = Figure(figsize=(8, 5), facecolor=T["panel"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(T["bg"])
        for row_n in sorted(set(coords["row"])):
            xs = [coords["x"][i] for i in range(len(coords["x"])) if coords["row"][i] == row_n]
            ys = [coords["y"][i] for i in range(len(coords["y"])) if coords["row"][i] == row_n]
            c  = ROW_COLORS[(row_n - 1) % len(ROW_COLORS)]
            ax.scatter(xs, ys, s=220, color=c, zorder=5,
                       edgecolors="white", linewidths=0.7, label=f"Row {row_n}")
            for x, y in zip(xs, ys):
                ax.annotate(str(row_n), (x, y), ha="center", va="center",
                            fontsize=7, color="white", fontweight="bold")
        ax.set_xlabel("Along-row / Spacing direction (m)", color=T["text"])
        ax.set_ylabel("Across-row / Burden direction (m)",  color=T["text"])
        ax.set_title(
            f"Staggered Blast Pattern — B={r.burden:.2f}m  S={r.spacing:.2f}m  "
            f"({inp.num_rows}×{inp.holes_per_row} holes, {r.total_holes} total)",
            color=T["text"], fontsize=10
        )
        ax.tick_params(colors=T["text"])
        for spine in ax.spines.values():
            spine.set_color(T["accent"])
        ax.legend(facecolor=T["accent"], labelcolor=T["text"])
        self._embed_figure(self._pat_frame, fig)

    def _draw_frag(self, r: BlastResults):
        if r.x50 <= 0:
            return
        sizes, passing = self.engine.fragmentation_curve(r.x50, r.uniformity_index)
        fig = Figure(figsize=(8, 5), facecolor=T["panel"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(T["bg"])
        ax.semilogx(sizes, passing, color=T["hl"], lw=2.5, label="Kuz-Ram")
        ax.axvline(r.x50, color=T["green"],  ls="--", lw=1.5, label=f"X₅₀={r.x50:.1f}mm")
        ax.axvline(r.x80, color=T["yellow"], ls="--", lw=1.5, label=f"X₈₀={r.x80:.1f}mm")
        ax.axhline(50,    color=T["green"],  ls=":",  alpha=0.4)
        ax.axhline(80,    color=T["yellow"], ls=":",  alpha=0.4)
        ax.fill_between(sizes, passing, alpha=0.08, color=T["hl"])
        ax.set_xlim(1, 1000); ax.set_ylim(0, 100)
        ax.set_xlabel("Fragment Size (mm)  [log scale]", color=T["text"])
        ax.set_ylabel("Cumulative Passing (%)",           color=T["text"])
        ax.set_title(
            f"Kuz-Ram Fragmentation  "
            f"[A={self.inputs.rock_factor}  n={r.uniformity_index:.2f}  "
            f"PF={r.powder_factor:.3f}kg/m³  Fines<50mm={r.percent_fines:.1f}%]",
            color=T["text"]
        )
        ax.tick_params(colors=T["text"])
        for sp in ax.spines.values(): sp.set_color(T["accent"])
        ax.grid(True, which="both", alpha=0.12, color=T["text2"])
        ax.legend(facecolor=T["accent"], labelcolor=T["text"])
        self._embed_figure(self._frag_frame, fig)

    def _draw_vib(self, inp: BlastInputs, r: BlastResults):
        dists, ppvs = self.engine.ppv_curve(
            r.charge_per_hole, inp.site_constant_k, inp.site_constant_alpha
        )
        fig = Figure(figsize=(8, 5), facecolor=T["panel"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(T["bg"])
        ax.loglog(dists, ppvs, color=T["hl"], lw=2.5, label="PPV Attenuation")
        ax.axhline(inp.max_ppv_limit, color=T["green"], ls="--", lw=1.5,
                   label=f"Limit = {inp.max_ppv_limit} mm/s")
        if r.critical_distance > 0:
            ax.axvline(r.critical_distance, color=T["yellow"], ls="--", lw=1.5,
                       label=f"Critical = {r.critical_distance:.0f}m")
        ax.fill_between(dists, ppvs, inp.max_ppv_limit,
                        where=[p > inp.max_ppv_limit for p in ppvs],
                        alpha=0.15, color=T["hl"], label="Exceedance Zone")
        ax.set_xlabel("Distance from Blast (m)  [log scale]", color=T["text"])
        ax.set_ylabel("PPV (mm/s)  [log scale]",               color=T["text"])
        ax.set_title(
            f"Ground Vibration — ISEE  "
            f"[K={inp.site_constant_k}  α={inp.site_constant_alpha}  "
            f"Q_delay={r.charge_per_hole:.1f}kg]",
            color=T["text"]
        )
        ax.tick_params(colors=T["text"])
        for sp in ax.spines.values(): sp.set_color(T["accent"])
        ax.grid(True, which="both", alpha=0.12)
        ax.legend(facecolor=T["accent"], labelcolor=T["text"])
        self._embed_figure(self._vib_frame, fig)

    def _draw_cost(self, r: BlastResults):
        inp    = self.inputs
        labels = ["Drilling", "Explosives", "Initiation", "Labour"]
        values = [
            r.drilling_cost,
            r.explosive_cost_total,
            r.initiation_cost,
            inp.labour_cost_per_blast,
        ]
        colors = [T["hl"], T["green"], T["yellow"], "#8855ee"]
        fig = Figure(figsize=(7, 5), facecolor=T["panel"])
        ax  = fig.add_subplot(111)
        ax.set_facecolor(T["bg"])
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct="%1.1f%%",
            colors=colors, startangle=140,
            textprops={"color": T["text"], "fontsize": 9},
            wedgeprops={"edgecolor": T["bg"], "linewidth": 2},
        )
        for at in autotexts:
            at.set_color("white"); at.set_fontweight("bold")
        ax.set_title(
            f"Total Cost: ${r.total_cost:,.2f}  |  "
            f"${r.cost_per_tonne:.3f}/tonne  |  "
            f"${r.cost_per_m3:.3f}/m³",
            color=T["text"]
        )
        self._embed_figure(self._cost_frame, fig)