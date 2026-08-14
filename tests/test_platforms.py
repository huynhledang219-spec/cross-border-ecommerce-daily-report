from __future__ import annotations

import unittest
from math import inf, nan
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.ecommerce_report.browser import (
    open_echotik_context,
    open_platform_context,
)
from scripts.ecommerce_report.echotik import ECHOTIK_ADAPTER
from scripts.ecommerce_report.config import RuntimeConfig
from scripts.ecommerce_report.platforms import (
    PlatformAdapterRegistry,
    PlatformCapabilities,
    PrimaryPlatformConfig,
    build_default_registry,
    validate_normalized_records,
)


class FakeAdapter:
    key = "marketpulse"
    display_name = "MarketPulse"
    capabilities = PlatformCapabilities(
        category_confirmation=True,
        seven_day_gmv=True,
        daily_sales_amount_trend=True,
        human_verification_detection=True,
    )

    def validate_config(self, config: PrimaryPlatformConfig) -> None:
        if not config.categories:
            raise ValueError("MarketPulse requires at least one category")

    def collect(self, context, config, *, detail_limit, trend_days, pages_per_category):
        return pd.DataFrame()


def _complete_normalized_records() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source": "MarketPulse",
                "name": "Original product title",
                "name_cn": "完整中文商品名",
                "category": "Home > Kitchen",
                "price": 19.99,
                "rating": 4.8,
                "reviews": 125,
                "gmv": 10_000.0,
                "gmv_7d": 2_500.0,
                "sold_7d": 80,
                "videos": 12,
                "creators": 7,
                "detail_url": "https://marketpulse.example/products/42?region=US",
                "gmv_trend_7d": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 400.0],
            },
            {
                "source": "MarketPulse",
                "name": "Second original title",
                "name_cn": "第二个完整中文商品名",
                "category": "Home > Storage",
                "price": 0,
                "rating": 0,
                "reviews": 0,
                "gmv": 0,
                "gmv_7d": 0,
                "sold_7d": 0,
                "videos": 0,
                "creators": 0,
                "detail_url": "http://marketpulse.example/products/43",
                "gmv_trend_7d": None,
            },
        ]
    )


