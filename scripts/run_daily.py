"""Scheduled command-line entrypoint for the idempotent daily job."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from scripts.ecommerce_report.daily import DailyJobError, run_daily_job
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from ecommerce_report.daily import DailyJobError, run_daily_job


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行跨境电商每日报表任务")
    parser.add_argument("--config", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        run_daily_job(args.config)
    except DailyJobError as error:
        print(f"日报生成失败；失败记录: {error.failure_path}", file=sys.stderr)
        return 1
    except Exception:
        print("日报生成失败；无法确认失败记录路径。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
