from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import ID_COLUMNS, RAW_DATA_FILE, WEEK_SCORE_RE


def score_columns(columns: list[str] | pd.Index) -> list[str]:
    cols = [col for col in columns if WEEK_SCORE_RE.match(col)]
    return sorted(
        cols,
        key=lambda col: (
            int(WEEK_SCORE_RE.match(col).group("week")),
            int(WEEK_SCORE_RE.match(col).group("judge")),
        ),
    )


def week_numbers(columns: list[str] | pd.Index) -> list[int]:
    weeks = {
        int(WEEK_SCORE_RE.match(col).group("week"))
        for col in columns
        if WEEK_SCORE_RE.match(col)
    }
    return sorted(weeks)


def load_raw_data(path: str | Path = RAW_DATA_FILE) -> pd.DataFrame:
    df = pd.read_csv(path, na_values=["N/A", "NA", ""])
    missing = [col for col in ID_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.copy()
    numeric_cols = [
        "celebrity_age_during_season",
        "season",
        "placement",
        *score_columns(df.columns),
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
