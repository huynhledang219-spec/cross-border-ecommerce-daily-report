from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pandas as pd
from openpyxl import Workbook, load_workbook

from scripts.ecommerce_report.config import RuntimeConfig
from scripts.ecommerce_report.daily import failure_path_for, run_daily_job
from scripts.ecommerce_report.pipeline import PipelineError, run_pipeline
from scripts.ecommerce_report.workbook import REPORT_HEADERS
from scripts.run_daily import main as run_daily_main
from scripts.run_report import main as run_report_main


class _PlaywrightSession:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


def _create_template(path: Path) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(REPORT_HEADERS)
    worksheet.append([None] * len(REPORT_HEADERS))
    workbook.save(path)
    workbook.close()


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.template_path = self.root / "template.xlsx"
        self.output_path = self.root / "reports" / "report.xlsx"
        _create_template(self.template_path)
        self.config = RuntimeConfig.from_mapping(
            self.root,
            {
                "output_dir": "./reports",
                "profile_dir": "./profile",
                "template_path": "./template.xlsx",
                "echotik_categories": [
                    {"path": ["Home", "Kitchen"], "id": "123456"},
                ],
                "amazon_categories": [
                    {"name": "Kitchen", "url": "https://www.amazon.com/kitchen"},
                ],
            },
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @patch("scripts.ecommerce_report.pipeline.scrape_amazon")
    @patch("scripts.ecommerce_report.pipeline.scrape_echotik")
    @patch("scripts.ecommerce_report.pipeline.open_echotik_context")
    @patch("scripts.ecommerce_report.pipeline._playwright_session")
    def test_an_empty_top_trend_does_not_block_a_later_top_twenty_chart(
        self,
        playwright_session: Mock,
        open_context: Mock,
        scrape_echotik: Mock,
        scrape_amazon: Mock,
    ) -> None:
        """Aborting export after one empty trend would lose the later valid chart."""
        playwright_session.return_value = _PlaywrightSession()
        browser_context = Mock()
        open_context.return_value = browser_context
        scrape_echotik.return_value = pd.DataFrame(
            [
                {
                    "source": "echotik",
                    "name": "empty trend",
                    "gmv": 1000,
                    "gmv_7d": 100,
                    "detail_url": "/product/1",
                },
                {
                    "source": "echotik",
                    "name": "later trend",
                    "gmv": 900,
                    "gmv_7d": 90,
                    "detail_url": "/product/2",
                    "gmv_trend_7d": [1, 2, 3, 4, 5, 6, 7],
                },
            ]
        )
        scrape_amazon.return_value = pd.DataFrame()

        result = run_pipeline(self.config, self.output_path)

        workbook = load_workbook(result, data_only=False)
        try:
            worksheet = workbook.active
            self.assertEqual(worksheet["B2"].value, "Top 1")
            self.assertEqual(worksheet["O2"].value, "数据为空")
            self.assertEqual(worksheet["B3"].value, "Top 2")
            self.assertIsNone(worksheet["O3"].value)
            self.assertEqual(len(worksheet._charts), 1)
        finally:
            workbook.close()
        browser_context.close.assert_called_once_with()


class DailyJobTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.config_path = self.root / "config.yaml"
        self.config_path.write_text("unused", encoding="utf-8")
        self.config = Mock(output_dir=self.root / "reports")
        self.day = date(2026, 8, 11)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_failure_path_uses_the_dedicated_daily_failure_directory(self) -> None:
        """Changing the directory or date format would hide failures from operators."""
        self.assertEqual(
            failure_path_for(self.day, self.root / "reports"),
            self.root / "reports" / "数据报表_失败原因" / "2026.8.11失败原因.txt",
        )

    @patch("scripts.ecommerce_report.daily.run_pipeline")
    @patch("scripts.ecommerce_report.daily.RuntimeConfig.load")
    def test_existing_daily_report_is_returned_without_collecting_again(
        self, load_config: Mock, run_pipeline_mock: Mock
    ) -> None:
        """Removing the existence guard would repeat a completed daily scrape."""
        load_config.return_value = self.config
        expected = self.config.output_dir / "2026.8.11数据报表.xlsx"
        expected.parent.mkdir(parents=True)
        expected.write_bytes(b"complete")

        result = run_daily_job(self.config_path, self.day)

        self.assertEqual(result, expected)
        run_pipeline_mock.assert_not_called()

    @patch("scripts.ecommerce_report.daily._now")
    @patch("scripts.ecommerce_report.daily.run_pipeline")
    @patch("scripts.ecommerce_report.daily.RuntimeConfig.load")
    def test_failed_day_can_retry_and_success_removes_the_failure_record(
        self, load_config: Mock, run_pipeline_mock: Mock, now: Mock
    ) -> None:
        """Treating a failure file as completion would prevent same-day recovery."""
        load_config.return_value = self.config
        now.return_value = datetime(2026, 8, 11, 9, 7, 5)
        run_pipeline_mock.side_effect = PipelineError(
            "EchoTik采集",
            RuntimeError(
                "cookie=session-secret\n连接超时，请稍后重试\n"
                'File "C:\\private\\runner.py", line 1\nTraceback (most recent call last)'
            ),
        )

        with self.assertRaises(PipelineError):
            run_daily_job(self.config_path, self.day)

        failure_path = failure_path_for(self.day, self.config.output_dir)
        self.assertEqual(
            failure_path.read_text(encoding="utf-8"),
            "失败时间: 2026-08-11 09:07:05\n"
            "阶段: EchoTik采集\n"
            "原因: 连接超时，请稍后重试\n",
        )

        output_path = self.config.output_dir / "2026.8.11数据报表.xlsx"

        def successful_retry(config: RuntimeConfig, destination: Path) -> Path:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"complete")
            return destination

        run_pipeline_mock.side_effect = successful_retry

        result = run_daily_job(self.config_path, self.day)

        self.assertEqual(result, output_path)
        self.assertFalse(failure_path.exists())
        self.assertEqual(run_pipeline_mock.call_count, 2)

    @patch("scripts.ecommerce_report.daily.run_pipeline")
    @patch("scripts.ecommerce_report.daily.RuntimeConfig.load")
    def test_success_creates_only_the_workbook_not_a_success_log(
        self, load_config: Mock, run_pipeline_mock: Mock
    ) -> None:
        """Writing a success marker into the failure directory would misreport status."""
        load_config.return_value = self.config

        def write_report(config: RuntimeConfig, destination: Path) -> Path:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"complete")
            return destination

        run_pipeline_mock.side_effect = write_report

        result = run_daily_job(self.config_path, self.day)

        self.assertEqual(result.name, "2026.8.11数据报表.xlsx")
        self.assertFalse((self.config.output_dir / "数据报表_失败原因").exists())


