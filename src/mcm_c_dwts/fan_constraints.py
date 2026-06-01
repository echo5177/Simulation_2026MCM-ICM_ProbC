from __future__ import annotations

import pandas as pd
from scipy.optimize import linprog


def _as_list(value: str | list[str] | tuple[str, ...] | set[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    return list(value)


def percent_rule_constraints(
    judge_percent: pd.Series,
    observed_eliminated: str | list[str] | tuple[str, ...] | set[str],
) -> tuple[list[str], list[list[float]], list[float]]:
    active = list(judge_percent.index)
    eliminated = _as_list(observed_eliminated)
    missing = [name for name in eliminated if name not in active]
    if missing:
        raise ValueError(f"Eliminated contestants are not in the active set: {missing}")

    a_ub: list[list[float]] = []
    b_ub: list[float] = []

    survivors = [name for name in active if name not in set(eliminated)]
    for eliminated_name in eliminated:
        eliminated_idx = active.index(eliminated_name)
        eliminated_judge = float(judge_percent.loc[eliminated_name])
        for survivor in survivors:
            row = [0.0] * len(active)
            row[eliminated_idx] = 1.0
            row[active.index(survivor)] = -1.0
            a_ub.append(row)
            b_ub.append(float(judge_percent.loc[survivor]) - eliminated_judge)

    return active, a_ub, b_ub


def _percent_rule_constraints(
    judge_percent: pd.Series,
    observed_eliminated: str,
) -> tuple[list[str], list[list[float]], list[float]]:
    return percent_rule_constraints(judge_percent, observed_eliminated)


def feasible_bounds_percent(
    judge_percent: pd.Series,
    observed_eliminated: str | list[str] | tuple[str, ...] | set[str],
) -> pd.DataFrame:
    active, a_ub, b_ub = percent_rule_constraints(judge_percent, observed_eliminated)
    n = len(active)
    a_eq = [[1.0] * n]
    b_eq = [1.0]
    bounds = [(0.0, 1.0)] * n
    rows: list[dict[str, object]] = []

    for idx, contestant in enumerate(active):
        c = [0.0] * n
        c[idx] = 1.0
        min_res = linprog(
            c,
            A_ub=a_ub,
            b_ub=b_ub,
            A_eq=a_eq,
            b_eq=b_eq,
            bounds=bounds,
            method="highs",
        )
        max_res = linprog(
            [-value for value in c],
            A_ub=a_ub,
            b_ub=b_ub,
            A_eq=a_eq,
            b_eq=b_eq,
            bounds=bounds,
            method="highs",
        )
        rows.append(
            {
                "contestant": contestant,
                "fan_share_min": min_res.fun if min_res.success else float("nan"),
                "fan_share_max": -max_res.fun if max_res.success else float("nan"),
                "min_status": min_res.message,
                "max_status": max_res.message,
            }
        )

    return pd.DataFrame(rows)
