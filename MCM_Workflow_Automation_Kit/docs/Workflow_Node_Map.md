# Workflow Node Map

```text
run_workflow.py
  -> optional project pipeline
  -> data_auditor
  -> result_checker
  -> paper_reviewer
  -> workflow_run_summary.md

create_release_packet.py
  -> release/<timestamp>/
  -> release_manifest.csv
  -> final_checklist.md
```

## v0.1 Commands

```powershell
python MCM_Workflow_Automation_Kit/run_workflow.py --project-root . --mode check
python MCM_Workflow_Automation_Kit/scripts/create_release_packet.py --project-root .
```

Use `--mode full` only when the configured project pipeline command should run
before checks.
