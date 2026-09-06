# ⚽ FPL Optimizer & Strategic Analytics Dashboard

[![Streamlit](https://img.shields.io/badge/Streamlit-1.42+-FF4B4B.svg?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=for-the-badge&logo=Python&logoColor=white)](https://www.python.org/)
[![PuLP](https://img.shields.io/badge/Optimization-PuLP%20MILP-22c55e.svg?style=for-the-badge)](https://coin-or.github.io/pulp/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57.svg?style=for-the-badge&logo=SQLite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

An enterprise-grade **Fantasy Premier League (FPL) Decision-Support System** that fuses integer linear programming (MILP), Monte Carlo probabilistic simulations, sharp bookmaker betting market odds, and rolling underlying expected metrics ($xG$, $xA$, $xGC$, Defensive Contributions) into an interactive, high-performance web dashboard.

> **TL;DR:** An advanced **FPL Decision Support & Optimization Dashboard** built with Streamlit and SQLite. It combines **PuLP Linear Programming** for optimal transfer and starting XI planning with a **Monte Carlo Match Simulator** to stress-test your squad across thousands of probabilistic outcomes. Featuring 9 specialized modular tabs, real-time live gameweek tracking, and immutable pre-deadline snapshot auditing.

<p>
  <a href="https://fploptimizer.streamlit.app" target="_blank" rel="noopener noreferrer">
    <img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Streamlit App" height="35">
  </a>
</p>
---

## 🚀 Key Features

### 1. 📋 Squad Analyzer & Best 11 Optimizer
* **FPL Account Direct Sync:** Seamlessly integrates with the official FPL API by simply entering your Team ID. Automatically imports your 15-player squad, bank budget, free transfers, and chip statuses.
* **Optimal XI Integer Solver:** Solves the mathematically optimal starting XI and captain for upcoming gameweeks subject to valid FPL formation constraints (min 3 DEF, min 2 MID, min 1 FWD, 1 GKP) using PuLP.
* **Pitch & List View Layouts:** Toggle between a soccer pitch formation view with interactive hover intel ($xGI/90$, 5-GW difficulty, average minutes) and dense, sortable list view cards.
* **Live Match Tracker & Real-Time Scores:** Live tracking during active gameweeks, showing real-time match statuses (`finished`, `live`, `upcoming`), live bonus points, and provisional rank movements.
* **Benchmark Comparisons:** Benchmark your starting XI against the budget-constrained **Dream 11** or unconstrained **Super Team**.
* **Pre-GW Snapshot Locking:** Lock your optimal lineup into the database pre-deadline to audit model projections against actual outcomes.

### 2. 🧠 Transfer Solver & Multi-GW Horizon Planner
* **Multi-Period Mathematical Optimization:** Optimizes multi-gameweek transfer routes across a 1 to 5 gameweek horizon using Mixed Integer Linear Programming (MILP).
* **Transfer Friction & Hit Penalties:** Models free transfer accumulation rules, trade friction, and custom points deduction caps (-4, -8, etc.) to prevent wasteful short-term churn.
* **Tactical Player Locking & Exclusions:** Enforce must-keep squad players or exclude unwanted targets from the solver.
* **Chip Strategy Simulation:** Model Wildcard and Free Hit total squad rebuilds without hit penalties.
* **Betting Market Weighting:** Factor in bookmaker implied odds and sharp line movement into player projected points ($xP$).
* **Direct Lock to Audit Journal:** Lock your planned transfer strategy to bypass delayed midweek FPL API transfer updates.

### 3. 🎲 Monte Carlo Match Simulator & Head-to-Head Testing
* **Stochastic Outcome Modeling:** Runs 1,000 to 10,000 probabilistic match simulations per gameweek to evaluate squad variance, goal distributions, and clean sheet probabilities.
* **Head-to-Head Comparison:** Stress-test your transfer plan or custom squad head-to-head against your current active lineup across the exact same match iterations.
* **Risk & Percentile Analysis:** Quantifies downside floor (10th percentile), median expectation (50th percentile), and ceiling boom potential (90th percentile), alongside head-to-head win percentages.

### 4. 🛠️ Custom 15-Player Sandbox
* **Interactive Filterable Player Pool:** Build hypothetical wildcard squads with search-as-you-type fuzzy player matching and real-time Premier League player photos.
* **Live Constraint Enforcement:** Strict real-time verification of FPL squad rules:
  * Budget cap tracking (£100.0m default or custom team value)
  * Positional quotas (2 GKP, 5 DEF, 5 MID, 3 FWD)
  * Maximum 3 players per Premier League club
* **Push to Simulator:** Push custom sandbox squads directly into the Monte Carlo simulation engine.

### 5. 🎯 Expected Stats & Efficiency Analysis
* **Hybrid Attacking Metric Modeling:** Evaluates attacking volume via Projected $xP$, $xG/90$, $xA/90$, and $xGI/90$.
* **Career Baseline Regression:** Blends short-term form with multi-season historical baselines to detect unsustainable hot streaks and regression candidates.
* **Starter Regularity Filters:** Filters out rotation liabilities and cameo substitutes via an interactive average minutes slider.

### 6. 🛡️ Defensive Contributions & Resilience
* **Projected Defensive xP:** Calculates clean sheet odds ($P(\text{CS}) \times 4$ for DEF/GKP, $\times 1$ for MID), expected goals conceded deductions ($-0.5 \times xGC$), and projected goalkeeper saves.
* **DC (CBIT) Bonus Tracking:** Monitors Clearances, Blocks, Interceptions, and Tackles to target players consistently reaching the official FPL +2 DC bonus threshold.
* **Bayesian Minute Shrinkage:** Automatically dampens small early-season sample sizes (<90 mins) against career norms.

### 7. 📈 Rolling Form & Fixture Matrix
* **Quadrant Analysis Scatter Plot:** Interactive Plotly scatter matrix mapping 5-match rolling $xGI/90$ against 5-GW cumulative Fixture Difficulty Rating (FDR).
* **Quadrant I Target Identification:** Pinpoints players entering prime haul territory (high underlying volume paired with green schedules).

### 8. 🗓️ Fixture Difficulty Ticker
* **5-Gameweek Schedule Matrix:** Ranks all 20 Premier League clubs by cumulative FDR.
* **Venue Weighting:** Distinguishes Home (H) and Away (A) fixture difficulties.
* **My Squad Filter:** Isolate fixture runs specifically for clubs represented in your squad.

### 9. 📓 Model Audit & Performance Journal
* **Pre-Deadline Snapshot Versioning:** Maintains immutable pre-gameweek lineup versions scoped per manager account (`manager_id`).
* **Match Outcome Settlement:** Reconciles official match points against model predictions to compute variance ($Actual - Predicted$).
* **Residual Analysis:** Identifies top overperformers and underperformers to differentiate between tactical errors and variance.

---

## 🏗️ Tech Stack & Architecture

```
                       ┌─────────────────────────────────────┐
                       │       Official FPL API &            │
                       │     The Odds API (Betting)          │
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
                       ┌─────────────────────────────────────┐
                       │     Data Pipeline & Sync Engine     │
                       │  (fetch_data.py / betting_engine.py)│
                       └──────────────────┬──────────────────┘
                                          │
                                          ▼
                       ┌─────────────────────────────────────┐
                       │        SQLite Database (fpl.db)     │
                       │   • players         • fixtures      │
                       │   • player_history  • audit_snaps   │
                       └──────────────────┬──────────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
      ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐
      │   PuLP Optimization   │ │   Monte Carlo     │ │  Streamlit Frontend   │
      │  Linear Programming   │ │ Simulation Engine │ │  9 Modular Tabs       │
      │  (solve_optimal_xi)   │ │(simulation_engine)│ │  (theme.py / app.py)  │
      └───────────────────────┘ └───────────────────┘ └───────────────────────┘
```

* **Frontend & Presentation:** [Streamlit](https://streamlit.io/) with custom responsive CSS, glassmorphic card designs, dynamic SVG pitch visualizations, and modern guide popovers.
* **Mathematical Optimization:** [PuLP](https://coin-or.github.io/pulp/) (Mixed Integer Linear Programming) utilizing the CBC solver for formation selection and multi-GW transfer routes.
* **Data Manipulation & Analytics:** [Pandas](https://pandas.pydata.org/) and [NumPy](https://numpy.org/).
* **Statistical Computing & Simulations:** [SciPy](https://scipy.org/) (Poisson / binomial distributions) powering the Monte Carlo match simulator.
* **Database & Persistence:** [SQLite3](https://www.sqlite.org/) with automated schema migrations and manager-scoped version auditing.
* **String & Fuzzy Matching:** [RapidFuzz](https://github.com/maxbachmann/rapidfuzz) for instant search-as-you-type player querying.
* **Interactive Visualizations:** [Plotly Express](https://plotly.com/python/) and custom HTML5 / Canvas components.

---

## 📂 Project Structure

```
fpl-strategic-dashboard/
├── app.py                      # Main Streamlit application entry point & router
├── requirements.txt            # Python dependencies
├── theme.py                    # Global styling, design system, and Guide popover engine
├── data.py                     # Data access layer, projected points formulas, and PuLP solver
├── simulation_engine.py        # Monte Carlo simulation engine & head-to-head distributions
├── betting_engine.py           # The Odds API integration, market xG & line velocity
├── audit_db.py                 # SQLite database schema, version migrations & snapshot persistence
├── fetch_data.py               # FPL API data extraction & database bootstrap script
├── fpl.db                      # Local SQLite database storing players, stats & audit snapshots
│
├── tabs/                       # Modular UI view controllers
│   ├── squad_analyzer.py       # Pitch view, live gameweek tracking & optimal XI solver
│   ├── transfer_analyzer.py    # Multi-GW horizon transfer planner & hit optimizer
│   ├── simulator.py            # Monte Carlo simulation tab & custom 15-player sandbox
│   ├── expected_stats.py       # Attacking metrics ($xG$, $xA$, $xGI$) & career baselines
│   ├── defensive_stats.py      # Defensive resilience, clean sheet probabilities & DC bonus
│   ├── rolling_form.py         # Rolling form scatter matrix & quadrant opportunity map
│   ├── fixture_ticker.py       # 5-gameweek fixture difficulty rating ticker
│   ├── transfer_market.py      # Transfer target finder & point value efficiency ($xP/£M$)
│   └── audit_journal.py        # Snapshot audit journal, version ledger & settlement
│
├── .streamlit/
│   ├── config.toml             # Streamlit server & theme configuration
│   └── secrets.toml            # API keys & telemetry configuration (local/untracked)
└── assets/                     # Team crests, images, and static resources
```

---

## ⚙️ Local Installation & Setup Guide

### 1. Prerequisites
* **Python 3.10** or higher
* **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/fpl-strategic-dashboard.git
cd fpl-strategic-dashboard
```

### 3. Create and Activate a Virtual Environment
* **On macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
* **On Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Initialize the Database
The application automatically checks for and builds the `fpl.db` SQLite database on first launch. If you want to populate or update the data manually via the CLI, run:
```bash
python fetch_data.py
```

### 6. Run the Application
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 🔐 Environment Secrets & Configuration

Configuration keys can be added to `.streamlit/secrets.toml` or set as environment variables.

Create a `.streamlit/secrets.toml` file in the root directory:

```toml
# (Optional) The Odds API Key for live betting market projections
# Get a free key at https://the-odds-api.com
ODDS_API_KEY = "your_odds_api_key_here"

# (Optional) Google Analytics Measurement ID for anonymous telemetry
GA_MEASUREMENT_ID = "G-XXXXXXXXXX"
```

> **Note:** If `ODDS_API_KEY` is not provided, the dashboard gracefully falls back to statistical baseline fixture difficulty ratings (FDR) and historical team defensive averages without crashing.

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve an algorithm, add a metric, or enhance the UI:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

