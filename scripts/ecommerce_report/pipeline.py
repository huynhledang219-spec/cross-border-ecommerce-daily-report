"""Orchestrate collection and workbook export without duplicating source logic."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar

import pandas as pd

from .amazon import scrape_amazon
from .browser import open_platform_context
from .config import RuntimeConfig
from .platforms import (
    PlatformAdapterRegistry,
    build_default_registry,
    validate_normalized_records,
)
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


def run_pipeline(
    config: RuntimeConfig,
    output_path: Path,
    registry: PlatformAdapterRegistry | None = None,
) -> Path:
    """Collect configured sources and export one template-preserving report."""

    config.validate()
    destination = RuntimeConfig.ensure_outside_skill(output_path, "output path")
    active_registry = registry or build_default_registry()
    adapter = active_registry.resolve(config.primary_platform.adapter)
    adapter.validate_config(config.primary_platform)
    primary_stage = f"{adapter.display_name}采集"

    session = _at_stage("启动浏览器", _playwright_session)
    context = None
    session_entered = False
    primary_error: BaseException | None = None
    primary_traceback = None
    try:
        playwright = _at_stage("启动浏览器", session.__enter__)
        session_entered = True
        context = _at_stage(
            "启动浏览器", lambda: open_platform_context(playwright, config)
        )
        primary_records = _at_stage(
            primary_stage,
            lambda: adapter.collect(
                context,
                config.primary_platform,
                detail_limit=config.detail_limit,
                trend_days=config.trend_days,
                pages_per_category=config.pages_per_category,
            ),
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

    if primary_records.empty:
        raise PipelineError(
            primary_stage,
            RuntimeError(f"未采集到任何 {adapter.display_name} 商品"),
        )
    _at_stage(
        primary_stage,
        lambda: validate_normalized_records(primary_records, adapter.display_name),
    )
    if amazon_records.empty:
        raise PipelineError(
            "Amazon采集", RuntimeError("未采集到任何 Amazon 商品")
        )

    records = pd.concat((primary_records, amazon_records), ignore_index=True)
    return _at_stage(
        "导出报表",
        lambda: write_report(
            records,
            destination,
            config.template_path,
            primary_source=adapter.display_name,
        ),
    )


__all__ = ["PipelineError", "run_pipeline"]
