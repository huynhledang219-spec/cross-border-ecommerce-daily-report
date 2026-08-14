from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from numbers import Real
from typing import Any, Mapping, Protocol, Sequence
from unicodedata import category
from urllib.parse import unquote, urlparse

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

_REQUIRED_TEXT_FIELDS = ("name", "name_cn", "category", "detail_url")
_REQUIRED_NUMERIC_FIELDS = (
    "price",
    "rating",
    "reviews",
    "gmv",
    "gmv_7d",
    "sold_7d",
    "videos",
    "creators",
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

    if not isinstance(source, str) or not source.strip():
        raise ValueError("normalized source display name must be a non-empty string")
    if any(value != source for value in records["source"]):
        raise ValueError(f"{source} normalized source label is inconsistent")

    for field_name in _REQUIRED_TEXT_FIELDS:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in records[field_name]
        ):
            raise ValueError(
                f"{source} normalized text field {field_name} must be a non-empty string"
            )

    for field_name in _REQUIRED_NUMERIC_FIELDS:
        if any(not _is_finite_nonnegative_number(value) for value in records[field_name]):
            raise ValueError(
                f"{source} normalized numeric field {field_name} must contain "
                "finite nonnegative numbers"
            )

    if any(not is_safe_detail_url(value) for value in records["detail_url"]):
        raise ValueError(
            f"{source} normalized detail_url must be an absolute HTTP(S) URL"
        )

    if "gmv_trend_7d" in records.columns:
        for trend in records["gmv_trend_7d"]:
            if _is_missing_optional_value(trend):
                continue
            if (
                isinstance(trend, (str, bytes, Mapping))
                or not isinstance(trend, Sequence)
                or len(trend) != 7
                or any(not _is_finite_nonnegative_number(value) for value in trend)
            ):
                raise ValueError(
                    f"{source} normalized gmv_trend_7d must contain exactly seven "
                    "finite nonnegative numbers"
                )


def _is_finite_nonnegative_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, Real)
        and isfinite(float(value))
        and value >= 0
    )


def is_safe_detail_url(value: Any) -> bool:
    """Accept only absolute browser-safe HTTP(S) product-detail URLs."""

    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or any(character.isspace() for character in value)
        or _has_url_control_or_format_character(value)
        or _has_url_control_or_format_character(unquote(value))
    ):
        return False
    try:
        parsed = urlparse(value)
        parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme.lower() in {"http", "https"}
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
    )


def _has_url_control_or_format_character(value: str) -> bool:
    return any(category(character) in {"Cc", "Cf"} for character in value)


def _is_missing_optional_value(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def build_default_registry() -> PlatformAdapterRegistry:
    from .echotik import ECHOTIK_ADAPTER

    return PlatformAdapterRegistry((ECHOTIK_ADAPTER,))
