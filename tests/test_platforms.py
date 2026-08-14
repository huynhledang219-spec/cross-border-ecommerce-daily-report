from __future__ import annotations

import unittest

import pandas as pd

from scripts.ecommerce_report.platforms import (
    PlatformAdapterRegistry,
    PlatformCapabilities,
    PrimaryPlatformConfig,
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
