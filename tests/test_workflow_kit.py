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
from mcm_workflow_kit.diagram_checker import read_png_dimensions, run_diagram_checks
from mcm_workflow_kit.orchestrator import NodeRun, WorkflowRun, render_workflow_summary
from mcm_workflow_kit.config import WorkflowConfig
from mcm_workflow_kit.release_packet import create_release_packet
from mcm_workflow_kit.source_checker import calculate_sha256, run_source_checks
from mcm_workflow_kit.v1_gate import run_v1_gate


def make_config(**overrides):
    defaults = {
        "project_pipeline_command": [],
        "raw_data_files": [],
        "paper_tex": "paper/main.tex",
        "paper_pdf": "paper/main.pdf",
        "latex_log": "paper/main.log",
        "key_results": "reports/key_results.csv",
        "figure_manifest": "reports/figure_manifest.csv",
        "figures_dirs": [],
        "tables_dir": "tables",
        "workflow_reports_dir": "reports/workflow",
        "page_target": 25,
        "page_hard_limit": 26,
        "placeholder_patterns": [],
        "release_artifacts": [],
    }
    defaults.update(overrides)
    return WorkflowConfig(**defaults)


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


def test_source_checker_validates_manifest_and_hash(tmp_path):
    data_dir = tmp_path / "data" / "raw" / "external"
    reports_dir = tmp_path / "reports"
    data_dir.mkdir(parents=True)
    reports_dir.mkdir()
    data_path = data_dir / "source.csv"
    data_path.write_text("value\n1\n", encoding="utf-8")
    expected_hash = calculate_sha256(data_path)
    (reports_dir / "external_data_needs.md").write_text(
        "# External Data Needs\n\nOfficial test source declared.\n",
        encoding="utf-8",
    )
    (reports_dir / "data_source_manifest.csv").write_text(
        "source_id,dataset_name,source_type,publisher,url,access_date,"
        "license_or_terms,retrieval_method,local_path,sha256,why_needed,"
        "paper_usage,citation_key\n"
        "test_source,Test Source,external,Test Publisher,"
        "https://example.com/source.csv,2026-06-06,Public test terms,"
        "web_download,data/raw/external/source.csv,"
        f"{expected_hash},Validate source checker,Model input,test_source\n",
        encoding="utf-8",
    )
    config = make_config(
        data_source_manifest="reports/data_source_manifest.csv",
        external_data_needs="reports/external_data_needs.md",
        source_manifest_required=True,
        external_data_required=True,
    )

    result = run_source_checks(tmp_path, config)

    assert result.status == "pass"
    assert result.external_sources == 1
    assert result.source_rows[0]["hash_status"] == "match"


def test_source_checker_fails_on_hash_mismatch(tmp_path):
    data_dir = tmp_path / "data" / "raw" / "external"
    reports_dir = tmp_path / "reports"
    data_dir.mkdir(parents=True)
    reports_dir.mkdir()
    (data_dir / "source.csv").write_text("value\n1\n", encoding="utf-8")
    (reports_dir / "external_data_needs.md").write_text(
        "# External Data Needs\n\nOfficial test source declared.\n",
        encoding="utf-8",
    )
    (reports_dir / "data_source_manifest.csv").write_text(
        "source_id,dataset_name,source_type,publisher,url,access_date,"
        "license_or_terms,retrieval_method,local_path,sha256,why_needed,"
        "paper_usage,citation_key\n"
        "test_source,Test Source,external,Test Publisher,"
        "https://example.com/source.csv,2026-06-06,Public test terms,"
        "web_download,data/raw/external/source.csv,deadbeef,"
        "Validate source checker,Model input,test_source\n",
        encoding="utf-8",
    )
    config = make_config(
        data_source_manifest="reports/data_source_manifest.csv",
        external_data_needs="reports/external_data_needs.md",
        source_manifest_required=True,
    )

    result = run_source_checks(tmp_path, config)

    assert result.status == "fail"
    assert any("sha256 mismatch" in message.message for message in result.messages)


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
        "Package: rerunfilecheck 2022-07-10 v1.10 Rerun checks for auxiliary files\n"
        "! LaTeX Error: File `missing.sty' not found.\n"
    )

    assert [message.level for message in messages] == ["warn", "warn", "fail"]


