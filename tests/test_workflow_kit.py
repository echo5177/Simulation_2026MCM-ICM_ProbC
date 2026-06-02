from __future__ import annotations

import pandas as pd

from mcm_workflow_kit.data_auditor import audit_csv_file, build_data_audit
from mcm_workflow_kit.result_checker import (
    check_key_results_in_text,
    check_table_numbers,
    missing_table_numbers,
    parse_latex_graphics,
    scan_placeholders,
)
from mcm_workflow_kit.paper_qa import (
    check_required_tex_sections,
    parse_pdfinfo_pages,
    scan_latex_log,
)
from mcm_workflow_kit.orchestrator import NodeRun, WorkflowRun, render_workflow_summary
from mcm_workflow_kit.config import WorkflowConfig
from mcm_workflow_kit.release_packet import create_release_packet


def test_data_auditor_summarizes_csv(tmp_path):
    csv_path = tmp_path / "sample.csv"
    pd.DataFrame(
        [
            {"season": 1, "week": 1, "score": 10.0, "name": "A"},
            {"season": 1, "week": 1, "score": None, "name": "B"},
            {"season": 1, "week": 2, "score": 40.0, "name": "A"},
            {"season": 1, "week": 2, "score": 40.0, "name": "A"},
        ]
    ).to_csv(csv_path, index=False)

    result = audit_csv_file(csv_path, display_path="sample.csv")

    assert result["path"] == "sample.csv"
    assert result["rows"] == 4
    assert result["columns"] == 4
    assert result["missing_values"] == 1
    assert result["missing_by_column"]["score"] == 1
    assert result["duplicate_rows"] == 1
    assert result["numeric_summary"]["score"]["count"] == 3
    assert result["group_counts"]["season"][0]["rows"] == 4
    assert len(result["group_counts"]["season/week"]) == 2


def test_build_data_audit_uses_project_relative_paths(tmp_path):
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    csv_path = data_dir / "data.csv"
    pd.DataFrame([{"value": 1}, {"value": 2}]).to_csv(csv_path, index=False)

    result = build_data_audit(tmp_path, ["data/raw/data.csv"])

    assert result.files[0]["path"] == "data/raw/data.csv"
    assert result.files[0]["rows"] == 2


def test_parse_latex_graphics_handles_options():
    text = r"""
    \includegraphics[width=0.5\linewidth]{figures/generated/fig_1.png}
    \includegraphics{fig_2.png}
    """

    assert parse_latex_graphics(text) == [
        "figures/generated/fig_1.png",
        "fig_2.png",
    ]


def test_placeholder_scanner_is_case_insensitive():
    assert scan_placeholders("This still has a todo marker.", ["TODO"]) == ["TODO"]


def test_key_result_checker_matches_numeric_variants(tmp_path):
    path = tmp_path / "key_results.csv"
    pd.DataFrame(
        [
            {"metric": "rate", "value": 0.7356321839},
            {"metric": "rows", "value": 421.0},
        ]
    ).to_csv(path, index=False)

    result = check_key_results_in_text(
        path,
        "The exact-match rate is 73.56%. The data has 421 rows.",
    )

    assert [row["status"] for row in result] == ["found", "found"]


def test_table_number_checker_finds_gaps(tmp_path):
    (tmp_path / "table_1_data.tex").write_text("", encoding="utf-8")
    (tmp_path / "table_3_results.tex").write_text("", encoding="utf-8")

    numbers = check_table_numbers(tmp_path)

    assert numbers == [1, 3]
    assert missing_table_numbers(numbers) == [2]


def test_parse_pdfinfo_pages():
    assert parse_pdfinfo_pages("Title:\nPages:           26\n") == 26
    assert parse_pdfinfo_pages("Title:\n") is None


def test_latex_log_scanner_classifies_messages():
    messages = scan_latex_log(
        "LaTeX Warning: Reference `x' undefined.\n"
        "Overfull \\hbox in paragraph\n"
        "! LaTeX Error: File `missing.sty' not found.\n"
    )

    assert [message.level for message in messages] == ["warn", "warn", "fail"]


def test_required_tex_sections():
    messages = check_required_tex_sections(
        r"\large \textbf{Summary}\tableofcontents References"
    )

    assert messages == []


def test_workflow_summary_renders_node_statuses():
    run = WorkflowRun(
        mode="check",
        project_root=".",
        run_dir="runs/test",
        started_at="start",
        finished_at="finish",
        status="pass",
        nodes=[
            NodeRun(
                name="data_auditor",
                status="pass",
                started_at="start",
                finished_at="finish",
                duration_seconds=0.5,
                detail="ok",
            )
        ],
    )

    lines = render_workflow_summary(run)

    assert "| data_auditor | pass | 0.500s | ok |" in lines


def test_release_packet_copies_configured_artifacts(tmp_path):
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper" / "main.pdf").write_text("pdf", encoding="utf-8")
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "key_results.csv").write_text(
        "metric,value\nx,1\n",
        encoding="utf-8",
    )

    config = WorkflowConfig(
        project_pipeline_command=[],
        raw_data_files=[],
        paper_tex="paper/main.tex",
        paper_pdf="paper/main.pdf",
        latex_log="paper/main.log",
        key_results="reports/key_results.csv",
        figure_manifest="reports/figure_manifest.csv",
        figures_dirs=[],
        tables_dir="tables",
        workflow_reports_dir="reports/workflow",
        page_target=25,
        page_hard_limit=26,
        placeholder_patterns=[],
        release_artifacts=[
            "paper/main.pdf",
            "reports",
            "missing.txt",
        ],
    )

    packet = create_release_packet(tmp_path, config, timestamp="test-release")

    assert (packet.release_dir / "paper" / "main.pdf").exists()
    assert (packet.release_dir / "reports" / "key_results.csv").exists()
    assert (packet.release_dir / "release_manifest.csv").exists()
    assert (packet.release_dir / "final_checklist.md").exists()
    assert [entry.status for entry in packet.entries] == [
        "copied",
        "copied",
        "missing",
    ]
