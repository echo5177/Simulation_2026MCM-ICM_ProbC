from __future__ import annotations

import pandas as pd


def gray_zone_flag(combined_score: pd.Series, tau: float) -> bool:
    ordered = combined_score.sort_values()
    if len(ordered) < 2:
        return False
    return bool((ordered.iloc[1] - ordered.iloc[0]) <= tau)


def simulate_gray_zone_system(
    fan_estimates: pd.DataFrame,
    validation_metrics: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    margins = validation_metrics["bottom_two_margin"].dropna()
    positive_margins = margins.loc[margins > 1e-6]
    tau = float(positive_margins.quantile(0.25)) if not positive_margins.empty else 0.01
    rows = []

    for (season, week), group in fan_estimates.groupby(["season", "week"]):
        combined = group.set_index("celebrity_name")["combined_percent"]
        bottom_two = list(combined.sort_values().head(2).index)
        trigger = gray_zone_flag(combined, tau)
        if trigger and len(bottom_two) == 2:
            bottom_group = group.set_index("celebrity_name").loc[bottom_two]
            new_eliminated = bottom_group["judge_total"].idxmin()
        else:
            new_eliminated = combined.idxmin()

        observed = sorted(group.loc[group["observed_eliminated"], "celebrity_name"])
        percent_eliminated = sorted(
            group.loc[group["percent_rule_eliminated"], "celebrity_name"]
        )
        rows.append(
            {
                "season": int(season),
                "week": int(week),
                "tau": tau,
                "gray_zone_triggered": trigger,
                "observed_eliminated": ";".join(observed),
                "percent_eliminated": ";".join(percent_eliminated),
                "proposed_eliminated": new_eliminated,
                "proposed_changes_percent": new_eliminated not in percent_eliminated,
                "proposed_matches_observed": new_eliminated in observed,
            }
        )

    simulation = pd.DataFrame(rows)
    summary = pd.DataFrame(
        [
            {
                "metric": "gray_zone_tau",
                "value": tau,
                "description": "25th percentile of modeled bottom-two combined-score margins.",
            },
            {
                "metric": "gray_zone_trigger_rate",
                "value": simulation["gray_zone_triggered"].mean(),
                "description": "Share of modeled elimination weeks sent to judge save.",
            },
            {
                "metric": "proposed_changes_percent_rate",
                "value": simulation["proposed_changes_percent"].mean(),
                "description": "Share of weeks where proposed system differs from pure percent rule.",
            },
            {
                "metric": "proposed_matches_observed_rate",
                "value": simulation["proposed_matches_observed"].mean(),
                "description": "Share of weeks where proposed single elimination appears in observed eliminated set.",
            },
        ]
    )
    return simulation, summary