def test_required_tex_sections():
    messages = check_required_tex_sections(
        r"\large \textbf{Summary}\tableofcontents References"
    )

    assert messages == []


def test_png_dimension_reader_uses_png_header(tmp_path):
    png_path = tmp_path / "sample.png"
    png_path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + (200).to_bytes(4, "big")
        + (120).to_bytes(4, "big")
    )

    assert read_png_dimensions(png_path) == (200, 120)


def test_diagram_checker_requires_structured_sources(tmp_path):
    figure_dir = tmp_path / "figures" / "concept"
    source_dir = tmp_path / "figures" / "concept_src"
    report_dir = tmp_path / "reports"
    figure_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    report_dir.mkdir()
    (figure_dir / "fig.png").write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + (200).to_bytes(4, "big")
        + (120).to_bytes(4, "big")
    )
    (source_dir / "fig.svg").write_text("<svg></svg>", encoding="utf-8")
    (source_dir / "fig.json").write_text("{}", encoding="utf-8")
    (report_dir / "figure_manifest.csv").write_text(
        "figure_id,path,source_script,paper_location\n"
        "Fig. 1,figures/concept/fig.png,scripts/render_workflow_figure.py,Intro\n",
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
        release_artifacts=[],
        diagram_sources=[
            {
                "figure_id": "Fig. 1",
                "png": "figures/concept/fig.png",
                "svg": "figures/concept_src/fig.svg",
                "json": "figures/concept_src/fig.json",
                "expected_source": "scripts/render_workflow_figure.py",
                "min_width": 100,
                "min_height": 100,
            }
        ],
    )

    result = run_diagram_checks(tmp_path, config)

    assert result.status == "pass"
    assert result.diagram_checks[0]["dimensions"] == "200x120"


def test_diagram_checker_warns_on_ai_generated_manifest_source(tmp_path):
    figure_dir = tmp_path / "figures" / "concept"
    source_dir = tmp_path / "figures" / "concept_src"
    report_dir = tmp_path / "reports"
    figure_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    report_dir.mkdir()
    (figure_dir / "fig.png").write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + (200).to_bytes(4, "big")
        + (120).to_bytes(4, "big")
    )
    (source_dir / "fig.svg").write_text("<svg></svg>", encoding="utf-8")
    (source_dir / "fig.json").write_text("{}", encoding="utf-8")
    (report_dir / "figure_manifest.csv").write_text(
        "figure_id,path,source_script,paper_location\n"
        "Fig. 1,figures/concept/fig.png,AI-generated concept figure,Intro\n",
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
        release_artifacts=[],
        diagram_sources=[
            {
                "figure_id": "Fig. 1",
                "png": "figures/concept/fig.png",
                "svg": "figures/concept_src/fig.svg",
                "json": "figures/concept_src/fig.json",
                "min_width": 100,
                "min_height": 100,
            }
        ],
    )

    result = run_diagram_checks(tmp_path, config)

    assert result.status == "warn"
    assert "AI-generated" in result.messages[0].message


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


def test_v1_gate_classifies_warned_nodes_and_team_placeholder(tmp_path):
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper" / "main.tex").write_text(
        r"\newcommand{\Team}{1111111}",
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
        release_artifacts=[],
        team_control_number_placeholders=["1111111"],
    )
    nodes = [
        NodeRun(
            name="paper_qa",
            status="warn",
            started_at="start",
            finished_at="finish",
            duration_seconds=0.1,
            detail="page target warning",
        )
    ]

    result = run_v1_gate(tmp_path, config, nodes)

    assert result.status == "warn"
    assert "paper_qa" in result.messages[0].message
    assert result.known_warnings == [
        "Team control number placeholder remains pending: 1111111"
    ]


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
