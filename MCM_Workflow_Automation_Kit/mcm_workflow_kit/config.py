from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


KIT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = KIT_ROOT / "workflow_config.json"


@dataclass(frozen=True)
class WorkflowConfig:
    project_pipeline_command: list[str]
    raw_data_files: list[str]
    paper_tex: str
    paper_pdf: str
    latex_log: str
    key_results: str
    figure_manifest: str
    figures_dirs: list[str]
    tables_dir: str
    workflow_reports_dir: str
    page_target: int
    page_hard_limit: int
    placeholder_patterns: list[str]
    release_artifacts: list[str]
    team_control_number_placeholders: list[str] = field(default_factory=list)
    diagram_sources: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "WorkflowConfig":
        return cls(
            project_pipeline_command=list(data.get("project_pipeline_command", [])),
            raw_data_files=list(data.get("raw_data_files", [])),
            paper_tex=str(data.get("paper_tex", "paper/main.tex")),
            paper_pdf=str(data.get("paper_pdf", "paper/main.pdf")),
            latex_log=str(data.get("latex_log", "paper/main.log")),
            key_results=str(data.get("key_results", "reports/key_results.csv")),
            figure_manifest=str(
                data.get("figure_manifest", "reports/figure_manifest.csv")
            ),
            figures_dirs=list(data.get("figures_dirs", ["figures"])),
            tables_dir=str(data.get("tables_dir", "tables")),
            workflow_reports_dir=str(
                data.get("workflow_reports_dir", "reports/workflow")
            ),
            page_target=int(data.get("page_target", 25)),
            page_hard_limit=int(data.get("page_hard_limit", 25)),
            placeholder_patterns=list(data.get("placeholder_patterns", [])),
            release_artifacts=list(data.get("release_artifacts", [])),
            team_control_number_placeholders=list(
                data.get("team_control_number_placeholders", [])
            ),
            diagram_sources=list(data.get("diagram_sources", [])),
        )


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> WorkflowConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return WorkflowConfig.from_mapping(data)


def resolve_project_path(project_root: str | Path, relative_path: str | Path) -> Path:
    return Path(project_root).resolve() / Path(relative_path)
