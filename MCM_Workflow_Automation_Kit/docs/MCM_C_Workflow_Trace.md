# MCM C Workflow Trace

This document records the reusable workflow learned from the completed 2026
MCM/ICM Problem C simulation project.

| Stage | Input | Operation | Tool | Human Judgment | Output | Automation Level |
| --- | --- | --- | --- | --- | --- | --- |
| Problem intake | PDF, data | Break down tasks | Codex/ChatGPT | Main modeling direction | problem_breakdown.md | Medium |
| Data audit | CSV | Profile and audit | Python | Interpret anomalies | data_audit_report.md | High |
| Modeling | Problem, data | Choose model family | Codex/ChatGPT | Main model choice | model_design.md | Medium |
| Coding | Model design | Implement pipeline | Codex + Python | Review logic | scripts/run_all.py | High |
| Results | Processed data | Generate tables and figures | Python | Figure usefulness | figures/, tables/ | High |
| Paper | Results, figures | Build narrative | Codex/ChatGPT | Main story and quality | paper/main.pdf | Medium |
| QA | PDF, logs | Check submission integrity | Python + reviewer | Final responsibility | workflow reports | High |
