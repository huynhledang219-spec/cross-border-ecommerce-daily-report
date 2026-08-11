"""Scheduled command-line entrypoint for the idempotent daily job."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from scripts.ecommerce_report.daily import emit_cli_failure, run_daily_job
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from ecommerce_report.daily import emit_cli_failure, run_daily_job


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行跨境电商每日报表任务")
    parser.add_argument("--config", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        run_daily_job(args.config)
    except Exception as error:
        emit_cli_failure(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
