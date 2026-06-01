from __future__ import annotations

import pandas as pd
from scipy.optimize import linprog


def _percent_rule_constraints(
    judge_percent: pd.Series,
    observed_eliminated: str,
) -> tuple[list[str], list[list[float]], list[float]]:
    active = list(judge_percent.index)
    if observed_eliminated not in active:
        raise ValueError(f"{observed_eliminated!r} is not in the active set")

    eliminated_idx = active.index(observed_eliminated)
    a_ub: list[list[float]] = []
    b_ub: list[float] = []
    eliminated_judge = float(judge_percent.loc[observed_eliminated])

    for contestant in active:
        if contestant == observed_eliminated:
            continue
        row = [0.0] * len(active)
        row[eliminated_idx] = 1.0
        row[active.index(contestant)] = -1.0
        a_ub.append(row)
        b_ub.append(float(judge_percent.loc[contestant]) - eliminated_judge)

    return active, a_ub, b_ub


def feasible_bounds_percent(
    judge_percent: pd.Series,
    observed_eliminated: str,
) -> pd.DataFrame:
    active, a_ub, b_ub = _percent_rule_constraints(judge_percent, observed_eliminated)
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
