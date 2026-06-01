from __future__ import annotations

import pandas as pd


DEFAULT_CASES = {
    "Jerry Rice",
    "Billy Ray Cyrus",
    "Bristol Palin",
    "Bobby Bones",
}


def controversy_case_panel(panel: pd.DataFrame, names: set[str] | None = None) -> pd.DataFrame:
    target_names = names or DEFAULT_CASES
    return panel.loc[panel["celebrity_name"].isin(target_names)].copy()
