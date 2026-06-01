from __future__ import annotations

import pandas as pd


def percent_rule(judge_percent: pd.Series, fan_share: pd.Series) -> pd.DataFrame:
    aligned_judge, aligned_fan = judge_percent.align(fan_share, join="inner")
    result = pd.DataFrame(
        {
            "judge_percent": aligned_judge,
            "fan_share": aligned_fan,
        }
    )
    result["combined_percent"] = result["judge_percent"] + result["fan_share"]
    result["eliminated"] = result["combined_percent"] == result["combined_percent"].min()
    return result.sort_values("combined_percent")


def rank_rule(judge_score: pd.Series, fan_support: pd.Series) -> pd.DataFrame:
    aligned_judge, aligned_fan = judge_score.align(fan_support, join="inner")
    result = pd.DataFrame(
        {
            "judge_score": aligned_judge,
            "fan_support": aligned_fan,
        }
    )
    result["judge_rank"] = result["judge_score"].rank(ascending=False, method="min")
    result["fan_rank"] = result["fan_support"].rank(ascending=False, method="min")
    result["combined_rank"] = result["judge_rank"] + result["fan_rank"]
    result["eliminated"] = result["combined_rank"] == result["combined_rank"].max()
    return result.sort_values("combined_rank", ascending=False)


def bottom_two(result: pd.DataFrame, score_column: str) -> pd.Index:
    return result.sort_values(score_column).head(2).index
