from __future__ import annotations

import pandas as pd
import statsmodels.formula.api as smf


def fit_judge_score_baseline(panel: pd.DataFrame):
    active = panel.loc[panel["active"]].copy()
    active["celebrity_age_during_season"] = active[
        "celebrity_age_during_season"
    ].fillna(active["celebrity_age_during_season"].median())
    formula = "judge_mean ~ celebrity_age_during_season + C(celebrity_industry)"
    return smf.ols(formula, data=active).fit()
