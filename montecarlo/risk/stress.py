"""
Stress testing module.
Applies deterministic shock scenarios to the portfolio and reports impact.
"""

import numpy as np
import pandas as pd

from config import ASSETS, STRESS_SCENARIOS


def run_stress_tests(
    weights: np.ndarray,
    scenarios: dict = STRESS_SCENARIOS,
) -> pd.DataFrame:
    """
    Run all stress scenarios against the portfolio.

    Args:
        weights: (n_assets,) portfolio weights
        scenarios: dict of scenario_name -> {asset: shock}

    Returns:
        DataFrame with columns: Scenario, Portfolio_Loss, and per-asset contributions.
    """
    rows = []
    for name, shocks in scenarios.items():
        shock_vec = np.array([shocks[a] for a in ASSETS])
        portfolio_impact = weights @ shock_vec

        # Asset-level contribution to portfolio loss
        contributions = weights * shock_vec

        row = {"Scenario": name, "Portfolio_Impact": portfolio_impact}
        for i, asset in enumerate(ASSETS):
            row[asset] = contributions[i]

        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.set_index("Scenario")
    return df
