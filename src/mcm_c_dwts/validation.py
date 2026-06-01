from __future__ import annotations

import pandas as pd

from .voting_rules import percent_rule


def validate_percent_elimination(
    judge_percent: pd.Series,
    fan_share: pd.Series,
    observed_eliminated: str,
) -> dict[str, object]:
    result = percent_rule(judge_percent, fan_share)
    predicted = list(result.loc[result["eliminated"]].index)
    return {
        "observed_eliminated": observed_eliminated,
        "predicted_eliminated": ";".join(predicted),
        "match": observed_eliminated in predicted,
        "bottom_score": float(result["combined_percent"].min()),
    }
