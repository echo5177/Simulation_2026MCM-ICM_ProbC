from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_season_audit(
    raw: pd.DataFrame,
    panel: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    raw_counts = raw.groupby("season").agg(
        contestants=("celebrity_name", "count"),
        min_placement=("placement", "min"),
        max_placement=("placement", "max"),
    )

    week_counts = (
        panel.loc[panel["active"]]
        .groupby("season")
        .agg(
            active_observations=("celebrity_name", "count"),
            valid_weeks=("week", "nunique"),
            max_active_week=("week", "max"),
        )
    )

    event_counts = events.groupby("season").agg(
        elimination_events=("event_type", lambda s: (s != "no_elimination").sum()),
        no_elimination_weeks=("event_type", lambda s: (s == "no_elimination").sum()),
        multi_elimination_rows=("event_type", lambda s: (s == "multi_elimination").sum()),
    )

    audit = raw_counts.join(week_counts, how="left").join(event_counts, how="left")
    return audit.fillna(0).reset_index().sort_values("season")


def write_data_audit_report(
    raw: pd.DataFrame,
    panel: pd.DataFrame,
    events: pd.DataFrame,
    season_audit: pd.DataFrame,
    path: str | Path,
) -> None:
    score_cells = panel[["judge1_score", "judge2_score", "judge3_score", "judge4_score"]]
    missing_score_cells = int(score_cells.isna().sum().sum())
    zero_score_cells = int((score_cells == 0).sum().sum())

    lines = [
        "# Data Audit Report",
        "",
        "This report is generated from the official raw CSV.",
        "",
        "## Raw Data",
        "",
        f"- Rows: {len(raw)}",
        f"- Columns: {len(raw.columns)}",
        f"- Seasons: {raw['season'].nunique()}",
        f"- Panel rows: {len(panel)}",
        f"- Active contestant-week rows: {int(panel['active'].sum())}",
        f"- Missing judge-score cells: {missing_score_cells}",
        f"- Zero judge-score cells: {zero_score_cells}",
        "",
        "## Season Summary",
        "",
        "```text",
        season_audit.to_string(index=False),
        "```",
        "",
        "## Event Type Counts",
        "",
        "```text",
        events["event_type"].value_counts(dropna=False).to_string(),
        "```",
        "",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
