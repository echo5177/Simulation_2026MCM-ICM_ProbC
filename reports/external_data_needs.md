# External Data Needs

## Problem-Derived Needs

This simulation currently uses the official Problem C contest packet only. No
external public datasets are required for the submitted model run.

## Current Decision

External data is not required for this Problem C run because the official CSV
contains the voting observations needed for reconstruction, validation, and
counterfactual analysis. If a future variant needs external data, record the
need here before downloading files into `data/raw/external/`.

## Codex Acquisition Protocol

1. Translate the problem statement into explicit data needs.
2. Prefer official, primary, public, and stable sources.
3. Compare candidate sources by publisher, coverage, update frequency, license,
   and reproducibility.
4. Download approved files into `data/raw/external/`.
5. Record every file in `reports/data_source_manifest.csv` with access date,
   local path, SHA-256 hash, intended paper usage, and citation key.
6. Run `source_checker` before modeling so provenance problems are caught early.
