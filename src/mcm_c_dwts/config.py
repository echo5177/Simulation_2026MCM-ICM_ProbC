from __future__ import annotations

from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"
GENERATED_FIGURES_DIR = FIGURES_DIR / "generated"
TABLES_DIR = PROJECT_ROOT / "tables"
REPORTS_DIR = PROJECT_ROOT / "reports"
PAPER_DIR = PROJECT_ROOT / "paper"

RAW_DATA_FILE = RAW_DIR / "2026_MCM_Problem_C_Data.csv"
RAW_PROBLEM_FILE = RAW_DIR / "2026_MCM_Problem_C.pdf"

ID_COLUMNS = [
    "celebrity_name",
    "ballroom_partner",
    "celebrity_industry",
    "celebrity_homestate",
    "celebrity_homecountry/region",
    "celebrity_age_during_season",
    "season",
    "results",
    "placement",
]

WEEK_SCORE_RE = re.compile(r"^week(?P<week>\d+)_judge(?P<judge>\d+)_score$")


def ensure_directories() -> None:
    for path in [
        RAW_DIR,
        INTERIM_DIR,
        PROCESSED_DIR,
        GENERATED_FIGURES_DIR,
        TABLES_DIR,
        REPORTS_DIR,
        PAPER_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
