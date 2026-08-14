from __future__ import annotations

import unittest
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
