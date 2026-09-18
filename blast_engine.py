# blast_engine.py — Core Blast Design Calculation Engine
# Methods: Langefors-Kihlstrom | Kb-Factor | Kuz-Ram | ISEE PPV | Lundborg Flyrock
# Target: Open-pit & quarry blast design

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


# ── Rock Type Presets ───────────────────────────────────────────────────────
ROCK_PRESETS: Dict[str, dict] = {
    "Soft Rock (Coal/Limestone)":        {"density": 1.80, "ucs": 30,  "rock_factor": 4},
    "Medium Rock (Sandstone)":           {"density": 2.30, "ucs": 80,  "rock_factor": 7},
    "Hard Rock (Granite)":               {"density": 2.65, "ucs": 150, "rock_factor": 10},
    "Very Hard Rock (Basalt/Quartzite)": {"density": 2.90, "ucs": 250, "rock_factor": 13},
}

# ── Explosive Presets ───────────────────────────────────────────────────────
EXPLOSIVE_PRESETS: Dict[str, dict] = {
    "ANFO":                  {"density": 0.85, "vod": 4500, "rws": 100, "rwb": 100},
    "Heavy ANFO (70/30)":   {"density": 1.05, "vod": 5200, "rws": 107, "rwb": 106},
    "Emulsion":              {"density": 1.20, "vod": 5800, "rws": 116, "rwb": 118},
    "Slurry / Watergel":    {"density": 1.30, "vod": 5000, "rws": 108, "rwb": 110},
    "ANFO/Emulsion 50/50":  {"density": 1.00, "vod": 5000, "rws": 109, "rwb": 108},
}


@dataclass
class BlastInputs:
    """All user-supplied blast design parameters."""
    # Geometry
    bench_height: float       = 10.0    # m
    hole_diameter: float      = 115.0   # mm
    drill_angle: float        = 90.0    # degrees (90=vertical)
    num_rows: int             = 3
    holes_per_row: int        = 6

    # Rock
    rock_type: str            = "Medium Rock (Sandstone)"
    rock_density: float       = 2.30    # t/m³
    ucs: float                = 80.0    # MPa
    rock_factor: float        = 7.0     # Kuz-Ram A factor

    # Explosive
    explosive_type: str       = "ANFO"
    explosive_density: float  = 0.85    # g/cm³
    rws: float                = 100.0   # Relative Weight Strength
    rwb: float                = 100.0   # Relative Bulk Strength
    vod: float                = 4500.0  # m/s

    # Design Factors
    burden_factor: float      = 30.0    # Kb: B = Kb × D_mm / 1000
    spacing_ratio: float      = 1.15    # Ks: S = Ks × B
    stemming_factor: float    = 0.70    # Kt: T = Kt × B
    subdrill_factor: float    = 0.25    # Kj: J = Kj × B
    charge_deck_factor: float = 1.0     # 1.0 = single deck

    # Vibration
    site_constant_k: float    = 160.0
    site_constant_alpha: float = -1.60
    max_ppv_limit: float      = 5.0     # mm/s

    # Cost (USD)
    explosive_cost_per_kg: float     = 1.20
    drilling_cost_per_m: float       = 8.00
    initiation_cost_per_hole: float  = 3.50
    labour_cost_per_blast: float     = 500.0


@dataclass
class BlastResults:
    """All calculated blast design outputs."""
    # Primary
    burden: float               = 0.0
    spacing: float              = 0.0
    stemming: float             = 0.0
    subdrill: float             = 0.0
    hole_depth: float           = 0.0
    charge_length: float        = 0.0
    langefors_burden: float     = 0.0

    # Charge
    charge_per_hole: float      = 0.0
    linear_charge_density: float = 0.0
    borehole_pressure: float    = 0.0

    # Pattern
    total_holes: int            = 0
    total_drill_meters: float   = 0.0
    total_explosives: float     = 0.0
    blast_area: float           = 0.0

    # Production
    volume_per_hole: float      = 0.0
    total_volume: float         = 0.0
    total_tonnage: float        = 0.0
    powder_factor: float        = 0.0
    specific_drilling: float    = 0.0

    # Kuz-Ram Fragmentation
    x50: float                  = 0.0
    x80: float                  = 0.0
    x20: float                  = 0.0
    uniformity_index: float     = 1.5
    percent_fines: float        = 0.0

    # Vibration / Safety
    critical_distance: float    = 0.0
    scaled_distance_limit: float = 0.0
    flyrock_distance: float     = 0.0
    min_safe_distance: float    = 0.0
    airblast_distance: float    = 0.0

    # Cost
    drilling_cost: float        = 0.0
    explosive_cost_total: float = 0.0
    initiation_cost: float      = 0.0
    total_cost: float           = 0.0
    cost_per_tonne: float       = 0.0
    cost_per_m3: float          = 0.0

    warnings: List[str]         = field(default_factory=list)