class EntrypointTests(unittest.TestCase):
    @patch("scripts.run_report.run_pipeline")
    @patch("scripts.run_report.RuntimeConfig.load")
    def test_manual_entrypoint_accepts_config_and_explicit_output(
        self, load_config: Mock, run_pipeline_mock: Mock
    ) -> None:
        """Ignoring --output would write a manual report to the wrong destination."""
        config = Mock(output_dir=Path("default"))
        load_config.return_value = config
        run_pipeline_mock.return_value = Path("chosen.xlsx")

        code = run_report_main(["--config", "settings.yaml", "--output", "chosen.xlsx"])

        self.assertEqual(code, 0)
        load_config.assert_called_once_with(Path("settings.yaml"))
        run_pipeline_mock.assert_called_once_with(config, Path("chosen.xlsx"))

    @patch("scripts.run_daily.run_daily_job")
    def test_scheduled_entrypoint_returns_zero_only_on_success(
        self, run_daily_job_mock: Mock
    ) -> None:
        """Returning zero after an exception would conceal a failed scheduled run."""
        run_daily_job_mock.return_value = Path("report.xlsx")
        self.assertEqual(run_daily_main(["--config", "settings.yaml"]), 0)

        run_daily_job_mock.side_effect = RuntimeError("private details")
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(run_daily_main(["--config", "settings.yaml"]), 1)
        self.assertNotIn("private details", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
