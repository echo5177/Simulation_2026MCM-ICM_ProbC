from __future__ import annotations

import pandas as pd

from .voting_rules import percent_rule, rank_rule


def compare_rank_percent(
    judge_score: pd.Series,
    judge_percent: pd.Series,
    fan_support: pd.Series,
) -> dict[str, object]:
    percent_result = percent_rule(judge_percent, fan_support)
    rank_result = rank_rule(judge_score, fan_support)
    percent_elim = sorted(percent_result.loc[percent_result["eliminated"]].index)
    rank_elim = sorted(rank_result.loc[rank_result["eliminated"]].index)
    return {
        "percent_eliminated": ";".join(percent_elim),
        "rank_eliminated": ";".join(rank_elim),
        "different": percent_elim != rank_elim,
    }