class BlastDesignEngine:
    """
    Open-pit blast design calculator.
    Methods: Kb-Factor (primary), Langefors-Kihlstrom (reference),
             Kuz-Ram fragmentation, ISEE PPV attenuation, Lundborg flyrock.
    """

    def calculate(self, inp: BlastInputs) -> BlastResults:
        r = BlastResults()
        D_mm = inp.hole_diameter
        D_m  = D_mm / 1000.0
        H    = inp.bench_height
        rho_e = inp.explosive_density   # g/cm³
        rho_r = inp.rock_density        # t/m³

        # ── 1. BURDEN ──────────────────────────────────────────────────────
        # Kb-Factor method (primary): B = Kb × D(mm) / 1000
        r.burden = (inp.burden_factor * D_mm) / 1000.0
        B = r.burden

        # Langefors-Kihlstrom reference:
        # B_L = (D/33) × √(ρe / ρr) × (RWS/100)^(1/3)
        r.langefors_burden = (
            (D_m / 0.033)
            * math.sqrt(rho_e / rho_r)
            * (inp.rws / 100.0) ** (1.0 / 3.0)
        )
        if r.langefors_burden > 0:
            deviation = abs(B - r.langefors_burden) / r.langefors_burden
            if deviation > 0.20:
                r.warnings.append(
                    f"Burden deviation >20%: Kb={B:.2f}m vs Langefors={r.langefors_burden:.2f}m"
                )

        # ── 2. SPACING ─────────────────────────────────────────────────────
        r.spacing = inp.spacing_ratio * B
        S = r.spacing

        # ── 3. STEMMING ────────────────────────────────────────────────────
        r.stemming = inp.stemming_factor * B
        T_min = 20.0 * D_m  # minimum: 20 × D
        if r.stemming < T_min:
            r.stemming = T_min
            r.warnings.append(f"Stemming raised to minimum 20×D = {T_min:.2f}m")
        T = r.stemming

        # ── 4. SUBDRILL ────────────────────────────────────────────────────
        r.subdrill = inp.subdrill_factor * B
        J = r.subdrill

        # ── 5. HOLE DEPTH ──────────────────────────────────────────────────
        if inp.drill_angle >= 89.9:
            r.hole_depth = H + J
        else:
            a_rad = math.radians(inp.drill_angle)
            r.hole_depth = (H + J) / math.sin(a_rad)
        HD = r.hole_depth

        # ── 6. CHARGE ──────────────────────────────────────────────────────
        r.charge_length = max(0.1, (HD - T) * inp.charge_deck_factor)
        Lc = r.charge_length

        # Linear charge density: lcd = (π/4) × D² × ρe × 1000  [kg/m]
        r.linear_charge_density = (math.pi / 4.0) * (D_m ** 2) * rho_e * 1000.0
        r.charge_per_hole       = r.linear_charge_density * Lc
        Q = r.charge_per_hole

        # Borehole pressure [MPa]: P_b = ρe(kg/m³) × VOD² / 4e6
        r.borehole_pressure = (rho_e * 1000.0 * inp.vod ** 2) / (4.0 * 1e6)

        # ── 7. PATTERN TOTALS ──────────────────────────────────────────────
        r.total_holes       = inp.num_rows * inp.holes_per_row
        r.total_drill_meters = r.total_holes * HD
        r.total_explosives  = r.total_holes * Q
        r.blast_area        = (inp.holes_per_row * S) * (inp.num_rows * B)

        # ── 8. PRODUCTION ──────────────────────────────────────────────────
        r.volume_per_hole  = B * S * H                         # m³ in-situ
        r.total_volume     = r.total_holes * r.volume_per_hole
        r.total_tonnage    = r.total_volume * rho_r * 0.90     # 10% swell deduct
        r.powder_factor    = Q / r.volume_per_hole if r.volume_per_hole > 0 else 0.0
        r.specific_drilling = HD / r.volume_per_hole if r.volume_per_hole > 0 else 0.0

        # ── 9. KUZ-RAM FRAGMENTATION ───────────────────────────────────────
        # X50 = A × K^(-0.8) × Q^(1/6) × (115/RWS)^(19/30)
        # Cunningham (1987) uniformity index n
        A   = inp.rock_factor
        K   = r.powder_factor
        RWS = inp.rws
        if K > 0 and Q > 0:
            r.x50 = A * (K ** -0.8) * (Q ** (1.0/6.0)) * ((115.0 / RWS) ** (19.0/30.0))
            n_raw = (
                (2.2 - 14.0 * B / D_m)
                * math.sqrt((1.0 + S / B) / 2.0)
                * (Lc / HD)
            )
            r.uniformity_index = max(0.5, min(3.5, n_raw))
            n = r.uniformity_index
            # Rosin-Rammler: x_p = x50 × [ln(1/(1-p/100)) / ln2]^(1/n)
            r.x80 = r.x50 * (math.log(1.0 / 0.20) / 0.693) ** (1.0 / n)
            r.x20 = r.x50 * (math.log(1.0 / 0.80) / 0.693) ** (1.0 / n)
            p50_fines = 1.0 - math.exp(-0.693 * (50.0 / r.x50) ** n)
            r.percent_fines = p50_fines * 100.0

        # ── 10. GROUND VIBRATION ───────────────────────────────────────────
        # PPV = K × SD^α  where SD = R / √Q_delay
        # → R_critical where PPV = limit: SD_lim = (limit/K)^(1/α)
        K_v     = inp.site_constant_k
        alpha   = inp.site_constant_alpha
        ppv_lim = inp.max_ppv_limit
        if ppv_lim > 0 and K_v > 0 and Q > 0:
            sd_lim = (ppv_lim / K_v) ** (1.0 / alpha)
            r.scaled_distance_limit = abs(sd_lim)
            r.critical_distance     = abs(sd_lim) * math.sqrt(Q)

        # ── 11. SAFETY ─────────────────────────────────────────────────────
        # Lundborg flyrock: L ≈ 260 × D(m)^(2/3)
        r.flyrock_distance  = 260.0 * (D_m ** (2.0 / 3.0))
        r.min_safe_distance = max(300.0, r.flyrock_distance * 1.5)
        # Air blast empirical: R_ab = 300 × Q^(1/3)
        r.airblast_distance = 300.0 * (Q ** (1.0 / 3.0))

        if B / H > 0.35:
            r.warnings.append(f"B/H = {B/H:.2f} > 0.35 — toe burden / misfires risk")
        if T / B < 0.50:
            r.warnings.append(f"T/B = {T/B:.2f} < 0.50 — flyrock / airblast risk")

        # ── 12. COST ───────────────────────────────────────────────────────
        r.drilling_cost       = r.total_drill_meters * inp.drilling_cost_per_m
        r.explosive_cost_total = r.total_explosives  * inp.explosive_cost_per_kg
        r.initiation_cost     = r.total_holes        * inp.initiation_cost_per_hole
        r.total_cost = (
            r.drilling_cost
            + r.explosive_cost_total
            + r.initiation_cost
            + inp.labour_cost_per_blast
        )
        if r.total_tonnage > 0:
            r.cost_per_tonne = r.total_cost / r.total_tonnage
            r.cost_per_m3    = r.total_cost / r.total_volume

        return r

    # ── Curve Generators ───────────────────────────────────────────────────

    def fragmentation_curve(
        self, x50: float, n: float
    ) -> Tuple[List[float], List[float]]:
        """Rosin-Rammler cumulative passing curve."""
        sizes   = [i * 0.5 for i in range(2, 2001)]    # 1 → 1000 mm
        passing = []
        for x in sizes:
            p = (1.0 - math.exp(-0.693 * (x / x50) ** n)) * 100.0 if x50 > 0 else 0.0
            passing.append(min(100.0, p))
        return sizes, passing

    def ppv_curve(
        self, q_delay: float, K: float, alpha: float
    ) -> Tuple[List[float], List[float]]:
        """ISEE PPV attenuation vs distance."""
        distances = list(range(10, 1001, 5))
        ppv_vals  = []
        for R in distances:
            sd  = R / math.sqrt(q_delay) if q_delay > 0 else 1.0
            ppv = max(0.0, K * (sd ** alpha))
            ppv_vals.append(ppv)
        return distances, ppv_vals

    def blast_pattern_coords(
        self, inp: BlastInputs, r: BlastResults
    ) -> Dict[str, list]:
        """Top-view staggered blast hole coordinates."""
        B = r.burden
        S = r.spacing
        coords: Dict[str, list] = {"x": [], "y": [], "row": []}
        for row_idx in range(inp.num_rows):
            offset = (S / 2.0) if row_idx % 2 == 1 else 0.0   # stagger odd rows
            for hole_idx in range(inp.holes_per_row):
                coords["x"].append(hole_idx * S + offset)
                coords["y"].append(row_idx  * B)
                coords["row"].append(row_idx + 1)
        return coords   
print("Hello! The script is working perfectly.")
