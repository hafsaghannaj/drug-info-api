"""
Core Monte Carlo simulation engine.
Generates correlated, fat-tailed, regime-aware return paths using
Cholesky decomposition with Student-t innovations.
"""

import numpy as np
from scipy import stats

from config import (
    ASSETS, N_ASSETS, N_SIMULATIONS, N_PERIODS, DT,
    REGIMES, REGIME_NAMES, TRANSITION_MATRIX, SEED,
)
from engine.regimes import simulate_regime_paths


def nearest_positive_definite(A: np.ndarray) -> np.ndarray:
    """Find the nearest positive-definite matrix (Higham algorithm)."""
    B = (A + A.T) / 2
    _, s, V = np.linalg.svd(B)
    H = V.T @ np.diag(s) @ V
    A2 = (B + H) / 2
    A3 = (A2 + A2.T) / 2

    if is_positive_definite(A3):
        return A3

    spacing = np.spacing(np.linalg.norm(A))
    I = np.eye(A.shape[0])
    k = 1
    while not is_positive_definite(A3):
        mineig = np.min(np.real(np.linalg.eigvalsh(A3)))
        A3 += I * (-mineig * k**2 + spacing)
        k += 1
    return A3


def is_positive_definite(A: np.ndarray) -> bool:
    try:
        np.linalg.cholesky(A)
        return True
    except np.linalg.LinAlgError:
        return False


def precompute_regime_params() -> dict:
    """Pre-compute Cholesky factors and scaled parameters for each regime."""
    params = {}
    for name in REGIME_NAMES:
        r = REGIMES[name]
        mu = r["mu"]
        sigma = r["sigma"]
        corr = r["corr"]
        df = r["df"]

        # Build covariance matrix and scale to daily
        cov_annual = np.diag(sigma) @ corr @ np.diag(sigma)
        cov_daily = cov_annual * DT

        # Ensure positive definiteness
        if not is_positive_definite(cov_daily):
            cov_daily = nearest_positive_definite(cov_daily)

        L = np.linalg.cholesky(cov_daily)
        mu_daily = mu * DT

        # Student-t variance normalization: Var(t_df) = df/(df-2) for df > 2
        t_scale = np.sqrt((df - 2) / df) if df > 2 else 1.0

        params[name] = {
            "mu_daily": mu_daily,
            "L": L,
            "df": df,
            "t_scale": t_scale,
            "cov_annual": cov_annual,
        }
    return params


def run_monte_carlo(n_sims: int = N_SIMULATIONS, seed: int = SEED) -> dict:
    """
    Run the full Monte Carlo simulation.

    Returns:
        dict with keys:
            'returns':  (n_sims, N_PERIODS, N_ASSETS) daily returns
            'prices':   (n_sims, N_PERIODS+1, N_ASSETS) price levels starting at 1.0
            'regimes':  (n_sims, N_PERIODS) integer regime labels
    """
    rng = np.random.default_rng(seed)
    regime_params = precompute_regime_params()

    # Simulate regime paths
    regimes = simulate_regime_paths(TRANSITION_MATRIX, n_sims, N_PERIODS, rng)

    # Pre-allocate returns array
    returns = np.empty((n_sims, N_PERIODS, N_ASSETS))

    # Generate returns regime-by-regime for efficiency
    # Process each regime block: find all (sim, time) pairs in that regime
    for regime_idx, regime_name in enumerate(REGIME_NAMES):
        p = regime_params[regime_name]
        mask = regimes == regime_idx  # (n_sims, N_PERIODS) boolean

        n_draws = mask.sum()
        if n_draws == 0:
            continue

        # Draw independent Student-t variates
        z = stats.t.rvs(df=p["df"], size=(n_draws, N_ASSETS), random_state=rng)
        z *= p["t_scale"]  # normalize to unit variance

        # Apply Cholesky correlation: r = mu + L @ z
        correlated = z @ p["L"].T + p["mu_daily"]

        # Place into the returns array at the correct positions
        returns[mask] = correlated

    # Compute price paths
    prices = np.ones((n_sims, N_PERIODS + 1, N_ASSETS))
    prices[:, 1:, :] = np.cumprod(1.0 + returns, axis=1)

    return {
        "returns": returns,
        "prices": prices,
        "regimes": regimes,
    }
