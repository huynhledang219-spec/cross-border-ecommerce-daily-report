"""Idempotent daily report orchestration and concise failure records."""

from __future__ import annotations

import os
import re
import sys
import tempfile
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
_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_PHONE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
_URL_QUERY = re.compile(r"(?i)(https?://[^\s?#]+)\?[^\s]+")


class DailyJobError(RuntimeError):
    """A daily failure whose sanitized record path is safe to show."""

    def __init__(self, failure_path: Path, stage: str) -> None:
        super().__init__("日报生成失败")
        self.failure_path = Path(failure_path)
        self.stage = stage


def emit_cli_failure(error: BaseException) -> None:
    """Write one sanitized, path-minimized failure line to stderr."""

    stage = getattr(error, "stage", "生成报表")
    failure_path = getattr(error, "failure_path", None)
    location = "无法确认失败记录"
    if failure_path is not None:
        location = f"数据报表_失败原因/{Path(failure_path).name}"
    print(
        f"日报生成失败；阶段: {stage}；失败记录: {location}",
        file=sys.stderr,
    )


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


def _bootstrap_output_dir(config_path: Path) -> Path:
    config_parent = Path(config_path).resolve().parent
    try:
        RuntimeConfig.ensure_outside_skill(config_parent, "configuration directory")
    except ValueError:
        runtime_root = Path(
            os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
        ).resolve()
        return runtime_root / "CrossBorderEcommerceDailyReport"
    return config_parent


def _now() -> datetime:
    return datetime.now()


def _sanitize_reason(error: BaseException) -> str:
    for raw_line in str(error).splitlines():
        line = " ".join(raw_line.strip().split())
        if not line or _SENSITIVE_CONTENT.search(line) or _TRACE_LINE.search(line):
            continue
        line = _EMAIL.sub("[邮箱已隐藏]", line)
        line = _PHONE.sub("[手机号已隐藏]", line)
        line = _URL_QUERY.sub(r"\1?[查询参数已隐藏]", line)
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
    bootstrap_failure_path = failure_path_for(
        job_day, _bootstrap_output_dir(resolved_config_path)
    )
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


__all__ = ["DailyJobError", "emit_cli_failure", "failure_path_for", "run_daily_job"]
