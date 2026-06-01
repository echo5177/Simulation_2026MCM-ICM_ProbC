from __future__ import annotations

import numpy as np
import pandas as pd

from .proposed_system import gray_zone_flag


def _name_set(value: object) -> set[str]:
    if pd.isna(value):
        return set()
    return {name.strip() for name in str(value).split(";") if name.strip()}


def _set_match_rate(df: pd.DataFrame, predicted_col: str) -> float:
    if df.empty:
        return float("nan")
    return float(
        df.apply(
            lambda row: _name_set(row["observed_eliminated"])
            == _name_set(row[predicted_col]),
            axis=1,
        ).mean()
    )


def _mean_overlap(df: pd.DataFrame, predicted_col: str) -> float:
    if df.empty:
        return float("nan")

    def overlap(row: pd.Series) -> float:
        observed = _name_set(row["observed_eliminated"])
        predicted = _name_set(row[predicted_col])
        if not observed:
            return 0.0
        return len(observed.intersection(predicted)) / len(observed)

    return float(df.apply(overlap, axis=1).mean())


def build_baseline_comparison(
    counterfactuals: pd.DataFrame,
    validation: pd.DataFrame,
) -> pd.DataFrame:
    rows = [
        {
            "candidate_rule": "Percent + inferred fan",
            "exact_match_rate": float(validation["percent_reproduces_observed"].mean()),
            "mean_observed_overlap": 1.0,
            "modeled_weeks": len(validation),
            "interpretation": "Constraint-consistent reconstruction",
        },
        {
            "candidate_rule": "Rank + inferred fan",
            "exact_match_rate": _set_match_rate(counterfactuals, "rank_eliminated"),
            "mean_observed_overlap": _mean_overlap(counterfactuals, "rank_eliminated"),
            "modeled_weeks": len(counterfactuals),
            "interpretation": "Rule-change counterfactual",
        },
        {
            "candidate_rule": "Judge-only bottom",
            "exact_match_rate": _set_match_rate(counterfactuals, "judge_only_bottom"),
            "mean_observed_overlap": _mean_overlap(counterfactuals, "judge_only_bottom"),
            "modeled_weeks": len(counterfactuals),
            "interpretation": "No fan vote baseline",
        },
        {
            "candidate_rule": "Fan-only bottom",
            "exact_match_rate": _set_match_rate(counterfactuals, "fan_only_bottom"),
            "mean_observed_overlap": _mean_overlap(counterfactuals, "fan_only_bottom"),
            "modeled_weeks": len(counterfactuals),
            "interpretation": "Estimated audience-only baseline",
        },
    ]
    return pd.DataFrame(rows)


def build_rule_switch_cases(
    counterfactuals: pd.DataFrame,
    validation: pd.DataFrame,
    top_n: int = 12,
) -> pd.DataFrame:
    merged = counterfactuals.merge(
        validation[
            [
                "season",
                "week",
                "bottom_two_margin",
                "mean_fan_share_width",
                "max_fan_share_width",
            ]
        ],
        on=["season", "week"],
        how="left",
    )
    switches = merged.loc[merged["rank_percent_different"]].copy()
    if switches.empty:
        return switches
    switches["switch_severity"] = (
        switches["eliminated_count"] - switches["rank_overlap_with_percent"]
    )
    return (
        switches.sort_values(
            ["switch_severity", "mean_fan_share_width", "active_count"],
            ascending=[False, False, False],
        )
        .head(top_n)
        .reset_index(drop=True)
    )


def build_fan_rescue_cases(
    fan_estimates: pd.DataFrame,
    top_n: int = 12,
) -> pd.DataFrame:
    rescue = fan_estimates.loc[fan_estimates["fan_rescue_gap"] > 0].copy()
    if rescue.empty:
        return rescue
    rescue["case_id"] = (
        "S"
        + rescue["season"].astype(str)
        + " W"
        + rescue["week"].astype(str)
        + " "
        + rescue["celebrity_name"]
    )
    columns = [
        "case_id",
        "season",
        "week",
        "celebrity_name",
        "judge_rank",
        "fan_rank_est",
        "fan_rescue_gap",
        "fan_share_est",
        "combined_percent",
        "observed_eliminated",
        "results",
    ]
    return (
        rescue[columns]
        .sort_values(["fan_rescue_gap", "fan_share_est"], ascending=[False, False])
        .head(top_n)
        .reset_index(drop=True)
    )


