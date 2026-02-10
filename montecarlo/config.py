"""
Configuration for Monte Carlo Portfolio Simulation.
All parameters, regime definitions, factor loadings, and stress scenarios.
"""

import numpy as np

# ─── Asset Universe ───────────────────────────────────────────────────────────

ASSETS = [
    "US_Equity", "Intl_Equity", "US_Treasury_10Y", "TIPS",
    "Gold", "Commodities", "USD_EUR", "USD_JPY",
]

ASSET_CLASSES = {
    "US_Equity": "Equity", "Intl_Equity": "Equity",
    "US_Treasury_10Y": "Bond", "TIPS": "Bond",
    "Gold": "Commodity", "Commodities": "Commodity",
    "USD_EUR": "FX", "USD_JPY": "FX",
}

N_ASSETS = len(ASSETS)

# ─── Simulation Parameters ────────────────────────────────────────────────────

N_SIMULATIONS = 10_000
N_YEARS = 10
TRADING_DAYS_PER_YEAR = 252
N_PERIODS = TRADING_DAYS_PER_YEAR * N_YEARS  # 2520
DT = 1.0 / TRADING_DAYS_PER_YEAR
RISK_FREE_RATE = 0.04  # annualized
SEED = 42

# ─── Regime Parameters ────────────────────────────────────────────────────────
# Each regime: annualized mu, annualized sigma, correlation matrix, Student-t df

# Bull regime — moderate returns, low vol, moderate correlations
BULL_MU = np.array([0.10, 0.08, 0.03, 0.04, 0.05, 0.06, 0.01, -0.01])
BULL_SIGMA = np.array([0.15, 0.17, 0.06, 0.07, 0.16, 0.20, 0.08, 0.10])
BULL_CORR = np.array([
    [ 1.00,  0.80,  -0.20, -0.10,  0.05,  0.30,  0.10,  0.05],
    [ 0.80,  1.00,  -0.15, -0.05,  0.10,  0.35,  0.25,  0.15],
    [-0.20, -0.15,   1.00,  0.70, -0.05, -0.10, -0.05,  0.10],
    [-0.10, -0.05,   0.70,  1.00,  0.15,  0.10,  0.00,  0.05],
    [ 0.05,  0.10,  -0.05,  0.15,  1.00,  0.40,  0.20,  0.10],
    [ 0.30,  0.35,  -0.10,  0.10,  0.40,  1.00,  0.15,  0.05],
    [ 0.10,  0.25,  -0.05,  0.00,  0.20,  0.15,  1.00,  0.30],
    [ 0.05,  0.15,   0.10,  0.05,  0.10,  0.05,  0.30,  1.00],
])
BULL_DF = 8  # mild fat tails

# Bear regime — negative/low returns, high vol, higher correlations
BEAR_MU = np.array([-0.05, -0.08, 0.06, 0.03, 0.08, -0.03, 0.02, 0.03])
BEAR_SIGMA = np.array([0.25, 0.28, 0.10, 0.12, 0.22, 0.30, 0.12, 0.14])
BEAR_CORR = np.array([
    [ 1.00,  0.90,  -0.30, -0.15,  0.15,  0.50,  0.20,  0.10],
    [ 0.90,  1.00,  -0.25, -0.10,  0.20,  0.55,  0.35,  0.20],
    [-0.30, -0.25,   1.00,  0.75, -0.10, -0.20, -0.10,  0.15],
    [-0.15, -0.10,   0.75,  1.00,  0.20,  0.05,  0.00,  0.10],
    [ 0.15,  0.20,  -0.10,  0.20,  1.00,  0.45,  0.25,  0.15],
    [ 0.50,  0.55,  -0.20,  0.05,  0.45,  1.00,  0.20,  0.10],
    [ 0.20,  0.35,  -0.10,  0.00,  0.25,  0.20,  1.00,  0.40],
    [ 0.10,  0.20,   0.15,  0.10,  0.15,  0.10,  0.40,  1.00],
])
BEAR_DF = 5  # moderate fat tails

