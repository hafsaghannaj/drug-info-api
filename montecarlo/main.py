"""
Monte Carlo Portfolio Simulation — Bridgewater-Caliber Analysis

Multi-asset, regime-switching simulation with fat-tailed returns,
risk parity allocation, macro factor decomposition, and stress testing.

Usage:
    python main.py
"""

import os
import sys
import time

import numpy as np
import pandas as pd

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    ASSETS, ASSET_CLASSES, N_ASSETS, N_SIMULATIONS, N_PERIODS,
    TRADING_DAYS_PER_YEAR, RISK_FREE_RATE, REGIMES, REGIME_NAMES,
    TRANSITION_MATRIX, FACTOR_LOADINGS, STRESS_SCENARIOS, SEED,
)
from engine.simulation import run_monte_carlo, precompute_regime_params
from engine.factors import decompose_returns
from allocation.risk_parity import risk_parity_weights, risk_contribution, risk_parity_by_class
from allocation.mean_variance import efficient_frontier
from risk.metrics import compute_all_metrics, summarize_metrics
from risk.stress import run_stress_tests
from visualization.charts import generate_all_charts


def print_header():
    print("=" * 72)
    print("  MONTE CARLO PORTFOLIO SIMULATION")
    print("  Multi-Asset | Regime-Switching | Fat-Tailed | Risk Parity")
    print("=" * 72)
    print(f"  Assets:       {N_ASSETS} across Equity, Bond, Commodity, FX")
    print(f"  Simulations:  {N_SIMULATIONS:,}")
    print(f"  Horizon:      {N_PERIODS // TRADING_DAYS_PER_YEAR} years ({N_PERIODS:,} trading days)")
    print(f"  Regimes:      Bull / Bear / Crisis (Markov switching)")
    print(f"  Innovations:  Student-t (fat tails) + Cholesky correlation")
    print(f"  Risk-free:    {RISK_FREE_RATE:.1%}")
    print(f"  Seed:         {SEED}")
    print("=" * 72)


def print_summary(weights, risk_contribs, class_rc, summary, stress_df):
    print("\n" + "─" * 72)
    print("  RISK PARITY PORTFOLIO ALLOCATION")
    print("─" * 72)
    print(f"  {'Asset':<20} {'Weight':>10} {'Risk Contrib':>14} {'Class':>10}")
    print("  " + "-" * 56)
    for i, asset in enumerate(ASSETS):
        print(f"  {asset:<20} {weights[i]:>10.2%} {risk_contribs[i]:>14.2%} {ASSET_CLASSES[asset]:>10}")

    print("\n  Risk Contribution by Asset Class:")
    for cls, rc in class_rc.items():
        print(f"    {cls:<12} {rc:.2%}")

    print("\n" + "─" * 72)
    print("  PORTFOLIO RISK METRICS (across {:,} simulations)".format(N_SIMULATIONS))
    print("─" * 72)
    print(f"  {'Metric':<28} {'Median':>10} {'5th Pct':>10} {'95th Pct':>10}")
    print("  " + "-" * 60)

    def fmt(v, pct=True):
        return f"{v:.2%}" if pct else f"{v:.2f}"

    for key, label, pct in [
        ("annualized_return", "Annualized Return", True),
        ("annualized_vol", "Annualized Volatility", True),
        ("sharpe", "Sharpe Ratio", False),
        ("sortino", "Sortino Ratio", False),
        ("max_drawdown", "Maximum Drawdown", True),
        ("calmar", "Calmar Ratio", False),
        ("skewness", "Skewness", False),
        ("kurtosis", "Excess Kurtosis", False),
    ]:
        s = summary[key]
        print(f"  {label:<28} {fmt(s['median'], pct):>10} {fmt(s['p5'], pct):>10} {fmt(s['p95'], pct):>10}")

    print(f"\n  Daily VaR (95%):   {summary['var_95']:.4%}")
    print(f"  Daily VaR (99%):   {summary['var_99']:.4%}")
    print(f"  Daily CVaR (95%):  {summary['cvar_95']:.4%}")
    print(f"  Daily CVaR (99%):  {summary['cvar_99']:.4%}")

    print("\n" + "─" * 72)
    print("  STRESS TEST RESULTS")
    print("─" * 72)
    print(f"  {'Scenario':<20} {'Portfolio Impact':>18}")
    print("  " + "-" * 40)
    for scenario in stress_df.index:
        impact = stress_df.loc[scenario, "Portfolio_Impact"]
        print(f"  {scenario:<20} {impact:>18.2%}")


