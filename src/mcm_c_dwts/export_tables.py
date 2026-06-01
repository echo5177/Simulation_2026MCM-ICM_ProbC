from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_latex_table(df: pd.DataFrame, path: str | Path, caption: str = "") -> None:
    Path(path).write_text(
        df.to_latex(index=False, escape=True, caption=caption),
        encoding="utf-8",
    )
