import pandas as pd

from mcm_c_dwts.fan_constraints import feasible_bounds_percent
from mcm_c_dwts.fan_estimation import max_entropy_percent_estimate


def test_percent_bounds_and_max_entropy_are_feasible():
    judge = pd.Series({"A": 0.5, "B": 0.3, "C": 0.2})
    bounds = feasible_bounds_percent(judge, observed_eliminated="C")
    estimate = max_entropy_percent_estimate(judge, observed_eliminated="C")

    assert set(bounds["contestant"]) == {"A", "B", "C"}
    assert abs(float(estimate.sum()) - 1.0) < 1e-6
    assert estimate["C"] + judge["C"] <= estimate["A"] + judge["A"] + 1e-6
    assert estimate["C"] + judge["C"] <= estimate["B"] + judge["B"] + 1e-6


def test_multi_elimination_constraints_keep_eliminated_below_survivor():
    judge = pd.Series({"A": 0.4, "B": 0.3, "C": 0.2, "D": 0.1})
    estimate = max_entropy_percent_estimate(judge, observed_eliminated=["C", "D"])

    for eliminated in ["C", "D"]:
        for survivor in ["A", "B"]:
            assert (
                estimate[eliminated] + judge[eliminated]
                <= estimate[survivor] + judge[survivor] + 1e-6
            )
