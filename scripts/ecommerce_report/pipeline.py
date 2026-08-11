"""Orchestrate collection and workbook export without duplicating source logic."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar

import pandas as pd

from .amazon import scrape_amazon
from .browser import open_echotik_context
from .config import RuntimeConfig
from .echotik import scrape_echotik
from .workbook import write_report


_T = TypeVar("_T")


class PipelineError(RuntimeError):
    """A concise pipeline failure carrying its operator-facing stage."""

    def __init__(self, stage: str, error: BaseException) -> None:
        super().__init__(f"{stage}失败")
        self.stage = stage
        self.error = error


def _playwright_session():
    from playwright.sync_api import sync_playwright

    return sync_playwright()


def _at_stage(stage: str, operation: Callable[[], _T]) -> _T:
    try:
        return operation()
    except PipelineError:
        raise
    except Exception as error:
        raise PipelineError(stage, error) from error


def run_pipeline(config: RuntimeConfig, output_path: Path) -> Path:
    """Collect configured sources and export one template-preserving report."""

    config.validate()
    destination = Path(output_path)
    context = None
    try:
        with _at_stage("启动浏览器", _playwright_session) as playwright:
            context = _at_stage(
                "启动浏览器", lambda: open_echotik_context(playwright, config)
            )
            echotik_records = _at_stage(
                "EchoTik采集", lambda: scrape_echotik(context, config)
            )
            amazon_records = _at_stage(
                "Amazon采集",
                lambda: scrape_amazon(context, config.amazon_categories),
            )
    finally:
        if context is not None:
            context.close()

    frames = [frame for frame in (echotik_records, amazon_records) if not frame.empty]
    records = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return _at_stage(
        "写入报表",
        lambda: write_report(records, destination, config.template_path),
    )


__all__ = ["PipelineError", "run_pipeline"]