def build_contestant_instability(
    fan_estimates: pd.DataFrame,
    min_weeks: int = 3,
    top_n: int = 12,
) -> pd.DataFrame:
    grouped = (
        fan_estimates.groupby(["celebrity_name", "season"])
        .agg(
            modeled_weeks=("week", "nunique"),
            mean_judge_rank=("judge_rank", "mean"),
            mean_fan_rank=("fan_rank_est", "mean"),
            mean_fan_rescue_gap=("fan_rescue_gap", "mean"),
            mean_controversy_index=("controversy_index", "mean"),
            max_controversy_index=("controversy_index", "max"),
            mean_fan_share=("fan_share_est", "mean"),
            final_placement=("placement", "min"),
            results=("results", "first"),
        )
        .reset_index()
    )
    grouped = grouped.loc[grouped["modeled_weeks"] >= min_weeks].copy()
    return (
        grouped.sort_values(
            [
                "max_controversy_index",
                "mean_controversy_index",
                "mean_fan_rescue_gap",
            ],
            ascending=[False, False, False],
        )
        .head(top_n)
        .reset_index(drop=True)
    )


def _simulate_for_tau(fan_estimates: pd.DataFrame, tau: float) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (season, week), group in fan_estimates.groupby(["season", "week"]):
        indexed = group.set_index("celebrity_name")
        combined = indexed["combined_percent"]
        bottom_two = list(combined.sort_values().head(2).index)
        trigger = gray_zone_flag(combined, tau)

        if trigger and len(bottom_two) == 2:
            new_eliminated = indexed.loc[bottom_two, "judge_total"].idxmin()
        else:
            new_eliminated = combined.idxmin()

        observed = set(group.loc[group["observed_eliminated"], "celebrity_name"])
        percent = set(group.loc[group["percent_rule_eliminated"], "celebrity_name"])
        rows.append(
            {
                "season": int(season),
                "week": int(week),
                "gray_zone_triggered": trigger,
                "proposed_changes_percent": new_eliminated not in percent,
                "proposed_matches_observed": new_eliminated in observed,
            }
        )
    return pd.DataFrame(rows)


def build_threshold_sensitivity(
    fan_estimates: pd.DataFrame,
    validation: pd.DataFrame,
) -> pd.DataFrame:
    margins = validation["bottom_two_margin"].dropna()
    positive_margins = margins.loc[margins > 1e-6]
    configs: list[tuple[str, float | None]] = [
        ("No gray zone", None),
        ("5th pct.", 0.05),
        ("10th pct.", 0.10),
        ("25th pct.", 0.25),
        ("50th pct.", 0.50),
        ("75th pct.", 0.75),
        ("90th pct.", 0.90),
    ]

    rows = []
    for label, quantile in configs:
        if quantile is None or positive_margins.empty:
            tau = -1.0
            x_value = 0.0
        else:
            tau = float(positive_margins.quantile(quantile))
            x_value = float(quantile)
        simulation = _simulate_for_tau(fan_estimates, tau)
        rows.append(
            {
                "threshold_label": label,
                "threshold_quantile": x_value,
                "tau": np.nan if quantile is None else tau,
                "gray_zone_trigger_rate": simulation["gray_zone_triggered"].mean(),
                "proposed_changes_percent_rate": simulation[
                    "proposed_changes_percent"
                ].mean(),
                "proposed_matches_observed_rate": simulation[
                    "proposed_matches_observed"
                ].mean(),
                "modeled_weeks": len(simulation),
            }
        )
    return pd.DataFrame(rows)