# Crisis regime — large drawdowns, extreme vol, correlations spike toward 1
CRISIS_MU = np.array([-0.30, -0.35, 0.10, 0.02, 0.15, -0.20, 0.05, 0.08])
CRISIS_SIGMA = np.array([0.45, 0.50, 0.15, 0.18, 0.30, 0.45, 0.18, 0.20])
CRISIS_CORR = np.array([
    [ 1.00,  0.95,  -0.40, -0.20,  0.25,  0.70,  0.30,  0.15],
    [ 0.95,  1.00,  -0.35, -0.15,  0.30,  0.75,  0.45,  0.25],
    [-0.40, -0.35,   1.00,  0.80, -0.15, -0.30, -0.15,  0.20],
    [-0.20, -0.15,   0.80,  1.00,  0.25,  0.00,  0.00,  0.15],
    [ 0.25,  0.30,  -0.15,  0.25,  1.00,  0.50,  0.30,  0.20],
    [ 0.70,  0.75,  -0.30,  0.00,  0.50,  1.00,  0.25,  0.15],
    [ 0.30,  0.45,  -0.15,  0.00,  0.30,  0.25,  1.00,  0.50],
    [ 0.15,  0.25,   0.20,  0.15,  0.20,  0.15,  0.50,  1.00],
])
CRISIS_DF = 3  # extreme fat tails

REGIMES = {
    "bull":   {"mu": BULL_MU,   "sigma": BULL_SIGMA,   "corr": BULL_CORR,   "df": BULL_DF},
    "bear":   {"mu": BEAR_MU,   "sigma": BEAR_SIGMA,   "corr": BEAR_CORR,   "df": BEAR_DF},
    "crisis": {"mu": CRISIS_MU, "sigma": CRISIS_SIGMA, "corr": CRISIS_CORR, "df": CRISIS_DF},
}

REGIME_NAMES = ["bull", "bear", "crisis"]

# ─── Markov Transition Matrix ─────────────────────────────────────────────────
# Row = current regime, Col = next regime.  Daily transition probabilities.
TRANSITION_MATRIX = np.array([
    [0.980, 0.015, 0.005],  # bull  → bull 98.0%, bear 1.5%, crisis 0.5%
    [0.030, 0.950, 0.020],  # bear  → bull 3.0%,  bear 95%,  crisis 2.0%
    [0.050, 0.150, 0.800],  # crisis→ bull 5.0%,  bear 15%,  crisis 80%
])

# ─── Macro Factor Loadings ────────────────────────────────────────────────────
# 8 assets × 3 factors: [Growth, Inflation, Rates]
# Calibrated to economic intuition:
#   Growth:    equities +, bonds -, commodities +
#   Inflation: TIPS +, gold +, commodities +, nominal bonds -
#   Rates:     bonds -, equities -, TIPS partial hedge
FACTOR_LOADINGS = np.array([
    [ 0.80,  0.10, -0.20],  # US_Equity
    [ 0.75,  0.15, -0.15],  # Intl_Equity
    [-0.30, -0.40,  0.70],  # US_Treasury_10Y
    [-0.10,  0.50,  0.30],  # TIPS
    [ 0.10,  0.60, -0.10],  # Gold
    [ 0.40,  0.55, -0.05],  # Commodities
    [ 0.20,  0.05, -0.15],  # USD_EUR
    [-0.10, -0.05,  0.25],  # USD_JPY
])

# ─── Stress Scenarios ─────────────────────────────────────────────────────────
# Asset-level cumulative shocks (total return over scenario period)
STRESS_SCENARIOS = {
    "GFC 2008": {
        "US_Equity": -0.38, "Intl_Equity": -0.43, "US_Treasury_10Y": 0.20,
        "TIPS": 0.02, "Gold": 0.05, "Commodities": -0.36,
        "USD_EUR": -0.04, "USD_JPY": 0.23,
    },
    "COVID 2020": {
        "US_Equity": -0.34, "Intl_Equity": -0.30, "US_Treasury_10Y": 0.15,
        "TIPS": 0.05, "Gold": 0.03, "Commodities": -0.25,
        "USD_EUR": -0.02, "USD_JPY": 0.03,
    },
    "Rate Shock": {
        "US_Equity": -0.15, "Intl_Equity": -0.12, "US_Treasury_10Y": -0.18,
        "TIPS": -0.08, "Gold": -0.05, "Commodities": 0.05,
        "USD_EUR": -0.05, "USD_JPY": -0.08,
    },
    "Stagflation": {
        "US_Equity": -0.20, "Intl_Equity": -0.22, "US_Treasury_10Y": -0.10,
        "TIPS": 0.05, "Gold": 0.15, "Commodities": 0.25,
        "USD_EUR": 0.03, "USD_JPY": -0.05,
    },
}
