import pandas as pd

from mcm_c_dwts.voting_rules import percent_rule, rank_rule


def test_percent_rule_eliminates_lowest_combined_score():
    judge = pd.Series({"A": 0.4, "B": 0.35, "C": 0.25})
    fan = pd.Series({"A": 0.2, "B": 0.3, "C": 0.1})
    result = percent_rule(judge, fan)
    eliminated = set(result.loc[result["eliminated"]].index)
    assert eliminated == {"C"}


def test_rank_rule_eliminates_worst_combined_rank():
    judge = pd.Series({"A": 30, "B": 28, "C": 20})
    fan = pd.Series({"A": 10, "B": 30, "C": 20})
    result = rank_rule(judge, fan)
    eliminated = set(result.loc[result["eliminated"]].index)
    assert eliminated == {"C"}
