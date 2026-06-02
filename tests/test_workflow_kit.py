from __future__ import annotations

import pandas as pd

from mcm_workflow_kit.data_auditor import audit_csv_file, build_data_audit


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
