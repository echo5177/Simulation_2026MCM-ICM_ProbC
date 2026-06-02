# MCM C Postmortem

The completed project already has a strong project-specific pipeline. The next
step is to separate reusable workflow checks from problem-specific modeling
code.

## What Worked

- A single `scripts/run_all.py` produced data, figures, tables, and reports.
- Key metrics were centralized in `reports/key_results.csv`.
- Figure provenance was centralized in `reports/figure_manifest.csv`.
- LaTeX and PDF artifacts were generated locally.

## What Remains To Automate

- Cross-project CSV audit.
- Paper/result consistency checks.
- LaTeX/PDF QA checks.
- Run state logging.
- Release packet creation.
