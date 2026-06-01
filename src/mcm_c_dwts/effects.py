from __future__ import annotations

import pandas as pd
import statsmodels.formula.api as smf
from lifelines import CoxPHFitter


def fit_judge_score_baseline(panel: pd.DataFrame):
    active = panel.loc[panel["active"]].copy()
    active["celebrity_age_during_season"] = active[
        "celebrity_age_during_season"
    ].fillna(active["celebrity_age_during_season"].median())
    formula = "judge_mean ~ celebrity_age_during_season + C(celebrity_industry)"
    return smf.ols(formula, data=active).fit()


def _tidy_statsmodels_result(result, model_name: str) -> pd.DataFrame:
    conf = result.conf_int()
    rows = []
    for term in result.params.index:
        rows.append(
            {
                "model": model_name,
                "term": term,
                "estimate": result.params.loc[term],
                "conf_low": conf.loc[term, 0],
                "conf_high": conf.loc[term, 1],
                "p_value": result.pvalues.loc[term],
            }
        )
    return pd.DataFrame(rows)


def _survival_dataset(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, group in panel.groupby(["celebrity_name", "season"]):
        first = group.iloc[0]
        active_weeks = group.loc[group["active"], "week"]
        if active_weeks.empty:
            continue
        rows.append(
            {
                "celebrity_name": first["celebrity_name"],
                "season": int(first["season"]),
                "duration_weeks": int(active_weeks.max()),
                "event_observed": str(first["results"]).startswith("Eliminated"),
                "celebrity_age_during_season": first["celebrity_age_during_season"],
                "celebrity_industry": first["celebrity_industry"],
            }
        )
    return pd.DataFrame(rows)


def build_effect_model_results(panel: pd.DataFrame, fan_estimates: pd.DataFrame) -> pd.DataFrame:
    outputs: list[pd.DataFrame] = []

    try:
        judge_model = fit_judge_score_baseline(panel)
        outputs.append(_tidy_statsmodels_result(judge_model, "judge_score_ols"))
    except Exception as exc:  # noqa: BLE001
        outputs.append(
            pd.DataFrame(
                [{"model": "judge_score_ols", "term": "MODEL_FAILED", "estimate": str(exc)}]
            )
        )

    try:
        fan_data = fan_estimates.copy()
        fan_data["celebrity_age_during_season"] = fan_data[
            "celebrity_age_during_season"
        ].fillna(fan_data["celebrity_age_during_season"].median())
        fan_model = smf.ols(
            "fan_share_est ~ celebrity_age_during_season + C(celebrity_industry)",
            data=fan_data,
        ).fit()
        outputs.append(_tidy_statsmodels_result(fan_model, "fan_support_ols"))
    except Exception as exc:  # noqa: BLE001
        outputs.append(
            pd.DataFrame(
                [{"model": "fan_support_ols", "term": "MODEL_FAILED", "estimate": str(exc)}]
            )
        )

    try:
        survival = _survival_dataset(panel)
        survival = pd.get_dummies(
            survival[
                [
                    "duration_weeks",
                    "event_observed",
                    "celebrity_age_during_season",
                    "celebrity_industry",
                ]
            ].dropna(),
            columns=["celebrity_industry"],
            drop_first=True,
            dtype=float,
        )
        industry_cols = [col for col in survival.columns if col.startswith("celebrity_industry_")]
        keep_cols = [
            "duration_weeks",
            "event_observed",
            "celebrity_age_during_season",
            *industry_cols[:8],
        ]
        cph = CoxPHFitter(penalizer=0.1)
        cph.fit(
            survival[keep_cols],
            duration_col="duration_weeks",
            event_col="event_observed",
        )
        cox = cph.summary.reset_index().rename(
            columns={
                "covariate": "term",
                "coef": "estimate",
                "coef lower 95%": "conf_low",
                "coef upper 95%": "conf_high",
                "p": "p_value",
            }
        )
        cox["model"] = "survival_cox"
        outputs.append(cox[["model", "term", "estimate", "conf_low", "conf_high", "p_value"]])
    except Exception as exc:  # noqa: BLE001
        outputs.append(
            pd.DataFrame(
                [{"model": "survival_cox", "term": "MODEL_FAILED", "estimate": str(exc)}]
            )
        )

    return pd.concat(outputs, ignore_index=True, sort=False)
