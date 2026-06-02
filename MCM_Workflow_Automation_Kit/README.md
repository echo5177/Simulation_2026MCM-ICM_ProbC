# MCM Workflow Automation Kit

Local-first automation kit for reusable MCM/ICM project checks.

The kit does not replace Codex or human modeling judgment. It provides
deterministic workflow nodes for data audit, result consistency checks, paper
QA, run logging, and release packet creation.

## Quick Start

```powershell
python MCM_Workflow_Automation_Kit/run_workflow.py --project-root . --mode check
```

Use `--mode full` after the project pipeline command in `workflow_config.json`
is ready to be run automatically.

## Design

- Keep project-specific modeling code in the project repository.
- Keep reusable checks in this kit.
- Write reports under `reports/workflow/`.
- Write transient state and logs under `MCM_Workflow_Automation_Kit/runs/`.
- Keep all text outputs UTF-8 encoded for Windows compatibility.
