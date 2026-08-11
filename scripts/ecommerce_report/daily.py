"""Idempotent daily report orchestration and concise failure records."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from .config import RuntimeConfig
from .pipeline import PipelineError, run_pipeline


_SENSITIVE_CONTENT = re.compile(
    r"(?ix)("
    r"\bauthorization\b|"
    r"\bbearer\s+\S+|"
    r"\bbasic\s+\S+|"
    r"https?://[^/\s@]+@|"
    r"(?:password|passwd|token|cookie|secret|api[-_ ]?key|key)\s*[:=]|"
    r"(?<![a-z])[a-z]:[\\/]|"
    r"/(?:home|users|root)/|"
    r"账号|密码|令牌"
    r")"
)
_TRACE_LINE = re.compile(r'^(Traceback\b|File\s+["\']|at\s+\S+|\^+$)')


class DailyJobError(RuntimeError):
    """A daily failure whose sanitized record path is safe to show."""

    def __init__(self, failure_path: Path, stage: str) -> None:
        super().__init__("日报生成失败")
        self.failure_path = Path(failure_path)
        self.stage = stage


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


def _sanitize_reason(error: BaseException) -> str:
    for raw_line in str(error).splitlines():
        line = " ".join(raw_line.strip().split())
        if not line or _SENSITIVE_CONTENT.search(line) or _TRACE_LINE.search(line):
            continue
        return line[:160]
    return "错误详情已隐藏"


def _write_failure(path: Path, stage: str, error: BaseException) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"失败时间: {_now():%Y-%m-%d %H:%M:%S}\n"
        f"阶段: {stage}\n"
        f"原因: {_sanitize_reason(error)}\n",
        encoding="utf-8",
    )


def run_daily_job(config_path: Path, day: date | None = None) -> Path:
    """Run today's report once, while allowing retries after a failed attempt."""

    job_day = day or date.today()
    resolved_config_path = Path(config_path).resolve()
    bootstrap_failure_path = failure_path_for(job_day, resolved_config_path.parent)
    try:
        config = RuntimeConfig.load(resolved_config_path)
    except Exception as error:
        _write_failure(bootstrap_failure_path, "读取配置", error)
        raise DailyJobError(bootstrap_failure_path, "读取配置") from error

    output_path = _report_path_for(job_day, config.output_dir)
    failure_path = failure_path_for(job_day, config.output_dir)
    if bootstrap_failure_path != failure_path:
        bootstrap_failure_path.unlink(missing_ok=True)

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
        raise DailyJobError(failure_path, stage) from error

    failure_path.unlink(missing_ok=True)
    return result


__all__ = ["DailyJobError", "failure_path_for", "run_daily_job"]
