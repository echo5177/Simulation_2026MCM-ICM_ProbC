from __future__ import annotations

import pandas as pd

from mcm_c_dwts.diagnostics import (
    build_baseline_comparison,
    build_constraint_summary,
    build_threshold_sensitivity,
)


def test_baseline_comparison_handles_multi_name_sets():
    counterfactuals = pd.DataFrame(
        [
            {
                "observed_eliminated": "A;B",
                "rank_eliminated": "B;A",
                "judge_only_bottom": "A;C",
                "fan_only_bottom": "D;E",
            },
            {
                "observed_eliminated": "C",
                "rank_eliminated": "D",
                "judge_only_bottom": "C",
                "fan_only_bottom": "C",
            },
        ]
    )
    validation = pd.DataFrame({"percent_reproduces_observed": [True, True]})

    result = build_baseline_comparison(counterfactuals, validation)

    rank_rate = result.loc[
        result["candidate_rule"] == "Rank + inferred fan", "exact_match_rate"
    ].iloc[0]
    judge_overlap = result.loc[
        result["candidate_rule"] == "Judge-only bottom", "mean_observed_overlap"
    ].iloc[0]
    assert rank_rate == 0.5
    assert judge_overlap == 0.75


def test_threshold_sensitivity_includes_no_gray_zone_baseline():
    fan_estimates = pd.DataFrame(
        [
            {
                "season": 1,
                "week": 1,
                "celebrity_name": "A",
                "combined_percent": 0.2,
                "judge_total": 20,
                "observed_eliminated": True,
                "percent_rule_eliminated": True,
            },
            {
                "season": 1,
                "week": 1,
                "celebrity_name": "B",
                "combined_percent": 0.25,
                "judge_total": 18,
                "observed_eliminated": False,
                "percent_rule_eliminated": False,
            },
        ]
    )
    validation = pd.DataFrame({"bottom_two_margin": [0.05]})

    result = build_threshold_sensitivity(fan_estimates, validation)

    assert result["threshold_label"].iloc[0] == "No gray zone"
    assert result["gray_zone_trigger_rate"].iloc[0] == 0.0
    assert result["modeled_weeks"].iloc[0] == 1


def test_constraint_summary_counts_pairwise_inequalities():
    validation = pd.DataFrame(
        {
            "active_count": [6, 5],
            "eliminated_count": [1, 2],
            "bottom_two_margin": [0.1, 0.2],
        }
    )

    result = build_constraint_summary(validation)

    total_constraints = result.loc[
        result["diagnostic"] == "Total linear inequalities", "value"
    ].iloc[0]
    assert total_constraints == 11
