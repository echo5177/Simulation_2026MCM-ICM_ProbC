from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def set_plot_style() -> None:
    sns.set_theme(style="whitegrid", context="paper")


def plot_season_structure(season_audit: pd.DataFrame, path: str | Path) -> None:
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(season_audit["season"].astype(str), season_audit["contestants"])
    ax.set_xlabel("Season")
    ax.set_ylabel("Contestants")
    ax.set_title("Contestants per Season")
    ax.tick_params(axis="x", labelrotation=90)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_judge_score_distribution(panel: pd.DataFrame, path: str | Path) -> None:
    set_plot_style()
    active = panel.loc[panel["active"]].copy()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.histplot(active["judge_total"], bins=30, ax=ax)
    ax.set_xlabel("Weekly judge total")
    ax.set_ylabel("Contestant-weeks")
    ax.set_title("Judge Score Distribution")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_fan_intervals(fan_estimates: pd.DataFrame, path: str | Path) -> None:
    set_plot_style()
    event_score = (
        fan_estimates.groupby(["season", "week"])["fan_share_width"]
        .mean()
        .sort_values(ascending=False)
    )
    season, week = event_score.index[0]
    sample = fan_estimates.loc[
        (fan_estimates["season"] == season) & (fan_estimates["week"] == week)
    ].sort_values("fan_share_est")

    fig, ax = plt.subplots(figsize=(8, 5.2))
    y = range(len(sample))
    ax.hlines(
        y,
        sample["fan_share_min"],
        sample["fan_share_max"],
        color="#5B8FF9",
        linewidth=2,
    )
    ax.scatter(sample["fan_share_est"], y, color="#D7263D", zorder=3, s=24)
    ax.set_yticks(list(y))
    ax.set_yticklabels(sample["celebrity_name"])
    ax.set_xlabel("Fan share")
    ax.set_title(f"Widest Feasible Fan-Support Intervals: Season {season}, Week {week}")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_uncertainty_heatmap(fan_estimates: pd.DataFrame, path: str | Path) -> None:
    set_plot_style()
    heat = fan_estimates.groupby(["season", "week"])["fan_share_width"].mean().unstack()
    fig, ax = plt.subplots(figsize=(8.5, 8))
    sns.heatmap(heat, cmap="viridis", ax=ax, cbar_kws={"label": "Mean interval width"})
    ax.set_title("Fan-Support Uncertainty by Season and Week")
    ax.set_xlabel("Week")
    ax.set_ylabel("Season")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_validation_dashboard(validation: pd.DataFrame, path: str | Path) -> None:
    set_plot_style()
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    match_rate = validation["percent_reproduces_observed"].mean()
    bottom_two_rate = validation["observed_in_bottom_two"].mean()
    axes[0].bar(["Exact set", "Bottom-two hit"], [match_rate, bottom_two_rate], color=["#2A9D8F", "#E9C46A"])
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Rate")
    axes[0].set_title("Reproduction")

    sns.histplot(validation["bottom_two_margin"].dropna(), bins=25, ax=axes[1], color="#5B8FF9")
    axes[1].set_title("Bottom-Two Margins")
    axes[1].set_xlabel("Combined-score margin")

    sns.histplot(validation["mean_fan_share_width"].dropna(), bins=25, ax=axes[2], color="#D7263D")
    axes[2].set_title("Uncertainty Widths")
    axes[2].set_xlabel("Mean feasible width")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_rule_comparison_heatmap(counterfactuals: pd.DataFrame, path: str | Path) -> None:
    set_plot_style()
    heat = (
        counterfactuals.assign(value=counterfactuals["rank_percent_different"].astype(int))
        .pivot_table(index="season", columns="week", values="value", aggfunc="max")
    )
    fig, ax = plt.subplots(figsize=(8.5, 8))
    sns.heatmap(
        heat,
        cmap=sns.color_palette(["#F2F2F2", "#D7263D"], as_cmap=True),
        cbar_kws={"label": "Rank differs from percent"},
        ax=ax,
    )
    ax.set_title("Rank vs Percent Counterfactual Differences")
    ax.set_xlabel("Week")
    ax.set_ylabel("Season")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_controversy_cases(trajectory: pd.DataFrame, path: str | Path) -> None:
    set_plot_style()
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for (name, season), group in trajectory.groupby(["celebrity_name", "season"]):
        label = f"{name} S{season}"
        ax.plot(group["week"], group["judge_rank"], marker="o", linewidth=1.6, label=f"{label} judge")
        ax.plot(group["week"], group["fan_rank_est"], marker="s", linestyle="--", linewidth=1.4, label=f"{label} fan")
    ax.invert_yaxis()
    ax.set_xlabel("Week")
    ax.set_ylabel("Rank (1 is best)")
    ax.set_title("Controversial Contestant Judge vs Estimated Fan Ranks")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_effects_forest(effects: pd.DataFrame, path: str | Path) -> None:
    set_plot_style()
    numeric = effects.copy()
    numeric["estimate_num"] = pd.to_numeric(numeric["estimate"], errors="coerce")
    numeric = numeric.dropna(subset=["estimate_num"])
    numeric = numeric.loc[numeric["term"] != "Intercept"].copy()
    if numeric.empty:
        return
    numeric["abs_estimate"] = numeric["estimate_num"].abs()
    sample = numeric.sort_values("abs_estimate", ascending=False).head(16)
    sample = sample.sort_values("estimate_num")

    fig, ax = plt.subplots(figsize=(8, 5.5))
    labels = sample["model"] + ": " + sample["term"].str.replace("C(celebrity_industry)[T.", "", regex=False).str.replace("]", "", regex=False)
    ax.barh(labels, sample["estimate_num"], color="#5B8FF9")
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Estimated coefficient")
    ax.set_title("Largest Effect Model Coefficients")
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def plot_system_comparison(simulation_summary: pd.DataFrame, path: str | Path) -> None:
    set_plot_style()
    summary = simulation_summary.loc[
        simulation_summary["metric"].isin(
            [
                "gray_zone_trigger_rate",
                "proposed_changes_percent_rate",
                "proposed_matches_observed_rate",
            ]
        )
    ].copy()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(summary["metric"], summary["value"].astype(float), color=["#2A9D8F", "#E76F51", "#5B8FF9"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Rate")
    ax.set_title("Proposed Gray-Zone System Simulation")
    ax.tick_params(axis="x", labelrotation=25)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)
