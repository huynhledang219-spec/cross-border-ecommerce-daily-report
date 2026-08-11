from __future__ import annotations

import html
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from scripts.ecommerce_report.workbook import REPORT_HEADERS


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ASSET_PATH = REPOSITORY_ROOT / "assets" / "report-template.xlsx"
SOURCE_PATH = (
    REPOSITORY_ROOT.parent
    / "跨境电商自动化"
    / "自动化每日数据报表"
    / "2026.8.11数据报表.xlsx"
)
EXPECTED_WIDTHS = (
    6.0,
    10.0,
    28.0,
    24.0,
    32.8571428571429,
    10.0,
    13.0,
    14.0,
    13.0,
    13.0,
    10.0,
    13.0,
    13.0,
    13.0,
    52.9333333333333,
)
EXPECTED_CHART_EXTENT = (3_513_455, 1_031_240)


def _assert_asset_exists(test: unittest.TestCase) -> None:
    test.assertTrue(ASSET_PATH.is_file(), "public workbook asset is absent")


def _style_fingerprint(cell) -> tuple[object, ...]:
    font_color = cell.font.color
    fill_color = cell.fill.fgColor
    return (
        cell.font.name,
        cell.font.sz,
        cell.font.bold,
        cell.font.italic,
        font_color.type if font_color else None,
        font_color.rgb if font_color and font_color.type == "rgb" else None,
        font_color.indexed if font_color and font_color.type == "indexed" else None,
        font_color.theme if font_color and font_color.type == "theme" else None,
        cell.fill.fill_type,
        fill_color.type,
        fill_color.rgb if fill_color.type == "rgb" else None,
        fill_color.indexed if fill_color.type == "indexed" else None,
        fill_color.theme if fill_color.type == "theme" else None,
        cell.border.left.style,
        cell.border.right.style,
        cell.border.top.style,
        cell.border.bottom.style,
        cell.alignment.horizontal,
        cell.alignment.vertical,
        cell.alignment.wrap_text,
        cell.number_format,
        cell.protection.locked,
        cell.protection.hidden,
    )


def _source_business_samples() -> tuple[str, ...]:
    """Return opaque source samples used only by non-disclosure assertions."""
    workbook = load_workbook(SOURCE_PATH, read_only=True, data_only=False, keep_links=False)
    try:
        worksheet = workbook.active
        samples: list[str] = []
        for row in worksheet.iter_rows(min_row=2, max_col=15, values_only=True):
            for column in (3, 4, 13, 14):
                value = row[column]
                if isinstance(value, str) and len(value.strip()) >= 8:
                    samples.append(value.strip())
                    if len(samples) == 24:
                        return tuple(samples)
        return tuple(samples)
    finally:
        workbook.close()


class PublicWorkbookAssetTests(unittest.TestCase):
    def test_contains_only_the_approved_header_row(self) -> None:
        _assert_asset_exists(self)
        workbook = load_workbook(ASSET_PATH, read_only=False, data_only=False, keep_links=False)
        try:
            self.assertEqual(len(workbook.worksheets), 1)
            worksheet = workbook.active
            self.assertEqual(worksheet.sheet_state, "visible")
            self.assertEqual(worksheet.max_row, 1)
            self.assertEqual(worksheet.max_column, 15)
            self.assertEqual(
                [worksheet.cell(1, column).value for column in range(1, 16)],
                REPORT_HEADERS,
            )
            self.assertTrue(
                all(
                    cell.value in REPORT_HEADERS
                    for row in worksheet.iter_rows()
                    for cell in row
                    if cell.value is not None
                )
            )
        finally:
            workbook.close()

    def test_retains_only_allowlisted_layout_style_and_chart_extent(self) -> None:
        _assert_asset_exists(self)
        self.assertTrue(SOURCE_PATH.is_file(), "private source fixture is unavailable")
        source = load_workbook(SOURCE_PATH, read_only=False, data_only=False, keep_links=False)
        asset = load_workbook(ASSET_PATH, read_only=False, data_only=False, keep_links=False)
        try:
            source_sheet = source.active
            asset_sheet = asset.active
            self.assertEqual(
                tuple(
                    asset_sheet.column_dimensions[get_column_letter(column)].width
                    for column in range(1, 16)
                ),
                EXPECTED_WIDTHS,
            )
            self.assertEqual(asset_sheet.row_dimensions[1].height, 32.0)
            self.assertEqual(
                [
                    (
                        asset_sheet.cell(1, column).alignment.horizontal,
                        asset_sheet.cell(1, column).alignment.vertical,
                        asset_sheet.cell(1, column).alignment.wrap_text,
                    )
                    for column in range(1, 16)
                ],
                [("center", "center", True)] * 15,
            )
            self.assertEqual(
                [_style_fingerprint(asset_sheet.cell(1, column)) for column in range(1, 16)],
                [_style_fingerprint(source_sheet.cell(1, column)) for column in range(1, 16)],
            )
            self.assertEqual(len(asset_sheet._charts), 1)
            chart = asset_sheet._charts[0]
            self.assertEqual(len(chart.series), 0)
            self.assertEqual((chart.anchor.ext.cx, chart.anchor.ext.cy), EXPECTED_CHART_EXTENT)
        finally:
            source.close()
            asset.close()

    def test_has_no_workbook_level_or_cell_level_active_content(self) -> None:
        _assert_asset_exists(self)
        workbook = load_workbook(ASSET_PATH, read_only=False, data_only=False, keep_links=False)
        try:
            self.assertEqual(list(workbook.defined_names.values()), [])
            self.assertEqual(getattr(workbook, "_external_links", []), [])
            for worksheet in workbook.worksheets:
                for row in worksheet.iter_rows():
                    for cell in row:
                        self.assertNotEqual(cell.data_type, "f")
                        self.assertIsNone(cell.hyperlink)
                        self.assertIsNone(cell.comment)
        finally:
            workbook.close()

    def test_zip_payload_has_no_private_or_external_parts(self) -> None:
        _assert_asset_exists(self)
        forbidden_fragments = (
            "externallinks/",
            "media/",
            "comments",
            "vml",
            "customxml/",
            "docprops/custom.xml",
            "connections",
            "querytables/",
            "pivotcache/",
            "embeddings/",
            "activex/",
            "macros/",
        )
        with ZipFile(ASSET_PATH) as archive:
            names = tuple(name.lower() for name in archive.namelist())
            self.assertTrue(all(not name.endswith("/") for name in names))
            self.assertFalse(
                any(fragment in name for name in names for fragment in forbidden_fragments)
            )

            xml_parts: list[str] = []
            for name in archive.namelist():
                if not name.lower().endswith((".xml", ".rels")):
                    continue
                raw = archive.read(name)
                text = raw.decode("utf-8")
                xml_parts.append(text)
                root = ET.fromstring(raw)
                if name.lower().endswith(".rels"):
                    for relationship in root:
                        self.assertNotEqual(relationship.attrib.get("TargetMode"), "External")
                        target = relationship.attrib.get("Target", "").lower()
                        self.assertFalse(target.startswith(("http://", "https://", "file:")))

            joined_xml = "\n".join(xml_parts)
            self.assertNotIn("<f>", joined_xml)
            self.assertNotIn(":f>", joined_xml)
            self.assertNotIn("hyperlink", joined_xml.lower())
            for sample in _source_business_samples():
                self.assertNotIn(sample, joined_xml, "source business value leaked into archive")
                self.assertNotIn(
                    html.escape(sample), joined_xml, "escaped source business value leaked into archive"
                )


if __name__ == "__main__":
    unittest.main()
