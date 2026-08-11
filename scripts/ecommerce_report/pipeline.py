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
    session = _at_stage("启动浏览器", _playwright_session)
    context = None
    session_entered = False
    primary_error: BaseException | None = None
    primary_traceback = None
    try:
        playwright = _at_stage("启动浏览器", session.__enter__)
        session_entered = True
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
    except BaseException as error:
        primary_error = error
        primary_traceback = error.__traceback__
    finally:
        if context is not None:
            try:
                context.close()
            except Exception as error:
                if primary_error is None:
                    primary_error = PipelineError("关闭浏览器", error)
                    primary_traceback = primary_error.__traceback__
        if session_entered:
            try:
                session.__exit__(
                    type(primary_error) if primary_error is not None else None,
                    primary_error,
                    primary_traceback,
                )
            except Exception as error:
                if primary_error is None:
                    primary_error = PipelineError("关闭浏览器", error)
                    primary_traceback = primary_error.__traceback__

    if primary_error is not None:
        raise primary_error.with_traceback(primary_traceback)

    frames = [frame for frame in (echotik_records, amazon_records) if not frame.empty]
    records = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return _at_stage(
        "导出报表",
        lambda: write_report(records, destination, config.template_path),
    )


__all__ = ["PipelineError", "run_pipeline"]
