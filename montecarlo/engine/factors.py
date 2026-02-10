"""
Macro factor decomposition.
Decomposes simulated returns into Growth, Inflation, and Rate components.
"""

import numpy as np

from config import FACTOR_LOADINGS, ASSETS

FACTOR_NAMES = ["Growth", "Inflation", "Rates"]


def decompose_returns(returns: np.ndarray) -> dict:
    """
    Decompose asset returns into macro factor components via OLS projection.

    Args:
        returns: (n_periods, n_assets) or (n_sims, n_periods, n_assets)
                 If 3D, uses the mean across simulations.

    Returns:
        dict with:
            'factor_returns':         (n_periods, 3) estimated factor return series
            'explained':              (n_periods, n_assets) factor-explained returns
            'residual':               (n_periods, n_assets) idiosyncratic returns
            'variance_decomposition': (n_assets, 4) fraction of variance from each factor + idio
    """
    B = FACTOR_LOADINGS  # (n_assets, 3)

    # If 3D, average across simulations for decomposition
    if returns.ndim == 3:
        R = returns.mean(axis=0)  # (n_periods, n_assets)
    else:
        R = returns

    # OLS: F = (B^T B)^{-1} B^T R^T  →  (3, n_periods)
    BtB_inv = np.linalg.inv(B.T @ B)
    factor_returns = (BtB_inv @ B.T @ R.T).T  # (n_periods, 3)

    # Explained returns
    explained = factor_returns @ B.T  # (n_periods, n_assets)

    # Residual
    residual = R - explained

    # Variance decomposition per asset
    total_var = np.var(R, axis=0)  # (n_assets,)
    n_assets = B.shape[0]
    n_factors = B.shape[1]
    var_decomp = np.zeros((n_assets, n_factors + 1))

    for f in range(n_factors):
        # Contribution of factor f to each asset
        factor_component = np.outer(factor_returns[:, f], B[:, f])  # (n_periods, n_assets)
        var_decomp[:, f] = np.var(factor_component, axis=0)

    var_decomp[:, -1] = np.var(residual, axis=0)  # idiosyncratic

    # Normalize to fractions
    row_sums = var_decomp.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    var_decomp_frac = var_decomp / row_sums

    return {
        "factor_returns": factor_returns,
        "explained": explained,
        "residual": residual,
        "variance_decomposition": var_decomp_frac,
    }