def build_constraint_summary(validation: pd.DataFrame) -> pd.DataFrame:
    diagnostics = validation.copy()
    diagnostics["linear_constraints"] = diagnostics["eliminated_count"] * (
        diagnostics["active_count"] - diagnostics["eliminated_count"]
    )
    rows = [
        ("Modeled elimination weeks", len(diagnostics), "season-week events"),
        ("Mean active contestants", diagnostics["active_count"].mean(), "contestants"),
        ("Median active contestants", diagnostics["active_count"].median(), "contestants"),
        ("Mean eliminated contestants", diagnostics["eliminated_count"].mean(), "contestants"),
        ("Total linear inequalities", diagnostics["linear_constraints"].sum(), "constraints"),
        ("Mean inequalities per week", diagnostics["linear_constraints"].mean(), "constraints"),
        ("Maximum inequalities in a week", diagnostics["linear_constraints"].max(), "constraints"),
        ("Median bottom-two margin", diagnostics["bottom_two_margin"].median(), "combined share"),
    ]
    return pd.DataFrame(rows, columns=["diagnostic", "value", "unit"])


def build_event_type_summary(
    counterfactuals: pd.DataFrame,
    validation: pd.DataFrame,
) -> pd.DataFrame:
    diagnostics = counterfactuals.merge(
        validation[
            [
                "season",
                "week",
                "mean_fan_share_width",
                "bottom_two_margin",
                "percent_reproduces_observed",
            ]
        ],
        on=["season", "week"],
        how="left",
    )
    diagnostics["linear_constraints"] = diagnostics["eliminated_count"] * (
        diagnostics["active_count"] - diagnostics["eliminated_count"]
    )
    return (
        diagnostics.groupby("event_type")
        .agg(
            weeks=("week", "count"),
            mean_active=("active_count", "mean"),
            mean_constraints=("linear_constraints", "mean"),
            rank_percent_diff_rate=("rank_percent_different", "mean"),
            fan_override_rate=("fan_override_judges", "mean"),
            mean_width=("mean_fan_share_width", "mean"),
            median_margin=("bottom_two_margin", "median"),
        )
        .reset_index()
    )


def build_era_rule_summary(
    counterfactuals: pd.DataFrame,
    validation: pd.DataFrame,
) -> pd.DataFrame:
    diagnostics = counterfactuals.merge(
        validation[
            [
                "season",
                "week",
                "mean_fan_share_width",
                "bottom_two_margin",
            ]
        ],
        on=["season", "week"],
        how="left",
    )
    bins = [0, 10, 20, 30, 40]
    labels = ["S1-S10", "S11-S20", "S21-S30", "S31-S34"]
    diagnostics["season_era"] = pd.cut(
        diagnostics["season"],
        bins=bins,
        labels=labels,
        right=True,
    )
    return (
        diagnostics.groupby("season_era", observed=True)
        .agg(
            modeled_weeks=("week", "count"),
            mean_active=("active_count", "mean"),
            rank_percent_diff_rate=("rank_percent_different", "mean"),
            fan_override_rate=("fan_override_judges", "mean"),
            mean_width=("mean_fan_share_width", "mean"),
            median_margin=("bottom_two_margin", "median"),
        )
        .reset_index()
    )


def build_selected_effects_table(effects: pd.DataFrame) -> pd.DataFrame:
    selected_terms = [
        ("judge_score_ols", "celebrity_age_during_season", "Judge score: age"),
        ("fan_support_ols", "celebrity_age_during_season", "Fan support: age"),
        ("survival_cox", "celebrity_age_during_season", "Survival hazard: age"),
        ("judge_score_ols", "C(celebrity_industry)[T.Athlete]", "Judge score: athlete"),
        ("judge_score_ols", "C(celebrity_industry)[T.Model]", "Judge score: model"),
        ("fan_support_ols", "C(celebrity_industry)[T.TV Personality]", "Fan support: TV personality"),
        ("fan_support_ols", "C(celebrity_industry)[T.Radio Personality]", "Fan support: radio personality"),
    ]
    rows = []
    for model, term, label in selected_terms:
        match = effects.loc[(effects["model"] == model) & (effects["term"] == term)]
        if match.empty:
            continue
        row = match.iloc[0]
        rows.append(
            {
                "effect": label,
                "estimate": row.get("estimate"),
                "conf_low": row.get("conf_low"),
                "conf_high": row.get("conf_high"),
                "p_value": row.get("p_value"),
            }
        )
    return pd.DataFrame(rows)
