from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MCM workflow automation checks.")
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    parser.add_argument(
        "--mode",
        choices=["check", "full"],
        default="check",
        help="check existing artifacts or run the full project pipeline first.",
    )
    parser.parse_args()
    raise SystemExit(
        "Workflow orchestrator scaffolded; implementation is added in a later commit."
    )


if __name__ == "__main__":
    raise SystemExit(main())
