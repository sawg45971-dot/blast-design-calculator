# ⚡ Advanced Blast Design Calculator

> Open-pit & quarry blast design tool — Kuz-Ram · Langefors-Kihlstrom · ISEE PPV

![Python](https://shields.io)
![License](https://shields.io)
![Mining](https://shields.io)

## Features

| Module | Details |
|--------|---------|
| **Blast Design** | Kb-factor method + Langefors-Kihlstrom verification |
| **Fragmentation** | Kuz-Ram model (Cunningham 1987) — X50, X80, Rosin-Rammler curve |
| **Ground Vibration** | ISEE PPV attenuation — K·SD^α, critical distance |
| **Safety** | Lundborg flyrock, air blast zone, stemming/burden checks |
| **Cost Analysis** | Drilling + explosives + initiation + labour, /tonne, /m³ |
| **Visualisation** | Blast pattern (top view), fragmentation curve, PPV chart, cost pie |
| **Export** | PDF report (reportlab) + Excel workbook (openpyxl) |

## Calculation Methods

- **Burden**: B = Kb × D(mm)/1000  ·  Langefors: B = (D/33)·√(ρₑ/ρᵣ)·(RWS/100)^(1/3)
- **Fragmentation**: X₅₀ = A · K^(-0.8) · Q^(1/6) · (115/RWS)^(19/30)
- **PPV**: PPV = K · (R/√Q)^α  ·  R_critical from regulatory limit
- **Flyrock**: L ≈ 260 · D^(2/3)  [Lundborg 1981]
- **Borehole Pressure**: Pᵦ = ρₑ(kg/m³) · VOD² / 4  [MPa]

## Project Structure

* **`main.py`**: The main application entry point that initializes and orchestrates the application execution loop.
* **`gui_app.py`**: Houses the graphical user interface (GUI) windows, layout forms, event listeners, and data-entry fields.
* **`blast_engine.py`**: The core computational logic engine running the fragmentation, burden formulas, and safety analytics.
* **`report_gen.py`**: Automatically structures and outputs calculations into professional PDF and Excel summaries.

## Installation

```bash
git clone https://github.com/sawg45971-dot/blast-design-calculator.git
cd blast-design-calculator
pip install -r requirements.txt
python main.py
```

## Usage

1. Select rock type preset → auto-fills density, UCS, Kuz-Ram factor.
2. Select explosive preset → auto-fills density, RWS, VOD.
3. Adjust design factors (Kb, spacing ratio, stemming, subdrill).
4. Click **⚡ CALCULATE BLAST DESIGN**.
5. Review metrics and interactive charts across the 7 application tabs.
6. Export custom operational PDF or data-driven Excel sheets directly.