def main():
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    print_header()

    # 1. Run Monte Carlo simulation
    print("\n[1/7] Running Monte Carlo simulation...", flush=True)
    t0 = time.time()
    results = run_monte_carlo(n_sims=N_SIMULATIONS, seed=SEED)
    t1 = time.time()
    print(f"      Done in {t1 - t0:.1f}s — generated {N_SIMULATIONS:,} paths")

    # 2. Compute weighted-average covariance from simulation for allocation
    print("[2/7] Computing covariance and expected returns...", flush=True)
    # Use mean returns and covariance from simulated data
    mean_daily_returns = results["returns"].mean(axis=(0, 1))  # (n_assets,)
    mu_annual = mean_daily_returns * TRADING_DAYS_PER_YEAR

    # Flatten sims for covariance estimation
    flat_returns = results["returns"].reshape(-1, N_ASSETS)  # (n_sims*n_periods, n_assets)
    # Use a subsample for covariance to keep memory reasonable
    rng = np.random.default_rng(SEED)
    subsample_idx = rng.choice(flat_returns.shape[0], size=min(500_000, flat_returns.shape[0]), replace=False)
    cov_daily = np.cov(flat_returns[subsample_idx], rowvar=False)
    cov_annual = cov_daily * TRADING_DAYS_PER_YEAR

    # 3. Risk parity allocation
    print("[3/7] Optimizing risk parity portfolio...", flush=True)
    weights = risk_parity_weights(cov_annual)
    risk_contribs = risk_contribution(weights, cov_annual)
    class_rc = risk_parity_by_class(weights, cov_annual)

    # 4. Portfolio returns and risk metrics
    print("[4/7] Computing portfolio risk metrics...", flush=True)
    portfolio_returns = np.einsum("ijk,k->ij", results["returns"], weights)
    metrics = compute_all_metrics(portfolio_returns)
    summary = summarize_metrics(metrics)

    # 5. Macro factor decomposition
    print("[5/7] Decomposing into macro factors...", flush=True)
    factor_results = decompose_returns(results["returns"])
    var_decomp = factor_results["variance_decomposition"]

    # 6. Efficient frontier
    print("[6/7] Computing efficient frontier...", flush=True)
    frontier = efficient_frontier(mu_annual, cov_annual, n_points=50)

    # 7. Stress testing
    print("[7/7] Running stress tests...", flush=True)
    stress_df = run_stress_tests(weights)

    # Print console summary
    print_summary(weights, risk_contribs, class_rc, summary, stress_df)

    # Generate charts
    print(f"\nGenerating visualizations to {output_dir}/...", flush=True)
    generate_all_charts(
        results=results,
        metrics=metrics,
        summary=summary,
        weights=weights,
        risk_contribs=risk_contribs,
        frontier=frontier,
        mu=mu_annual,
        cov=cov_annual,
        var_decomp=var_decomp,
        stress_df=stress_df,
        output_dir=output_dir,
    )

    # Save summary CSV
    summary_rows = []
    for key in ["annualized_return", "annualized_vol", "sharpe", "sortino",
                "max_drawdown", "calmar", "skewness", "kurtosis"]:
        s = summary[key]
        summary_rows.append({"metric": key, "median": s["median"], "p5": s["p5"], "p95": s["p95"]})
    for key in ["var_95", "var_99", "cvar_95", "cvar_99"]:
        summary_rows.append({"metric": key, "median": summary[key], "p5": None, "p95": None})
    pd.DataFrame(summary_rows).to_csv(os.path.join(output_dir, "summary.csv"), index=False)

    print(f"\nAll outputs saved to {output_dir}/")
    print("Charts: " + ", ".join([
        "simulation_paths.png", "return_distribution.png", "regime_timeline.png",
        "risk_parity_allocation.png", "efficient_frontier.png", "factor_decomposition.png",
        "stress_test_waterfall.png", "drawdown_distribution.png", "risk_metrics_summary.png",
    ]))
    print("\n" + "=" * 72)
    print("  Simulation complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()
