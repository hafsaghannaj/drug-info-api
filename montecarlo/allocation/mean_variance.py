"""
Mean-variance optimization and efficient frontier computation.
Classical Markowitz for comparison with risk parity.
"""

import numpy as np
from scipy.optimize import minimize


def efficient_frontier(
    mu: np.ndarray,
    cov: np.ndarray,
    n_points: int = 50,
) -> dict:
    """
    Compute the efficient frontier via quadratic optimization.

    Returns:
        dict with 'returns', 'vols', 'weights' arrays along the frontier.
    """
    n = len(mu)

    def portfolio_vol(w):
        return np.sqrt(w @ cov @ w)

    # Find the min and max achievable returns
    min_ret = mu.min()
    max_ret = mu.max()
    target_returns = np.linspace(min_ret, max_ret, n_points)

    frontier_vols = []
    frontier_rets = []
    frontier_weights = []

    w0 = np.ones(n) / n
    bounds = [(0.0, 1.0)] * n

    for target in target_returns:
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
            {"type": "eq", "fun": lambda w, t=target: w @ mu - t},
        ]

        result = minimize(
            portfolio_vol, w0,
            method="SLSQP",
            constraints=constraints,
            bounds=bounds,
            options={"ftol": 1e-10, "maxiter": 500},
        )

        if result.success:
            frontier_vols.append(portfolio_vol(result.x))
            frontier_rets.append(target)
            frontier_weights.append(result.x.copy())

    return {
        "returns": np.array(frontier_rets),
        "vols": np.array(frontier_vols),
        "weights": np.array(frontier_weights),
    }


def min_variance_portfolio(cov: np.ndarray) -> np.ndarray:
    """Compute the global minimum variance portfolio."""
    n = cov.shape[0]

    def portfolio_var(w):
        return w @ cov @ w

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
    bounds = [(0.0, 1.0)] * n
    w0 = np.ones(n) / n

    result = minimize(
        portfolio_var, w0,
        method="SLSQP",
        constraints=constraints,
        bounds=bounds,
    )
    return result.x
