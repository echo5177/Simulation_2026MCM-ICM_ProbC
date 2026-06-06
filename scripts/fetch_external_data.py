from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KIT_PATH = PROJECT_ROOT / "MCM_Workflow_Automation_Kit"
if str(KIT_PATH) not in sys.path:
    sys.path.insert(0, str(KIT_PATH))

from mcm_workflow_kit.source_checker import REQUIRED_COLUMNS, calculate_sha256


HTTP_SCHEMES = {"http", "https"}


def read_manifest(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader], list(reader.fieldnames or [])


def write_manifest(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_schema(fieldnames: list[str]) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing:
        raise ValueError("Manifest missing columns: " + ", ".join(missing))


def should_fetch(row: dict[str, str], selected_ids: set[str]) -> bool:
    if selected_ids and row.get("source_id", "") not in selected_ids:
        return False
    if row.get("source_type", "").strip().lower() != "external":
        return False
    parsed = urlparse(row.get("url", "").strip())
    return parsed.scheme.lower() in HTTP_SCHEMES


def download_file(url: str, destination: Path, timeout: int) -> None:
    request = Request(url, headers={"User-Agent": "MCM-Automation-Kit/1.0"})
    with urlopen(request, timeout=timeout) as response:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)


def fetch_sources(
    manifest_path: Path,
    project_root: Path,
    selected_ids: set[str],
    dry_run: bool,
    allow_overwrite: bool,
    update_hashes: bool,
    timeout: int,
) -> int:
    rows, fieldnames = read_manifest(manifest_path)
    validate_schema(fieldnames)
    changed_manifest = False
    fetched = 0

    for row in rows:
        if not should_fetch(row, selected_ids):
            continue

        source_id = row.get("source_id", "").strip()
        url = row.get("url", "").strip()
        local_rel = row.get("local_path", "").strip()
        if not local_rel:
            raise ValueError(f"{source_id} has no local_path.")

        destination = project_root / local_rel
        planned = f"{source_id}: {url} -> {local_rel}"
        if dry_run:
            print(f"DRY RUN {planned}")
            continue

        if destination.exists() and not allow_overwrite:
            print(f"SKIP existing file: {local_rel}")
            continue

        try:
            download_file(url, destination, timeout)
        except URLError as exc:
            raise RuntimeError(f"Failed to download {source_id}: {url}") from exc

        computed_hash = calculate_sha256(destination)
        expected_hash = row.get("sha256", "").strip().lower()
        if expected_hash and computed_hash.lower() != expected_hash:
            raise RuntimeError(f"{source_id} sha256 mismatch after download.")
        if update_hashes and not expected_hash:
            row["sha256"] = computed_hash
            changed_manifest = True

        fetched += 1
        print(f"FETCHED {planned}")

    if changed_manifest:
        write_manifest(manifest_path, rows, fieldnames)
        print(f"UPDATED {manifest_path}")

    return fetched


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download external data rows declared in reports/data_source_manifest.csv."
    )
    parser.add_argument(
        "--manifest",
        default="reports/data_source_manifest.csv",
        help="Project-relative source manifest path.",
    )
    parser.add_argument(
        "--source-id",
        action="append",
        default=[],
        help="Fetch only this source_id. Can be repeated.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned downloads.")
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Overwrite existing local files.",
    )
    parser.add_argument(
        "--update-hashes",
        action="store_true",
        help="Fill blank sha256 fields after successful downloads.",
    )
    parser.add_argument("--timeout", type=int, default=60, help="Network timeout seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = PROJECT_ROOT / args.manifest
    fetched = fetch_sources(
        manifest_path=manifest_path,
        project_root=PROJECT_ROOT,
        selected_ids=set(args.source_id),
        dry_run=args.dry_run,
        allow_overwrite=args.allow_overwrite,
        update_hashes=args.update_hashes,
        timeout=args.timeout,
    )
    print(f"External sources fetched: {fetched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
