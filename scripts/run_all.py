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
from mcm_c_dwts.controversy import build_controversy_cases
from mcm_c_dwts.effects import build_effect_model_results
from mcm_c_dwts.export_tables import export_latex_table
from mcm_c_dwts.model_outputs import build_rule_summary, infer_fan_support_outputs
from mcm_c_dwts.plots import (
    plot_controversy_cases,
    plot_effects_forest,
    plot_fan_intervals,
    plot_judge_score_distribution,
    plot_rule_comparison_heatmap,
    plot_season_structure,
    plot_system_comparison,
    plot_uncertainty_heatmap,
    plot_validation_dashboard,
)
from mcm_c_dwts.proposed_system import simulate_gray_zone_system
from mcm_c_dwts.reconstruct_events import (
    active_set_by_week,
    judge_scores_by_week,
    reconstruct_elimination_events,
)


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> None:
    ensure_directories()

    raw = load_raw_data()
    panel = build_long_panel(raw)
    active_set = active_set_by_week(panel)
    judge_scores = judge_scores_by_week(panel)
    events = reconstruct_elimination_events(panel)
    season_audit = build_season_audit(raw, panel, events)
    inference = infer_fan_support_outputs(judge_scores, events)
    fan_estimates = inference.fan_vote_estimates
    validation = inference.validation_metrics
    counterfactuals = inference.rule_counterfactuals
    rule_summary = build_rule_summary(counterfactuals)
    controversy_trajectory, controversy_summary = build_controversy_cases(
        panel,
        fan_estimates,
    )
    effects = build_effect_model_results(panel, fan_estimates)
    proposed_simulation, proposed_summary = simulate_gray_zone_system(
        fan_estimates,
        validation,
    )

    panel.to_csv(INTERIM_DIR / "long_panel.csv", index=False)
    active_set.to_csv(INTERIM_DIR / "active_set_by_week.csv", index=False)
    judge_scores.to_csv(INTERIM_DIR / "judge_scores_by_week.csv", index=False)
    events.to_csv(INTERIM_DIR / "elimination_events.csv", index=False)
    season_audit.to_csv(PROCESSED_DIR / "season_audit.csv", index=False)
    fan_estimates.to_csv(PROCESSED_DIR / "fan_vote_estimates.csv", index=False)
    validation.to_csv(PROCESSED_DIR / "validation_metrics.csv", index=False)
    counterfactuals.to_csv(PROCESSED_DIR / "rule_counterfactuals.csv", index=False)
    rule_summary.to_csv(PROCESSED_DIR / "rule_comparison_summary.csv", index=False)
    controversy_trajectory.to_csv(PROCESSED_DIR / "controversy_case_trajectories.csv", index=False)
    controversy_summary.to_csv(PROCESSED_DIR / "controversy_cases.csv", index=False)
    effects.to_csv(PROCESSED_DIR / "effects_model_results.csv", index=False)
    proposed_simulation.to_csv(PROCESSED_DIR / "new_system_simulation.csv", index=False)
    proposed_summary.to_csv(PROCESSED_DIR / "new_system_summary.csv", index=False)
    inference.model_issue_log.to_csv(PROCESSED_DIR / "model_issue_log.csv", index=False)

    export_latex_table(
        season_audit,
        TABLES_DIR / "table_1_data_audit.tex",
        caption="Data audit summary by season.",
    )
    voting_rule_table = pd.DataFrame(
        [
            {
                "Rule": "Percent",
                "Score": "judge share + fan share",
                "Elimination": "Lowest combined percent",
            },
            {
                "Rule": "Rank",
                "Score": "judge rank + fan rank",
                "Elimination": "Worst combined rank",
            },
            {
                "Rule": "Bottom-two judge save",
                "Score": "combined score first, judge decision in bottom two",
                "Elimination": "Judge save determines survivor in gray zone",
            },
        ]
    )
    export_latex_table(
        voting_rule_table,
        TABLES_DIR / "table_2_voting_rule_formulas.tex",
        caption="Voting rule formalization.",
    )
    export_latex_table(
        validation.describe(include="all").reset_index().head(16),
        TABLES_DIR / "table_3_validation_metrics.tex",
        caption="Model validation metric summary.",
    )
    export_latex_table(
        rule_summary,
        TABLES_DIR / "table_4_rule_comparison_metrics.tex",
        caption="Rank versus percent counterfactual metrics.",
    )
    export_latex_table(
        controversy_summary,
        TABLES_DIR / "table_5_controversial_case_summary.tex",
        caption="Controversial contestant case summary.",
    )
    export_latex_table(
        effects.head(30),
        TABLES_DIR / "table_6_effects_model_results.tex",
        caption="Effect model coefficient summary.",
    )
    export_latex_table(
        proposed_summary,
        TABLES_DIR / "table_7_producer_recommendation.tex",
        caption="Proposed voting system simulation summary.",
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
    interval_fig = GENERATED_FIGURES_DIR / "fig_5_fan_vote_feasible_intervals.png"
    uncertainty_fig = GENERATED_FIGURES_DIR / "fig_6_fan_vote_uncertainty_heatmap.png"
    validation_fig = GENERATED_FIGURES_DIR / "fig_7_validation_dashboard.png"
    rule_fig = GENERATED_FIGURES_DIR / "fig_8_rank_percent_difference_heatmap.png"
    controversy_fig = GENERATED_FIGURES_DIR / "fig_9_controversial_trajectories.png"
    effects_fig = GENERATED_FIGURES_DIR / "fig_11_effects_forest.png"
    system_fig = GENERATED_FIGURES_DIR / "fig_12_new_system_dashboard.png"
    plot_season_structure(season_audit, season_fig)
    plot_judge_score_distribution(panel, score_fig)
    plot_fan_intervals(fan_estimates, interval_fig)
    plot_uncertainty_heatmap(fan_estimates, uncertainty_fig)
    plot_validation_dashboard(validation, validation_fig)
    plot_rule_comparison_heatmap(counterfactuals, rule_fig)
    plot_controversy_cases(controversy_trajectory, controversy_fig)
    plot_effects_forest(effects, effects_fig)
    plot_system_comparison(proposed_summary, system_fig)

    metrics = {
        "raw_rows": len(raw),
        "raw_columns": len(raw.columns),
        "seasons": raw["season"].nunique(),
        "panel_rows": len(panel),
        "active_contestant_weeks": int(panel["active"].sum()),
        "elimination_event_rows": len(events),
        "single_elimination_rows": int((events["event_type"] == "single_elimination").sum()),
        "multi_elimination_rows": int((events["event_type"] == "multi_elimination").sum()),
        "no_elimination_rows": int((events["event_type"] == "no_elimination").sum()),
        "modeled_elimination_weeks": len(validation),
        "percent_reproduction_rate": validation["percent_reproduces_observed"].mean(),
        "bottom_two_hit_rate": validation["observed_in_bottom_two"].mean(),
        "mean_fan_share_width": validation["mean_fan_share_width"].mean(),
        "outcome_difference_rate": counterfactuals["rank_percent_different"].mean(),
        "fan_override_rate": counterfactuals["fan_override_judges"].mean(),
        "gray_zone_tau": float(proposed_summary.loc[proposed_summary["metric"] == "gray_zone_tau", "value"].iloc[0]),
        "gray_zone_trigger_rate": float(proposed_summary.loc[proposed_summary["metric"] == "gray_zone_trigger_rate", "value"].iloc[0]),
    }

    key_results = pd.DataFrame(
        [(metric, value) for metric, value in metrics.items()],
        columns=["metric", "value"],
    )
    key_results.to_csv(REPORTS_DIR / "key_results.csv", index=False)

    pd.DataFrame(
        [
            (
                "Fig. 1",
                "figures/concept/fig_1_overall_research_workflow.png",
                "AI-generated concept figure",
                "1. Introduction",
            ),
            (
                "Fig. 2",
                "figures/concept/fig_2_voting_rule_mechanism.png",
                "AI-generated concept figure",
                "3. Voting Rule Formalization",
            ),
            ("Fig. 3", rel(season_fig), "scripts/run_all.py", "2. Data Audit"),
            ("Fig. 4", rel(score_fig), "scripts/run_all.py", "2. Data Audit"),
            ("Fig. 5", rel(interval_fig), "scripts/run_all.py", "4. Fan Vote Estimation"),
            ("Fig. 6", rel(uncertainty_fig), "scripts/run_all.py", "4-5. Uncertainty and Validation"),
            ("Fig. 7", rel(validation_fig), "scripts/run_all.py", "5. Validation"),
            ("Fig. 8", rel(rule_fig), "scripts/run_all.py", "6. Rank vs Percent"),
            ("Fig. 9", rel(controversy_fig), "scripts/run_all.py", "7. Controversial Cases"),
            (
                "Fig. 10",
                "figures/concept/fig_10_proposed_system_flowchart.png",
                "AI-generated concept figure",
                "9. Proposed System",
            ),
            ("Fig. 11", rel(effects_fig), "scripts/run_all.py", "8. Effects Model"),
            ("Fig. 12", rel(system_fig), "scripts/run_all.py", "9. Proposed System"),
            (
                "Memo Card",
                "figures/concept/memo_producer_decision_card.png",
                "AI-generated concept figure",
                "Memo to Producers",
            ),
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
    issue_text = (
        inference.model_issue_log.to_string(index=False)
        if not inference.model_issue_log.empty
        else "No model issues were recorded."
    )
    write_text(
        REPORTS_DIR / "sanity_check_report.md",
        "# Sanity Check Report\n\n"
        "## Workflow Status\n\n"
        "- Data audit generated successfully.\n"
        "- Fan-support inference generated for modeled elimination weeks.\n"
        "- All Summary numbers should be copied from `reports/key_results.csv`.\n\n"
        "## Model Issue Log\n\n"
        "```text\n"
        f"{issue_text}\n"
        "```\n",
    )
    write_if_missing(
        REPORTS_DIR / "submission_checklist.md",
        "# Submission Checklist\n\n- [ ] Summary control number = header control number = AI report team number\n- [ ] Main report within page limit\n- [ ] Every Summary number appears in reports/key_results.csv\n- [ ] Every generated figure appears in reports/figure_manifest.csv\n- [ ] AI Use Report appended after main report\n",
    )

    print(f"Workflow finished at {datetime.now(timezone.utc).isoformat()}")
    print(f"Wrote {REPORTS_DIR / 'key_results.csv'}")


if __name__ == "__main__":
    main()
