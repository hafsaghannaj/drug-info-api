"""
Publication-quality chart generation for Monte Carlo portfolio analysis.
All charts saved as high-DPI PNGs to the output directory.
"""

import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats

from config import ASSETS, ASSET_CLASSES, REGIME_NAMES, TRADING_DAYS_PER_YEAR

# Style
plt.style.use("dark_background")
COLORS = {
    "bull": "#00c853",
    "bear": "#ff6d00",
    "crisis": "#d50000",
    "primary": "#42a5f5",
    "secondary": "#ab47bc",
    "accent": "#26c6da",
    "gold": "#ffd600",
}
ASSET_COLORS = sns.color_palette("husl", len(ASSETS))
CLASS_COLORS = {"Equity": "#42a5f5", "Bond": "#66bb6a", "Commodity": "#ffa726", "FX": "#ab47bc"}


def _save(fig, output_dir, name):
    fig.savefig(os.path.join(output_dir, name), dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)


def plot_simulation_paths(results, metrics, output_dir):
    """Fan chart of portfolio wealth paths with percentile bands."""
    wealth = metrics["wealth"]  # (n_sims, n_periods)
    n_sims, n_periods = wealth.shape
    t = np.arange(n_periods) / TRADING_DAYS_PER_YEAR

    fig, ax = plt.subplots(figsize=(14, 7))

    # Plot 100 sample paths
    rng = np.random.default_rng(0)
    sample_idx = rng.choice(n_sims, size=min(100, n_sims), replace=False)
    for i in sample_idx:
        ax.plot(t, wealth[i], alpha=0.05, color=COLORS["primary"], linewidth=0.5)

    # Percentile bands
    p5 = np.percentile(wealth, 5, axis=0)
    p25 = np.percentile(wealth, 25, axis=0)
    p50 = np.median(wealth, axis=0)
    p75 = np.percentile(wealth, 75, axis=0)
    p95 = np.percentile(wealth, 95, axis=0)

    ax.fill_between(t, p5, p95, alpha=0.15, color=COLORS["primary"], label="5th-95th pct")
    ax.fill_between(t, p25, p75, alpha=0.25, color=COLORS["primary"], label="25th-75th pct")
    ax.plot(t, p50, color=COLORS["gold"], linewidth=2, label="Median")

    ax.set_xlabel("Years", fontsize=12)
    ax.set_ylabel("Portfolio Value ($1 initial)", fontsize=12)
    ax.set_title("Monte Carlo Simulation: 10,000 Portfolio Paths", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", fontsize=10)
    ax.set_xlim(0, t[-1])
    ax.grid(alpha=0.2)

    _save(fig, output_dir, "simulation_paths.png")


def plot_return_distribution(metrics, output_dir):
    """Histogram of terminal returns with VaR/CVaR lines and QQ plot."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    ann_ret = metrics["annualized_return"]

    # Histogram
    ax1.hist(ann_ret, bins=80, density=True, alpha=0.7, color=COLORS["primary"],
             edgecolor="none", label="Simulated")

    # Fitted normal overlay
    mu, sigma = ann_ret.mean(), ann_ret.std()
    x = np.linspace(ann_ret.min(), ann_ret.max(), 200)
    ax1.plot(x, stats.norm.pdf(x, mu, sigma), color=COLORS["gold"],
             linewidth=2, label=f"Normal fit (μ={mu:.2%}, σ={sigma:.2%})")

    # VaR lines
    var_5 = np.percentile(ann_ret, 5)
    var_1 = np.percentile(ann_ret, 1)
    ax1.axvline(var_5, color=COLORS["bear"], linestyle="--", linewidth=1.5,
                label=f"5th pct: {var_5:.2%}")
    ax1.axvline(var_1, color=COLORS["crisis"], linestyle="--", linewidth=1.5,
                label=f"1st pct: {var_1:.2%}")

    ax1.set_xlabel("Annualized Return", fontsize=11)
    ax1.set_ylabel("Density", fontsize=11)
    ax1.set_title("Distribution of Annualized Returns", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=9)
    ax1.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax1.grid(alpha=0.2)

    # QQ plot
    stats.probplot(ann_ret, dist="norm", plot=ax2)
    ax2.set_title("Q-Q Plot vs. Normal", fontsize=13, fontweight="bold")
    ax2.get_lines()[0].set_color(COLORS["primary"])
    ax2.get_lines()[0].set_markersize(2)
    ax2.get_lines()[1].set_color(COLORS["crisis"])
    ax2.grid(alpha=0.2)

    _save(fig, output_dir, "return_distribution.png")


def plot_regime_timeline(results, output_dir):
    """Stacked area showing regime fractions over time."""
    regimes = results["regimes"]  # (n_sims, n_periods)
    n_sims, n_periods = regimes.shape
    t = np.arange(n_periods) / TRADING_DAYS_PER_YEAR

    # Fraction of sims in each regime at each time step
    fractions = np.zeros((3, n_periods))
    for r in range(3):
        fractions[r] = (regimes == r).mean(axis=0)

    fig, ax = plt.subplots(figsize=(14, 5))
    colors = [COLORS["bull"], COLORS["bear"], COLORS["crisis"]]
    labels = ["Bull", "Bear", "Crisis"]
    ax.stackplot(t, fractions, colors=colors, labels=labels, alpha=0.85)

    ax.set_xlabel("Years", fontsize=12)
    ax.set_ylabel("Fraction of Simulations", fontsize=12)
    ax.set_title("Regime Distribution Over Time (Markov Chain)", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.set_xlim(0, t[-1])
    ax.set_ylim(0, 1)
    ax.grid(alpha=0.2)

    _save(fig, output_dir, "regime_timeline.png")


def plot_risk_parity_allocation(weights, risk_contribs, output_dir):
    """Side-by-side bar charts: capital weights vs risk contribution."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    x = np.arange(len(ASSETS))
    short_names = [a.replace("_", "\n") for a in ASSETS]

    # Capital weights
    bars1 = ax1.bar(x, weights, color=ASSET_COLORS, edgecolor="white", linewidth=0.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(short_names, fontsize=8)
    ax1.set_ylabel("Weight", fontsize=11)
    ax1.set_title("Capital Allocation", fontsize=13, fontweight="bold")
    ax1.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax1.grid(alpha=0.2, axis="y")

    # Risk contribution
    bars2 = ax2.bar(x, risk_contribs, color=ASSET_COLORS, edgecolor="white", linewidth=0.5)
    ax2.set_xticks(x)
    ax2.set_xticklabels(short_names, fontsize=8)
    ax2.set_ylabel("Risk Contribution", fontsize=11)
    ax2.set_title("Risk Contribution (Target: Equal)", fontsize=13, fontweight="bold")
    ax2.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax2.axhline(1.0 / len(ASSETS), color=COLORS["gold"], linestyle="--",
                linewidth=1.5, label=f"Target: {1/len(ASSETS):.1%}")
    ax2.legend(fontsize=10)
    ax2.grid(alpha=0.2, axis="y")

    _save(fig, output_dir, "risk_parity_allocation.png")


def plot_efficient_frontier(frontier, mu, cov, rp_weights, output_dir):
    """Efficient frontier with individual assets and risk parity portfolio marked."""
    fig, ax = plt.subplots(figsize=(12, 8))

    # Frontier curve
    ax.plot(frontier["vols"], frontier["returns"], color=COLORS["primary"],
            linewidth=2, label="Efficient Frontier")

    # Individual assets
    asset_vols = np.sqrt(np.diag(cov))
    for i, (name, vol, ret) in enumerate(zip(ASSETS, asset_vols, mu)):
        ax.scatter(vol, ret, color=ASSET_COLORS[i], s=80, zorder=5, edgecolors="white")
        ax.annotate(name.replace("_", " "), (vol, ret), textcoords="offset points",
                    xytext=(8, 4), fontsize=8, color="white")

    # Risk parity portfolio
    rp_vol = np.sqrt(rp_weights @ cov @ rp_weights)
    rp_ret = rp_weights @ mu
    ax.scatter(rp_vol, rp_ret, color=COLORS["gold"], s=200, marker="*",
               zorder=10, edgecolors="white", linewidth=1, label="Risk Parity")

    # Equal weight portfolio
    ew = np.ones(len(mu)) / len(mu)
    ew_vol = np.sqrt(ew @ cov @ ew)
    ew_ret = ew @ mu
    ax.scatter(ew_vol, ew_ret, color=COLORS["accent"], s=100, marker="D",
               zorder=10, edgecolors="white", linewidth=1, label="Equal Weight")

    ax.set_xlabel("Annualized Volatility", fontsize=12)
    ax.set_ylabel("Annualized Return", fontsize=12)
    ax.set_title("Efficient Frontier with Risk Parity Portfolio", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.legend(fontsize=10, loc="upper left")
    ax.grid(alpha=0.2)

    _save(fig, output_dir, "efficient_frontier.png")


def plot_factor_decomposition(var_decomp, output_dir):
    """Stacked bar chart of variance decomposition by macro factor."""
    factor_names = ["Growth", "Inflation", "Rates", "Idiosyncratic"]
    colors = [COLORS["primary"], COLORS["bear"], COLORS["accent"], "#757575"]

    fig, ax = plt.subplots(figsize=(14, 6))
    x = np.arange(len(ASSETS))
    short_names = [a.replace("_", "\n") for a in ASSETS]

    bottom = np.zeros(len(ASSETS))
    for f in range(4):
        ax.bar(x, var_decomp[:, f], bottom=bottom, color=colors[f],
               label=factor_names[f], edgecolor="white", linewidth=0.5)
        bottom += var_decomp[:, f]

    ax.set_xticks(x)
    ax.set_xticklabels(short_names, fontsize=9)
    ax.set_ylabel("Fraction of Variance", fontsize=11)
    ax.set_title("Macro Factor Variance Decomposition", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.grid(alpha=0.2, axis="y")

    _save(fig, output_dir, "factor_decomposition.png")


def plot_stress_test(stress_df, output_dir):
    """Waterfall chart of portfolio impact under each stress scenario."""
    fig, ax = plt.subplots(figsize=(12, 6))

    scenarios = stress_df.index.tolist()
    impacts = stress_df["Portfolio_Impact"].values
    colors = [COLORS["crisis"] if v < 0 else COLORS["bull"] for v in impacts]

    bars = ax.barh(scenarios, impacts, color=colors, edgecolor="white", height=0.5)

    for bar, val in zip(bars, impacts):
        x_pos = val - 0.005 if val < 0 else val + 0.005
        ha = "right" if val < 0 else "left"
        ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
                f"{val:.1%}", ha=ha, va="center", fontsize=11, fontweight="bold")

    ax.axvline(0, color="white", linewidth=0.5)
    ax.set_xlabel("Portfolio Impact", fontsize=12)
    ax.set_title("Stress Test Results", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.grid(alpha=0.2, axis="x")
    ax.invert_yaxis()

    _save(fig, output_dir, "stress_test_waterfall.png")


def plot_drawdown_distribution(metrics, output_dir):
    """Histogram of maximum drawdowns across simulations."""
    fig, ax = plt.subplots(figsize=(12, 6))

    max_dd = metrics["max_drawdown"]
    ax.hist(max_dd, bins=80, density=True, alpha=0.7, color=COLORS["crisis"],
            edgecolor="none")

    # Key percentiles
    p50 = np.median(max_dd)
    p95 = np.percentile(max_dd, 95)
    p99 = np.percentile(max_dd, 99)

    ax.axvline(p50, color=COLORS["gold"], linestyle="--", linewidth=1.5,
               label=f"Median: {p50:.1%}")
    ax.axvline(p95, color=COLORS["bear"], linestyle="--", linewidth=1.5,
               label=f"95th pct: {p95:.1%}")
    ax.axvline(p99, color="white", linestyle="--", linewidth=1.5,
               label=f"99th pct: {p99:.1%}")

    ax.set_xlabel("Maximum Drawdown", fontsize=12)
    ax.set_ylabel("Density", fontsize=12)
    ax.set_title("Distribution of Maximum Drawdowns (10-Year Horizon)", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.legend(fontsize=10)
    ax.grid(alpha=0.2)

    _save(fig, output_dir, "drawdown_distribution.png")


def plot_metrics_summary(summary, output_dir):
    """Table-style figure showing all risk metrics."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis("off")

    rows = []
    row_labels = []

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
        rows.append([fmt(s["median"], pct), fmt(s["p5"], pct), fmt(s["p95"], pct)])
        row_labels.append(label)

    # Add single-value metrics
    for key, label in [("var_95", "Daily VaR (95%)"), ("var_99", "Daily VaR (99%)"),
                       ("cvar_95", "Daily CVaR (95%)"), ("cvar_99", "Daily CVaR (99%)")]:
        rows.append([f"{summary[key]:.4%}", "—", "—"])
        row_labels.append(label)

    col_labels = ["Median", "5th Pct", "95th Pct"]

    table = ax.table(cellText=rows, rowLabels=row_labels, colLabels=col_labels,
                     cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.6)

    # Style cells
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#555555")
        if row == 0:
            cell.set_facecolor("#333333")
            cell.set_text_props(fontweight="bold", color="white")
        elif col == -1:
            cell.set_facecolor("#2a2a2a")
            cell.set_text_props(fontweight="bold", color="white")
        else:
            cell.set_facecolor("#1a1a1a")
            cell.set_text_props(color="white")

    ax.set_title("Portfolio Risk Metrics Summary (10,000 Simulations)",
                 fontsize=14, fontweight="bold", pad=20)

    _save(fig, output_dir, "risk_metrics_summary.png")


def generate_all_charts(results, metrics, summary, weights, risk_contribs,
                        frontier, mu, cov, var_decomp, stress_df, output_dir):
    """Generate and save all charts."""
    plot_simulation_paths(results, metrics, output_dir)
    plot_return_distribution(metrics, output_dir)
    plot_regime_timeline(results, output_dir)
    plot_risk_parity_allocation(weights, risk_contribs, output_dir)
    plot_efficient_frontier(frontier, mu, cov, weights, output_dir)
    plot_factor_decomposition(var_decomp, output_dir)
    plot_stress_test(stress_df, output_dir)
    plot_drawdown_distribution(metrics, output_dir)
    plot_metrics_summary(summary, output_dir)
