"""Manual command-line entrypoint for one report."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

try:
    from scripts.ecommerce_report.config import RuntimeConfig
    from scripts.ecommerce_report.pipeline import run_pipeline
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from ecommerce_report.config import RuntimeConfig
    from ecommerce_report.pipeline import run_pipeline


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成跨境电商选品报表")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = RuntimeConfig.load(args.config)
    today = date.today()
    output_path = args.output or (
        config.output_dir / f"{today.year}.{today.month}.{today.day}数据报表.xlsx"
    )
    run_pipeline(config, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
