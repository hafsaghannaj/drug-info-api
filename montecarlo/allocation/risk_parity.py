"""
Risk parity portfolio optimizer.
Implements Bridgewater's equal-risk-contribution allocation approach.
"""

import numpy as np
from scipy.optimize import minimize

from config import ASSETS, ASSET_CLASSES


def risk_contribution(weights: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Compute each asset's percentage contribution to total portfolio risk."""
    port_var = weights @ cov @ weights
    port_vol = np.sqrt(port_var)
    marginal = cov @ weights  # marginal risk per asset
    rc = weights * marginal / port_vol  # risk contribution
    return rc / rc.sum()  # normalize to percentages


def risk_parity_weights(cov: np.ndarray) -> np.ndarray:
    """
    Compute risk parity weights where each asset contributes
    equal risk to the portfolio.
    """
    n = cov.shape[0]
    target_rc = np.ones(n) / n

    def objective(w):
        port_var = w @ cov @ w
        port_vol = np.sqrt(port_var)
        marginal = cov @ w
        rc = w * marginal / port_vol
        rc_pct = rc / rc.sum()
        return np.sum((rc_pct - target_rc) ** 2)

    # Initial guess: inverse volatility
    vols = np.sqrt(np.diag(cov))
    w0 = (1.0 / vols) / (1.0 / vols).sum()

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0.01, 0.50)] * n  # min 1%, max 50% per asset

    result = minimize(
        objective, w0,
        method="SLSQP",
        constraints=constraints,
        bounds=bounds,
        options={"ftol": 1e-12, "maxiter": 1000},
    )

    if not result.success:
        # Fall back to inverse-vol weights
        return w0

    return result.x


def risk_parity_by_class(weights: np.ndarray, cov: np.ndarray) -> dict:
    """Compute risk contribution grouped by asset class."""
    rc = risk_contribution(weights, cov)
    class_rc = {}
    for i, asset in enumerate(ASSETS):
        cls = ASSET_CLASSES[asset]
        class_rc[cls] = class_rc.get(cls, 0.0) + rc[i]
    return class_rc
