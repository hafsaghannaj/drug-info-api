"""
Comprehensive risk and performance metrics.
VaR, CVaR, drawdown, Sharpe, Sortino, Calmar, skewness, kurtosis.
"""

import numpy as np
from scipy import stats

from config import TRADING_DAYS_PER_YEAR, RISK_FREE_RATE


def maximum_drawdown(wealth_path: np.ndarray) -> float:
    """Compute max drawdown from a 1D wealth/price path."""
    peak = np.maximum.accumulate(wealth_path)
    drawdown = (peak - wealth_path) / peak
    return float(np.max(drawdown))


def maximum_drawdown_series(wealth_path: np.ndarray) -> np.ndarray:
    """Return the full drawdown series from a 1D wealth path."""
    peak = np.maximum.accumulate(wealth_path)
    return (peak - wealth_path) / peak


def compute_all_metrics(
    portfolio_returns: np.ndarray,
    rf: float = RISK_FREE_RATE,
) -> dict:
    """
    Compute risk/performance metrics on portfolio returns.

    Args:
        portfolio_returns: (n_sims, n_periods) daily portfolio returns
        rf: annualized risk-free rate

    Returns:
        dict of metric_name -> value (single number or array across sims)
    """
    n_sims, n_periods = portfolio_returns.shape
    daily_rf = rf / TRADING_DAYS_PER_YEAR

    # Annualized return per simulation
    total_return = np.prod(1.0 + portfolio_returns, axis=1)
    n_years = n_periods / TRADING_DAYS_PER_YEAR
    annualized_return = total_return ** (1.0 / n_years) - 1.0

    # Annualized volatility per simulation
    daily_vol = np.std(portfolio_returns, axis=1, ddof=1)
    annualized_vol = daily_vol * np.sqrt(TRADING_DAYS_PER_YEAR)

    # Sharpe ratio
    sharpe = (annualized_return - rf) / annualized_vol

    # Sortino ratio — uses downside deviation
    excess = portfolio_returns - daily_rf
    downside = np.where(excess < 0, excess, 0.0)
    downside_vol = np.sqrt(np.mean(downside**2, axis=1)) * np.sqrt(TRADING_DAYS_PER_YEAR)
    sortino = (annualized_return - rf) / np.where(downside_vol > 0, downside_vol, np.nan)

    # Maximum drawdown per simulation
    wealth = np.cumprod(1.0 + portfolio_returns, axis=1)
    max_dd = np.array([maximum_drawdown(wealth[i]) for i in range(n_sims)])

    # Calmar ratio
    calmar = annualized_return / np.where(max_dd > 0, max_dd, np.nan)

    # VaR and CVaR (on daily returns, pooled across all sims)
    all_returns = portfolio_returns.flatten()
    var_95 = np.percentile(all_returns, 5)
    var_99 = np.percentile(all_returns, 1)
    cvar_95 = all_returns[all_returns <= var_95].mean()
    cvar_99 = all_returns[all_returns <= var_99].mean()

    # Skewness and kurtosis (per simulation, then summarize)
    skew_vals = stats.skew(portfolio_returns, axis=1)
    kurt_vals = stats.kurtosis(portfolio_returns, axis=1)  # excess kurtosis

    return {
        # Distributions across simulations
        "annualized_return": annualized_return,
        "annualized_vol": annualized_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "skewness": skew_vals,
        "kurtosis": kurt_vals,
        # Single values (pooled)
        "var_95": var_95,
        "var_99": var_99,
        "cvar_95": cvar_95,
        "cvar_99": cvar_99,
        # Wealth paths for charting
        "wealth": wealth,
    }


def summarize_metrics(metrics: dict) -> dict:
    """Summarize distributions into median [5th, 95th] percentiles."""
    summary = {}
    for key in ["annualized_return", "annualized_vol", "sharpe", "sortino",
                "max_drawdown", "calmar", "skewness", "kurtosis"]:
        vals = metrics[key]
        vals_clean = vals[np.isfinite(vals)]
        if len(vals_clean) > 0:
            summary[key] = {
                "median": float(np.median(vals_clean)),
                "p5": float(np.percentile(vals_clean, 5)),
                "p95": float(np.percentile(vals_clean, 95)),
            }
    for key in ["var_95", "var_99", "cvar_95", "cvar_99"]:
        summary[key] = float(metrics[key])
    return summary
