from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

import pandas as pd


REQUIRED_PRODUCT_FIELDS = frozenset(
    {
        "source",
        "name",
        "name_cn",
        "category",
        "price",
        "rating",
        "reviews",
        "gmv",
        "gmv_7d",
        "sold_7d",
        "videos",
        "creators",
        "detail_url",
    }
)


@dataclass(frozen=True)
class PlatformCapabilities:
    category_confirmation: bool
    seven_day_gmv: bool
    daily_sales_amount_trend: bool
    human_verification_detection: bool

    def missing_required(self) -> tuple[str, ...]:
        return tuple(name for name, enabled in vars(self).items() if not enabled)


@dataclass(frozen=True)
class PrimaryPlatformConfig:
    adapter: str = "echotik"
    categories: tuple[Mapping[str, Any], ...] = ()
    options: Mapping[str, Any] = field(default_factory=dict)


class PlatformAdapter(Protocol):
    key: str
    display_name: str
    capabilities: PlatformCapabilities

    def validate_config(self, config: PrimaryPlatformConfig) -> None: ...

    def collect(
        self,
        context,
        config: PrimaryPlatformConfig,
        *,
        detail_limit: int,
        trend_days: int,
        pages_per_category: int,
    ) -> pd.DataFrame: ...


class PlatformAdapterRegistry:
    def __init__(self, adapters: Sequence[PlatformAdapter]) -> None:
        self._adapters = {adapter.key: adapter for adapter in adapters}
        if len(self._adapters) != len(adapters):
            raise ValueError("duplicate primary platform adapter key")
        for adapter in adapters:
            missing = adapter.capabilities.missing_required()
            if missing:
                raise ValueError(
                    f"{adapter.display_name} missing required capabilities: {', '.join(missing)}"
                )

    def resolve(self, key: str) -> PlatformAdapter:
        try:
            return self._adapters[key]
        except KeyError as error:
            raise ValueError(f"unknown primary platform adapter: {key}") from error


def validate_normalized_records(records: pd.DataFrame, source: str) -> None:
    missing = REQUIRED_PRODUCT_FIELDS - set(records.columns)
    if missing:
        raise ValueError(
            f"{source} normalized product fields missing: {', '.join(sorted(missing))}"
        )
    if not records.empty and set(records["source"].dropna()) != {source}:
        raise ValueError(f"{source} normalized source label is inconsistent")


def build_default_registry() -> PlatformAdapterRegistry:
    from .echotik import ECHOTIK_ADAPTER

    return PlatformAdapterRegistry((ECHOTIK_ADAPTER,))
