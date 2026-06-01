from __future__ import annotations

import pandas as pd


def gray_zone_flag(combined_score: pd.Series, tau: float) -> bool:
    ordered = combined_score.sort_values()
    if len(ordered) < 2:
        return False
    return bool((ordered.iloc[1] - ordered.iloc[0]) <= tau)
