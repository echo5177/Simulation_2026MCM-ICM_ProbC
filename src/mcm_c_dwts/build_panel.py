from __future__ import annotations

import pandas as pd

from .config import ID_COLUMNS
from .data_loader import week_numbers


def build_long_panel(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    weeks = week_numbers(raw.columns)

    for _, record in raw.iterrows():
        base = {col: record[col] for col in ID_COLUMNS}
        for week in weeks:
            row = dict(base)
            row["week"] = week
            scores = []
            for judge in range(1, 5):
                col = f"week{week}_judge{judge}_score"
                value = record.get(col)
                row[f"judge{judge}_score"] = value
                if pd.notna(value):
                    scores.append(float(value))

            row["judge_count"] = len(scores)
            row["judge_total"] = float(sum(scores)) if scores else float("nan")
            row["judge_mean"] = (
                row["judge_total"] / row["judge_count"] if scores else float("nan")
            )
            row["has_score_record"] = bool(scores)
            row["active"] = bool(scores and row["judge_total"] > 0)
            rows.append(row)

    panel = pd.DataFrame(rows)
    return panel.sort_values(["season", "week", "placement", "celebrity_name"])
