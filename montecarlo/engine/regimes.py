"""
Markov regime-switching model.
Generates regime paths (bull/bear/crisis) for Monte Carlo simulations.
"""

import numpy as np


def stationary_distribution(transition_matrix: np.ndarray) -> np.ndarray:
    """Compute the stationary distribution of a Markov chain."""
    n = transition_matrix.shape[0]
    # Solve pi @ P = pi  with  sum(pi) = 1
    # Equivalent to (P^T - I) @ pi = 0  with constraint
    A = transition_matrix.T - np.eye(n)
    A[-1, :] = 1.0  # replace last equation with sum = 1
    b = np.zeros(n)
    b[-1] = 1.0
    return np.linalg.solve(A, b)


def simulate_regime_paths(
    transition_matrix: np.ndarray,
    n_sims: int,
    n_periods: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Simulate Markov chain regime paths for all simulations.

    Returns:
        regimes: array of shape (n_sims, n_periods) with integer labels
                 0=bull, 1=bear, 2=crisis
    """
    n_regimes = transition_matrix.shape[0]
    pi = stationary_distribution(transition_matrix)

    # Cumulative transition probabilities for vectorized sampling
    cum_trans = np.cumsum(transition_matrix, axis=1)

    regimes = np.empty((n_sims, n_periods), dtype=np.int32)

    # Initial states drawn from stationary distribution
    regimes[:, 0] = rng.choice(n_regimes, size=n_sims, p=pi)

    # Step through time — vectorized across simulations
    for t in range(1, n_periods):
        u = rng.random(n_sims)
        current = regimes[:, t - 1]
        # For each sim, look up the cumulative transition row for its current regime
        cum_probs = cum_trans[current]  # (n_sims, n_regimes)
        # Determine next regime: first column where u < cum_prob
        regimes[:, t] = (u[:, None] >= cum_probs).sum(axis=1)

    return regimes
