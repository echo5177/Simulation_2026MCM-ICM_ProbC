from __future__ import annotations

import pandas as pd


def active_set_by_week(panel: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "season",
        "week",
        "celebrity_name",
        "ballroom_partner",
        "celebrity_industry",
        "celebrity_homestate",
        "celebrity_homecountry/region",
        "celebrity_age_during_season",
        "results",
        "placement",
        "judge_total",
        "judge_mean",
    ]
    return panel.loc[panel["active"], cols].sort_values(
        ["season", "week", "judge_total", "celebrity_name"],
        ascending=[True, True, False, True],
    )


def judge_scores_by_week(panel: pd.DataFrame) -> pd.DataFrame:
    active = active_set_by_week(panel).copy()
    active["judge_rank"] = active.groupby(["season", "week"])["judge_total"].rank(
        ascending=False,
        method="min",
    )
    active["contestants_active"] = active.groupby(["season", "week"])[
        "celebrity_name"
    ].transform("count")
    return active.sort_values(["season", "week", "judge_rank", "celebrity_name"])


def reconstruct_elimination_events(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for season, season_panel in panel.groupby("season"):
        active_by_week = {
            int(week): set(group.loc[group["active"], "celebrity_name"])
            for week, group in season_panel.groupby("week")
        }
        valid_weeks = [week for week, active in active_by_week.items() if active]

        for week, next_week in zip(valid_weeks, valid_weeks[1:]):
            current = active_by_week[week]
            nxt = active_by_week[next_week]
            eliminated = sorted(current - nxt)
            added = sorted(nxt - current)

            if eliminated:
                for name in eliminated:
                    rows.append(
                        {
                            "season": int(season),
                            "week": week,
                            "next_week": next_week,
                            "event_type": (
                                "multi_elimination"
                                if len(eliminated) > 1
                                else "single_elimination"
                            ),
                            "celebrity_name": name,
                            "active_count": len(current),
                            "next_active_count": len(nxt),
                            "eliminated_count": len(eliminated),
                            "added_count": len(added),
                        }
                    )
            else:
                rows.append(
                    {
                        "season": int(season),
                        "week": week,
                        "next_week": next_week,
                        "event_type": "no_elimination",
                        "celebrity_name": "",
                        "active_count": len(current),
                        "next_active_count": len(nxt),
                        "eliminated_count": 0,
                        "added_count": len(added),
                    }
                )

    return pd.DataFrame(rows).sort_values(["season", "week", "celebrity_name"])
