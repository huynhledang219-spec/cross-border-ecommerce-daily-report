"""Idempotent daily report orchestration and concise failure records."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from .config import RuntimeConfig
from .pipeline import PipelineError, run_pipeline


_SENSITIVE_LINE = re.compile(
    r"(?i)(authorization|cookie|password|passwd|secret|token|api[-_ ]?key|账号|密码|令牌)"
)
_TRACE_LINE = re.compile(r'^(Traceback\b|File\s+["\']|at\s+\S+|\^+$)')


def _day_prefix(day: date) -> str:
    return f"{day.year}.{day.month}.{day.day}"


def _report_path_for(day: date, output_dir: Path) -> Path:
    return Path(output_dir) / f"{_day_prefix(day)}数据报表.xlsx"


def failure_path_for(day: date, output_dir: Path) -> Path:
    """Return the one failure-record path for a calendar day."""

    return (
        Path(output_dir)
        / "数据报表_失败原因"
        / f"{_day_prefix(day)}失败原因.txt"
    )


def _now() -> datetime:
    return datetime.now()


def _concise_reason(error: BaseException) -> str:
    for raw_line in str(error).splitlines():
        line = " ".join(raw_line.strip().split())
        if not line or _SENSITIVE_LINE.search(line) or _TRACE_LINE.search(line):
            continue
        return line[:160]
    return "错误详情已隐藏"


def _write_failure(path: Path, stage: str, error: BaseException) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"失败时间: {_now():%Y-%m-%d %H:%M:%S}\n"
        f"阶段: {stage}\n"
        f"原因: {_concise_reason(error)}\n",
        encoding="utf-8",
    )


def run_daily_job(config_path: Path, day: date | None = None) -> Path:
    """Run today's report once, while allowing retries after a failed attempt."""

    job_day = day or date.today()
    config = RuntimeConfig.load(Path(config_path))
    output_path = _report_path_for(job_day, config.output_dir)
    failure_path = failure_path_for(job_day, config.output_dir)

    if output_path.exists():
        failure_path.unlink(missing_ok=True)
        return output_path

    try:
        result = run_pipeline(config, output_path)
    except Exception as error:
        if isinstance(error, PipelineError):
            stage = error.stage
            reason = error.error
        else:
            stage = "生成报表"
            reason = error
        _write_failure(failure_path, stage, reason)
        raise

    failure_path.unlink(missing_ok=True)
    return result


__all__ = ["failure_path_for", "run_daily_job"]
