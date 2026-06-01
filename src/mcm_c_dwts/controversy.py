from __future__ import annotations

import pandas as pd


DEFAULT_CASES = {
    "Jerry Rice",
    "Billy Ray Cyrus",
    "Bristol Palin",
    "Bobby Bones",
}


def controversy_case_panel(panel: pd.DataFrame, names: set[str] | None = None) -> pd.DataFrame:
    target_names = names or DEFAULT_CASES
    return panel.loc[panel["celebrity_name"].isin(target_names)].copy()


def build_controversy_cases(
    panel: pd.DataFrame,
    fan_estimates: pd.DataFrame,
    names: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    target_names = names or DEFAULT_CASES
    trajectory = fan_estimates.loc[
        fan_estimates["celebrity_name"].isin(target_names)
    ].copy()

    if trajectory.empty:
        return trajectory, pd.DataFrame()

    summary = (
        trajectory.groupby(["celebrity_name", "season"])
        .agg(
            modeled_weeks=("week", "nunique"),
            mean_judge_rank=("judge_rank", "mean"),
            mean_fan_rank=("fan_rank_est", "mean"),
            mean_fan_rescue_gap=("fan_rescue_gap", "mean"),
            max_controversy_index=("controversy_index", "max"),
            mean_fan_share=("fan_share_est", "mean"),
            final_placement=("placement", "min"),
        )
        .reset_index()
    )

    raw_results = (
        panel.loc[panel["celebrity_name"].isin(target_names)]
        .groupby(["celebrity_name", "season"])
        .agg(results=("results", "first"))
        .reset_index()
    )
    summary = summary.merge(raw_results, on=["celebrity_name", "season"], how="left")
    return trajectory, summary.sort_values(
        ["max_controversy_index", "celebrity_name"],
        ascending=[False, True],
    )
