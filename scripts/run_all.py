from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd

from mcm_c_dwts.config import (
    GENERATED_FIGURES_DIR,
    INTERIM_DIR,
    PROCESSED_DIR,
    REPORTS_DIR,
    TABLES_DIR,
    ensure_directories,
)
from mcm_c_dwts.build_panel import build_long_panel
from mcm_c_dwts.data_audit import build_season_audit, write_data_audit_report
from mcm_c_dwts.data_loader import load_raw_data
from mcm_c_dwts.export_tables import export_latex_table
from mcm_c_dwts.plots import plot_judge_score_distribution, plot_season_structure
from mcm_c_dwts.reconstruct_events import (
    active_set_by_week,
    judge_scores_by_week,
    reconstruct_elimination_events,
)


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def main() -> None:
    ensure_directories()

    raw = load_raw_data()
    panel = build_long_panel(raw)
    active_set = active_set_by_week(panel)
    judge_scores = judge_scores_by_week(panel)
    events = reconstruct_elimination_events(panel)
    season_audit = build_season_audit(raw, panel, events)

    panel.to_csv(INTERIM_DIR / "long_panel.csv", index=False)
    active_set.to_csv(INTERIM_DIR / "active_set_by_week.csv", index=False)
    judge_scores.to_csv(INTERIM_DIR / "judge_scores_by_week.csv", index=False)
    events.to_csv(INTERIM_DIR / "elimination_events.csv", index=False)
    season_audit.to_csv(PROCESSED_DIR / "season_audit.csv", index=False)

    export_latex_table(
        season_audit,
        TABLES_DIR / "table_1_data_audit.tex",
        caption="Data audit summary by season.",
    )
    write_data_audit_report(
        raw,
        panel,
        events,
        season_audit,
        REPORTS_DIR / "data_audit_report.md",
    )

    season_fig = GENERATED_FIGURES_DIR / "fig_3_season_structure.png"
    score_fig = GENERATED_FIGURES_DIR / "fig_4_judge_score_distribution.png"
    plot_season_structure(season_audit, season_fig)
    plot_judge_score_distribution(panel, score_fig)

    key_results = pd.DataFrame(
        [
            ("raw_rows", len(raw)),
            ("raw_columns", len(raw.columns)),
            ("seasons", raw["season"].nunique()),
            ("panel_rows", len(panel)),
            ("active_contestant_weeks", int(panel["active"].sum())),
            ("elimination_event_rows", len(events)),
            ("single_elimination_rows", int((events["event_type"] == "single_elimination").sum())),
            ("multi_elimination_rows", int((events["event_type"] == "multi_elimination").sum())),
            ("no_elimination_rows", int((events["event_type"] == "no_elimination").sum())),
        ],
        columns=["metric", "value"],
    )
    key_results.to_csv(REPORTS_DIR / "key_results.csv", index=False)

    pd.DataFrame(
        [
            ("Fig. 3", str(season_fig), "scripts/run_all.py", "2. Data Audit"),
            ("Fig. 4", str(score_fig), "scripts/run_all.py", "2. Data Audit"),
        ],
        columns=["figure_id", "path", "source_script", "paper_location"],
    ).to_csv(REPORTS_DIR / "figure_manifest.csv", index=False)

    write_if_missing(
        REPORTS_DIR / "data_source_log.md",
        "# Data Source Log\n\n- Official CSV: data/raw/2026_MCM_Problem_C_Data.csv\n- Official problem PDF: data/raw/2026_MCM_Problem_C.pdf\n",
    )
    write_if_missing(
        REPORTS_DIR / "citation_verification.md",
        "# Citation Verification\n\nNo external citations have been added yet.\n",
    )
    write_if_missing(
        REPORTS_DIR / "ai_use_log.md",
        "# AI Use Log\n\nRecord AI-assisted planning, coding, checking, and writing here.\n",
    )
    write_if_missing(
        REPORTS_DIR / "sanity_check_report.md",
        "# Sanity Check Report\n\nInitial data audit generated successfully.\n",
    )
    write_if_missing(
        REPORTS_DIR / "submission_checklist.md",
        "# Submission Checklist\n\n- [ ] Summary control number = header control number = AI report team number\n- [ ] Main report within page limit\n- [ ] Every Summary number appears in reports/key_results.csv\n- [ ] Every generated figure appears in reports/figure_manifest.csv\n- [ ] AI Use Report appended after main report\n",
    )

    print(f"Workflow finished at {datetime.now(timezone.utc).isoformat()}")
    print(f"Wrote {REPORTS_DIR / 'key_results.csv'}")


if __name__ == "__main__":
    main()
