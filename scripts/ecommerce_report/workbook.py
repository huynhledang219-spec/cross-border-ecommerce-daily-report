"""Template-preserving Excel report export and inspection."""

from __future__ import annotations

import ast
import math
import os
import shutil
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.chart import LineChart, Reference

from .amazon import translate_amazon_title_to_chinese


REPORT_HEADERS = [
    "排名",
    "近7天重点选品",
    "来源",
    "品名关键词",
    "中文名称",
    "价格(USD)",
    "商品评分",
    "评论数",
    "GMV",
    "7天GMV",
    "7天销量",
    "关联视频",
    "关联达人",
    "EchoTik详情链接",
    "诊断",
]

_HELPER_HEADERS = tuple(f"趋势日{day}" for day in range(1, 8))
_DEFAULT_CHART_EXTENT = (3_513_455, 1_031_240)
_SOURCE_PRIORITY = {"你的库存": 0, "echotik": 1, "Amazon": 2}


@dataclass(frozen=True)
class ReportInspection:
    """Stable, read-only summary of workbook properties relevant to the Skill."""

    path: Path
    headers: tuple[str, ...]
    source_order: tuple[str, ...]
    hidden_columns: tuple[str, ...]
    chart_count: int
    chart_extents: tuple[tuple[int, int], ...]
    visible_cells_only: tuple[bool, ...]
    formula_errors: tuple[str, ...]


def _excel_value(value: Any) -> Any:
    if value is pd.NA:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value.item() if hasattr(value, "item") else value


def _number(value: Any, default: float = -math.inf) -> float:
    numeric = pd.to_numeric(value, errors="coerce")
    return default if pd.isna(numeric) else float(numeric)


def _complete_trend(value: Any) -> list[float] | None:
    if isinstance(value, str):
        try:
            value = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return None
    if not isinstance(value, (list, tuple)) or len(value) != 7:
        return None
    try:
        values = [float(item) for item in value]
    except (TypeError, ValueError):
        return None
    if any(not math.isfinite(item) or item < 0 for item in values):
        return None
    return values


def _prepare_records(records: pd.DataFrame) -> list[dict[str, Any]]:
    prepared = [dict(record) for record in records.to_dict(orient="records")]
    echotik = [record for record in prepared if record.get("source") == "echotik"]
    top_records = sorted(
        echotik,
        key=lambda record: _number(record.get("gmv_7d")),
        reverse=True,
    )[:20]
    top_positions = {id(record): position for position, record in enumerate(top_records, 1)}

    for record in prepared:
        position = top_positions.get(id(record))
        record["_top_position"] = position
        record["近7天重点选品"] = f"Top {position}" if position else None
        if record.get("source") == "Amazon":
            complete_title = " ".join(str(record.get("name") or "").split())
            record["name_cn"] = (
                translate_amazon_title_to_chinese(complete_title)
                if complete_title
                else ""
            )

    def sort_key(record: dict[str, Any]) -> tuple[float, float, float, float]:
        source = str(record.get("source") or "")
        source_priority = float(_SOURCE_PRIORITY.get(source, len(_SOURCE_PRIORITY)))
        top_position = record.get("_top_position")
        top_group = 0.0 if top_position else 1.0
        top_order = float(top_position or 999)
        total_gmv = -_number(record.get("gmv"))
        if source != "echotik":
            top_group = 0.0
            top_order = 0.0
        return source_priority, top_group, top_order, total_gmv

    return sorted(prepared, key=sort_key)


def _report_row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "排名": record.get("rank"),
        "近7天重点选品": record.get("近7天重点选品"),
        "来源": record.get("source"),
        "品名关键词": record.get("name"),
        "中文名称": record.get("name_cn"),
        "价格(USD)": record.get("price"),
        "商品评分": record.get("rating"),
        "评论数": record.get("reviews"),
        "GMV": record.get("gmv"),
        "7天GMV": record.get("gmv_7d"),
        "7天销量": record.get("sold_7d"),
        "关联视频": record.get("videos"),
        "关联达人": record.get("creators"),
        "EchoTik详情链接": record.get("detail_url"),
        "诊断": record.get("diagnostic"),
    }


def _copy_row_style(worksheet, source_row: int, target_row: int) -> None:
    worksheet.row_dimensions[target_row].height = worksheet.row_dimensions[source_row].height
    for column in range(1, len(REPORT_HEADERS) + 1):
        source = worksheet.cell(source_row, column)
        target = worksheet.cell(target_row, column)
        target._style = copy(source._style)
        target.number_format = source.number_format
        target.protection = copy(source.protection)
        target.alignment = copy(source.alignment)


