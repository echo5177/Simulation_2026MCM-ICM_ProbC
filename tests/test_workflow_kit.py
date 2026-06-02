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
