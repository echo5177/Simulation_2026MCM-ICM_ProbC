from __future__ import annotations

import cvxpy as cp
import pandas as pd

from .fan_constraints import _percent_rule_constraints


def max_entropy_percent_estimate(
    judge_percent: pd.Series,
    observed_eliminated: str,
    prior: pd.Series | None = None,
    smooth_weight: float = 0.0,
) -> pd.Series:
    active, a_ub, b_ub = _percent_rule_constraints(judge_percent, observed_eliminated)
    n = len(active)
    fan = cp.Variable(n, nonneg=True)
    constraints = [cp.sum(fan) == 1.0]

    for row, bound in zip(a_ub, b_ub):
        constraints.append(cp.sum(cp.multiply(row, fan)) <= bound)

    objective = cp.sum(cp.entr(fan))
    if prior is not None and smooth_weight > 0:
        prior_values = prior.reindex(active).fillna(1.0 / n).to_numpy(dtype=float)
        objective -= smooth_weight * cp.sum_squares(fan - prior_values)

    problem = cp.Problem(cp.Maximize(objective), constraints)
    problem.solve()

    if fan.value is None:
        raise RuntimeError(f"CVXPY failed to solve fan estimate: {problem.status}")
    return pd.Series(fan.value, index=active, name="fan_share")
