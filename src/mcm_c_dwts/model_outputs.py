from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .fan_constraints import feasible_bounds_percent
from .fan_estimation import max_entropy_percent_estimate


@dataclass(frozen=True)
class InferenceOutputs:
    fan_vote_estimates: pd.DataFrame
    validation_metrics: pd.DataFrame
    rule_counterfactuals: pd.DataFrame
    model_issue_log: pd.DataFrame


def _event_groups(events: pd.DataFrame):
    elimination_events = events.loc[events["event_type"] != "no_elimination"].copy()
    for key, group in elimination_events.groupby(["season", "week", "next_week"]):
        eliminated = sorted(name for name in group["celebrity_name"].dropna() if name)
        if eliminated:
            yield key, eliminated, group.iloc[0].to_dict()


def _bottom_names(series: pd.Series, k: int) -> list[str]:
    return list(series.sort_values(ascending=True).head(k).index)


def _top_bad_rank_names(series: pd.Series, k: int) -> list[str]:
    return list(series.sort_values(ascending=False).head(k).index)


def infer_fan_support_outputs(
    judge_scores: pd.DataFrame,
    events: pd.DataFrame,
) -> InferenceOutputs:
    estimate_rows: list[pd.DataFrame] = []
    validation_rows: list[dict[str, object]] = []
    counterfactual_rows: list[dict[str, object]] = []
    issue_rows: list[dict[str, object]] = []

    active_lookup = {
        (int(season), int(week)): group.copy()
        for (season, week), group in judge_scores.groupby(["season", "week"])
    }

    for (season, week, next_week), eliminated, event_meta in _event_groups(events):
        season = int(season)
        week = int(week)
        next_week = int(next_week)
        key = {"season": season, "week": week, "next_week": next_week}
        active = active_lookup.get((season, week))
        if active is None or active.empty:
            issue_rows.append({**key, "issue": "missing_active_set"})
            continue

        active = active.set_index("celebrity_name", drop=False)
        missing = [name for name in eliminated if name not in active.index]
        if missing:
            issue_rows.append({**key, "issue": f"missing_eliminated:{';'.join(missing)}"})
            continue

        judge_total = active["judge_total"].astype(float)
        if float(judge_total.sum()) <= 0:
            issue_rows.append({**key, "issue": "nonpositive_judge_total"})
            continue

        judge_percent = judge_total / judge_total.sum()
        try:
            bounds = feasible_bounds_percent(judge_percent, eliminated)
            fan_share = max_entropy_percent_estimate(judge_percent, eliminated)
        except Exception as exc:  # noqa: BLE001 - keep full issue trail for sanity report
            issue_rows.append({**key, "issue": type(exc).__name__, "detail": str(exc)})
            continue

        k = len(eliminated)
        result = active[[
            "celebrity_name",
            "ballroom_partner",
            "celebrity_industry",
            "celebrity_homestate",
            "celebrity_homecountry/region",
            "celebrity_age_during_season",
            "results",
            "placement",
            "judge_total",
            "judge_mean",
            "judge_rank",
            "contestants_active",
        ]].copy()
        result["season"] = season
        result["week"] = week
        result["next_week"] = next_week
        result["event_type"] = event_meta["event_type"]
        result["observed_eliminated"] = result.index.isin(eliminated)
        result["judge_percent"] = judge_percent
        result["fan_share_est"] = fan_share.reindex(result.index)
        result["fan_rank_est"] = result["fan_share_est"].rank(ascending=False, method="min")
        result["combined_percent"] = result["judge_percent"] + result["fan_share_est"]
        result["combined_percent_rank"] = result["combined_percent"].rank(
            ascending=True,
            method="min",
        )
        result["rank_rule_score"] = result["judge_rank"] + result["fan_rank_est"]
        result["rank_rule_bad_rank"] = result["rank_rule_score"].rank(
            ascending=False,
            method="min",
        )
        result["fan_rescue_gap"] = result["judge_rank"] - result["fan_rank_est"]
        result["controversy_index"] = (result["judge_rank"] - result["fan_rank_est"]).abs()

        bounds = bounds.rename(columns={"contestant": "celebrity_name"}).set_index(
            "celebrity_name"
        )
        result = result.join(bounds[["fan_share_min", "fan_share_max"]])
        result["fan_share_width"] = result["fan_share_max"] - result["fan_share_min"]

        percent_bottom = _bottom_names(result["combined_percent"], k)
        rank_bottom = _top_bad_rank_names(result["rank_rule_score"], k)
        judge_bottom = _bottom_names(result["judge_total"], k)
        fan_bottom = _bottom_names(result["fan_share_est"], k)
        bottom_two = _bottom_names(result["combined_percent"], min(2, len(result)))
        sorted_combined = result["combined_percent"].sort_values()
        bottom_margin = (
            float(sorted_combined.iloc[1] - sorted_combined.iloc[0])
            if len(sorted_combined) >= 2
            else np.nan
        )

        result["percent_rule_eliminated"] = result.index.isin(percent_bottom)
        result["rank_rule_eliminated"] = result.index.isin(rank_bottom)
        estimate_rows.append(result.reset_index(drop=True))

        observed_set = set(eliminated)
        percent_set = set(percent_bottom)
        rank_set = set(rank_bottom)
        validation_rows.append(
            {
                **key,
                "event_type": event_meta["event_type"],
                "active_count": int(event_meta["active_count"]),
                "eliminated_count": k,
                "observed_eliminated": ";".join(eliminated),
                "percent_predicted_bottom": ";".join(percent_bottom),
                "percent_reproduces_observed": observed_set == percent_set,
                "observed_in_bottom_two": bool(observed_set.intersection(bottom_two)),
                "mean_fan_share_width": float(result["fan_share_width"].mean()),
                "max_fan_share_width": float(result["fan_share_width"].max()),
                "bottom_two_margin": bottom_margin,
            }
        )
        counterfactual_rows.append(
            {
                **key,
                "event_type": event_meta["event_type"],
                "active_count": int(event_meta["active_count"]),
                "eliminated_count": k,
                "observed_eliminated": ";".join(eliminated),
                "percent_eliminated": ";".join(percent_bottom),
                "rank_eliminated": ";".join(rank_bottom),
                "judge_only_bottom": ";".join(judge_bottom),
                "fan_only_bottom": ";".join(fan_bottom),
                "rank_percent_different": percent_set != rank_set,
                "fan_override_judges": percent_set != set(judge_bottom),
                "rank_overlap_with_percent": len(percent_set.intersection(rank_set)),
            }
        )

    return InferenceOutputs(
        fan_vote_estimates=pd.concat(estimate_rows, ignore_index=True)
        if estimate_rows
        else pd.DataFrame(),
        validation_metrics=pd.DataFrame(validation_rows),
        rule_counterfactuals=pd.DataFrame(counterfactual_rows),
        model_issue_log=pd.DataFrame(issue_rows),
    )


def build_rule_summary(counterfactuals: pd.DataFrame) -> pd.DataFrame:
    if counterfactuals.empty:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "metric": "modeled_elimination_weeks",
                "value": len(counterfactuals),
                "description": "Elimination weeks processed by the fan-support model.",
            },
            {
                "metric": "outcome_difference_rate",
                "value": counterfactuals["rank_percent_different"].mean(),
                "description": "Share of modeled weeks where rank and percent rules disagree.",
            },
            {
                "metric": "fan_override_rate",
                "value": counterfactuals["fan_override_judges"].mean(),
                "description": "Share of modeled weeks where fan support changes judge-only bottom set.",
            },
            {
                "metric": "mean_rank_percent_overlap",
                "value": counterfactuals["rank_overlap_with_percent"].mean(),
                "description": "Average overlap between rank-rule and percent-rule eliminated sets.",
            },
        ]
    )
