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
