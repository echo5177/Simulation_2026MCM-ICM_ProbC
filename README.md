# Simulation_2026MCM-ICM_ProbC

Private repository for the 2026 MCM/ICM Problem C simulation project.

The project follows the fixed modeling direction from the prior planning
notes: infer feasible latent fan support under voting-rule constraints, quantify
uncertainty, compare counterfactual voting systems, and keep every paper result
traceable through generated reports.

## Quick Start

Use the existing `mcm` Conda environment:

```powershell
conda activate mcm
python scripts/run_all.py
pytest
```

The workflow writes audited intermediate data, figures, tables, and result logs
under `data/`, `figures/`, `tables/`, and `reports/`.