def write_report(
    records: pd.DataFrame,
    output_path: Path,
    template_path: Path,
) -> Path:
    """Write normalized records into a copy of an existing Excel template."""

    output_path = Path(output_path)
    template_path = Path(template_path)
    if not template_path.is_file():
        raise FileNotFoundError(f"报表格式模板不存在: {template_path}")
    if output_path.resolve() == template_path.resolve():
        raise ValueError("输出路径不能与模板路径相同")
    prepared = _prepare_records(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        dir=output_path.parent,
        prefix=f".{output_path.stem}-",
        suffix=".xlsx",
        delete=False,
    ) as temporary_file:
        staged_path = Path(temporary_file.name)
    try:
        shutil.copy2(template_path, staged_path)
        workbook = load_workbook(staged_path)
        try:
            worksheet = workbook.active
            reference_extent = _DEFAULT_CHART_EXTENT
            if worksheet._charts:
                anchor = worksheet._charts[0].anchor
                extent = getattr(anchor, "ext", None)
                if extent is not None:
                    reference_extent = (extent.cx, extent.cy)
            worksheet._charts = []

            if worksheet.max_column > len(REPORT_HEADERS):
                worksheet.delete_cols(
                    len(REPORT_HEADERS) + 1,
                    worksheet.max_column - len(REPORT_HEADERS),
                )
            for column, header in enumerate(REPORT_HEADERS, start=1):
                worksheet.cell(1, column).value = header

            existing_last_row = worksheet.max_row
            output_last_row = len(prepared) + 1
            for row in range(2, max(existing_last_row, output_last_row) + 1):
                for column in range(1, len(REPORT_HEADERS) + 1):
                    cell = worksheet.cell(row, column)
                    cell.value = None
                    cell.hyperlink = None

            style_source_row = 3 if existing_last_row >= 3 else 2
            for row in range(existing_last_row + 1, output_last_row + 1):
                _copy_row_style(worksheet, style_source_row, row)

            for output_row, record in enumerate(prepared, start=2):
                values = _report_row(record)
                for column, header in enumerate(REPORT_HEADERS, start=1):
                    worksheet.cell(output_row, column).value = _excel_value(
                        values.get(header)
                    )

            detail_column = REPORT_HEADERS.index("EchoTik详情链接") + 1
            diagnostic_column = REPORT_HEADERS.index("诊断") + 1
            detail_letter = worksheet.cell(1, detail_column).column_letter
            worksheet.column_dimensions[detail_letter].hidden = True
            for row in range(2, output_last_row + 1):
                cell = worksheet.cell(row, detail_column)
                detail_url = str(cell.value or "").strip()
                if detail_url:
                    cell.hyperlink = detail_url
                    cell.value = ""
                cell.number_format = ";;;"

            helper_start_column = len(REPORT_HEADERS) + 1
            for offset, header in enumerate(_HELPER_HEADERS):
                helper_column = helper_start_column + offset
                worksheet.cell(1, helper_column).value = header
                helper_letter = worksheet.cell(1, helper_column).column_letter
                worksheet.column_dimensions[helper_letter].hidden = True

            for output_row, record in enumerate(prepared, start=2):
                if record.get("_top_position") is None:
                    continue
                trend = _complete_trend(record.get("gmv_trend_7d"))
                if trend is None:
                    worksheet.cell(output_row, diagnostic_column).value = "数据为空"
                    continue
                for offset, value in enumerate(trend):
                    worksheet.cell(output_row, helper_start_column + offset).value = value
                worksheet.cell(output_row, diagnostic_column).value = None

                chart = LineChart()
                chart.width = reference_extent[0] / 360_000
                chart.height = reference_extent[1] / 360_000
                chart.legend = None
                chart.y_axis.delete = True
                chart.x_axis.delete = True
                chart.visible_cells_only = False
                chart.add_data(
                    Reference(
                        worksheet,
                        min_col=helper_start_column,
                        max_col=helper_start_column + 6,
                        min_row=output_row,
                        max_row=output_row,
                    ),
                    from_rows=True,
                    titles_from_data=False,
                )
                chart.series[0].graphicalProperties.line.solidFill = "5B4CF0"
                chart.series[0].graphicalProperties.line.width = 22_000
                diagnostic_letter = worksheet.cell(1, diagnostic_column).column_letter
                worksheet.add_chart(chart, f"{diagnostic_letter}{output_row}")

            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = f"A1:O{output_last_row}"
            workbook.save(staged_path)
        finally:
            workbook.close()

        verification_workbook = load_workbook(staged_path, read_only=False)
        verification_workbook.close()
        os.replace(staged_path, output_path)
    finally:
        staged_path.unlink(missing_ok=True)
    return output_path


def inspect_report(path: Path) -> ReportInspection:
    """Inspect workbook structure without changing the report."""

    path = Path(path)
    workbook = load_workbook(path, data_only=False)
    try:
        worksheet = workbook.active
        headers = tuple(worksheet.cell(1, column).value for column in range(1, 16))

        source_column = REPORT_HEADERS.index("来源") + 1
        source_order: list[str] = []
        for row in range(2, worksheet.max_row + 1):
            source = worksheet.cell(row, source_column).value
            if source and source not in source_order:
                source_order.append(str(source))

        hidden_columns: list[str] = []
        for column in range(1, worksheet.max_column + 1):
            letter = worksheet.cell(1, column).column_letter
            header = worksheet.cell(1, column).value
            if worksheet.column_dimensions[letter].hidden and header:
                hidden_columns.append(str(header))

        formula_errors: list[str] = []
        for audit_sheet in workbook.worksheets:
            for row in audit_sheet.iter_rows():
                for cell in row:
                    if cell.data_type in {"e", "f"}:
                        formula_errors.append(
                            f"{audit_sheet.title}!{cell.coordinate}:{cell.value}"
                        )

        charts = tuple(worksheet._charts)
        return ReportInspection(
            path=path,
            headers=tuple(str(header) for header in headers),
            source_order=tuple(source_order),
            hidden_columns=tuple(hidden_columns),
            chart_count=len(charts),
            chart_extents=tuple(
                (chart.anchor.ext.cx, chart.anchor.ext.cy) for chart in charts
            ),
            visible_cells_only=tuple(chart.visible_cells_only for chart in charts),
            formula_errors=tuple(formula_errors),
        )
    finally:
        workbook.close()


__all__ = ["REPORT_HEADERS", "ReportInspection", "inspect_report", "write_report"]
