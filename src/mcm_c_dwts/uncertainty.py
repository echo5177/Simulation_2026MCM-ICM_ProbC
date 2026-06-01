from __future__ import annotations

import numpy as np
import pandas as pd

from .fan_constraints import _percent_rule_constraints


def sample_feasible_percent(
    judge_percent: pd.Series,
    observed_eliminated: str,
    n_samples: int = 5000,
    seed: int = 2026,
) -> pd.DataFrame:
    active, a_ub, b_ub = _percent_rule_constraints(judge_percent, observed_eliminated)
    rng = np.random.default_rng(seed)
    samples = rng.dirichlet(np.ones(len(active)), size=n_samples)

    feasible_rows = []
    a_ub_arr = np.asarray(a_ub, dtype=float)
    b_ub_arr = np.asarray(b_ub, dtype=float)
    for sample in samples:
        if np.all(a_ub_arr @ sample <= b_ub_arr + 1e-10):
            feasible_rows.append(sample)

    return pd.DataFrame(feasible_rows, columns=active)