class PlatformRegistryTests(unittest.TestCase):
    def test_platform_context_keeps_the_echotik_compatibility_alias(self) -> None:
        self.assertIs(open_echotik_context, open_platform_context)

    def test_echotik_adapter_declares_complete_capabilities(self) -> None:
        self.assertEqual(ECHOTIK_ADAPTER.key, "echotik")
        self.assertEqual(ECHOTIK_ADAPTER.display_name, "EchoTik")
        self.assertEqual(ECHOTIK_ADAPTER.capabilities.missing_required(), ())

    def test_echotik_adapter_rejects_unproven_category_id(self) -> None:
        config = PrimaryPlatformConfig(
            adapter="echotik",
            categories=(
                {"path": ["宠物用品", "猫狗配件"], "id": "not-numeric"},
            ),
        )

        with self.assertRaisesRegex(ValueError, "digits only"):
            ECHOTIK_ADAPTER.validate_config(config)

    def test_echotik_adapter_rejects_unsupported_options(self) -> None:
        config = PrimaryPlatformConfig(
            adapter="echotik",
            categories=({"path": ["Home", "Kitchen"], "id": "123456"},),
            options={"region": "US"},
        )

        with self.assertRaisesRegex(ValueError, "does not support options"):
            ECHOTIK_ADAPTER.validate_config(config)

    def test_runtime_config_load_rejects_unsupported_echotik_options(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "config.yaml"
            config_path.write_text(
                "primary_platform:\n"
                "  adapter: echotik\n"
                "  categories:\n"
                "    - path: [Home, Kitchen]\n"
                '      id: "123456"\n'
                "  options:\n"
                "    region: US\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "does not support options"):
                RuntimeConfig.load(config_path)

    def test_default_registry_resolves_echotik_with_complete_capabilities(self) -> None:
        adapter = build_default_registry().resolve("echotik")

        self.assertEqual(adapter.key, "echotik")
        self.assertEqual(adapter.display_name, "EchoTik")
        self.assertEqual(adapter.capabilities.missing_required(), ())

    def test_registry_resolves_only_registered_keys(self) -> None:
        registry = PlatformAdapterRegistry((FakeAdapter(),))
        self.assertEqual(registry.resolve("marketpulse").display_name, "MarketPulse")
        with self.assertRaisesRegex(ValueError, "unknown primary platform adapter"):
            registry.resolve("remote.module:Adapter")

    def test_registry_rejects_missing_required_capability(self) -> None:
        adapter = FakeAdapter()
        adapter.capabilities = PlatformCapabilities(
            category_confirmation=True,
            seven_day_gmv=True,
            daily_sales_amount_trend=False,
            human_verification_detection=True,
        )
        with self.assertRaisesRegex(ValueError, "missing required capabilities"):
            PlatformAdapterRegistry((adapter,))

    def test_normalized_records_require_report_fields(self) -> None:
        records = pd.DataFrame([{"source": "MarketPulse", "name": "Product"}])
        with self.assertRaisesRegex(ValueError, "normalized product fields"):
            validate_normalized_records(records, "MarketPulse")

    def test_complete_normalized_records_are_accepted(self) -> None:
        validate_normalized_records(_complete_normalized_records(), "MarketPulse")

    def test_empty_complete_frame_remains_for_pipeline_empty_source_handling(self) -> None:
        records = _complete_normalized_records().iloc[0:0]

        validate_normalized_records(records, "MarketPulse")

    def test_normalized_records_require_exact_nonblank_source_on_every_row(self) -> None:
        for invalid_source in (
            None,
            pd.NA,
            nan,
            "",
            "   ",
            "marketpulse",
            "EchoTik",
        ):
            with self.subTest(source=invalid_source):
                records = _complete_normalized_records()
                records.at[1, "source"] = invalid_source

                with self.assertRaisesRegex(ValueError, "source label is inconsistent"):
                    validate_normalized_records(records, "MarketPulse")

    def test_normalized_records_reject_null_or_blank_required_text(self) -> None:
        for field in ("name", "name_cn", "category", "detail_url"):
            for invalid_value in (None, "", "   "):
                with self.subTest(field=field, value=invalid_value):
                    records = _complete_normalized_records()
                    records[field] = records[field].astype(object)
                    records.at[0, field] = invalid_value

                    with self.assertRaisesRegex(ValueError, f"text field {field}"):
                        validate_normalized_records(records, "MarketPulse")

    def test_normalized_records_require_finite_nonnegative_numeric_fields(self) -> None:
        numeric_fields = (
            "price",
            "rating",
            "reviews",
            "gmv",
            "gmv_7d",
            "sold_7d",
            "videos",
            "creators",
        )
        for field in numeric_fields:
            for invalid_value in (None, "100", nan, inf, -1, True):
                with self.subTest(field=field, value=invalid_value):
                    records = _complete_normalized_records()
                    records[field] = records[field].astype(object)
                    records.at[0, field] = invalid_value

                    with self.assertRaisesRegex(ValueError, f"numeric field {field}"):
                        validate_normalized_records(records, "MarketPulse")

    def test_normalized_records_require_absolute_http_detail_urls(self) -> None:
        invalid_urls = (
            "products/42",
            "/products/42",
            "file:///etc/passwd",
            r"\\server\share\product.html",
            "javascript:alert(1)",
            "data:text/html,malicious",
            "https:///products/42",
            "https://user:password@marketpulse.example/products/42",
        )
        for invalid_url in invalid_urls:
            with self.subTest(url=invalid_url):
                records = _complete_normalized_records()
                records.at[0, "detail_url"] = invalid_url

                with self.assertRaisesRegex(ValueError, "absolute HTTP.S. URL"):
                    validate_normalized_records(records, "MarketPulse")

    def test_optional_trend_requires_seven_finite_nonnegative_values(self) -> None:
        invalid_trends = (
            [],
            [1, 2, 3, 4, 5, 6],
            [1, 2, 3, 4, 5, 6, nan],
            [1, 2, 3, 4, 5, 6, inf],
            [1, 2, 3, 4, 5, 6, -1],
            [1, 2, 3, 4, 5, 6, "7"],
        )
        for invalid_trend in invalid_trends:
            with self.subTest(trend=invalid_trend):
                records = _complete_normalized_records()
                records.at[0, "gmv_trend_7d"] = invalid_trend

                with self.assertRaisesRegex(ValueError, "seven finite nonnegative"):
                    validate_normalized_records(records, "MarketPulse")
