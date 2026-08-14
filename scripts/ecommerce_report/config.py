from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, ClassVar, Mapping
from urllib.parse import urlparse

from .platforms import (
    PlatformAdapterRegistry,
    PrimaryPlatformConfig,
    build_default_registry,
)


@dataclass(frozen=True)
class EchoTikCategory:
    path: tuple[str, ...]
    category_id: str


@dataclass(frozen=True)
class AmazonCategory:
    name: str
    url: str


DEFAULT_ECHOTIK_CATEGORIES = (
    EchoTikCategory(("宠物用品", "猫狗配件", "猫狗清洁美容"), "816392"),
    EchoTikCategory(("宠物用品", "猫狗配件", "猫狗服饰"), "813960"),
)

DEFAULT_AMAZON_CATEGORIES = (
    AmazonCategory(
        "Pet Grooming Supplies",
        "https://www.amazon.com/s?k=pet+grooming+supplies&i=pets",
    ),
    AmazonCategory(
        "Pet Clothing & Accessories",
        "https://www.amazon.com/s?k=pet+clothing+accessories&i=pets",
    ),
)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    frozen = _freeze(value)
    if not isinstance(frozen, Mapping):
        raise TypeError("expected a mapping")
    return frozen

DEFAULT_PRIMARY_PLATFORM = PrimaryPlatformConfig(
    adapter="echotik",
    categories=tuple(
        _freeze_mapping({"path": category.path, "id": category.category_id})
        for category in DEFAULT_ECHOTIK_CATEGORIES
    ),
    options=_freeze_mapping({}),
)


@dataclass(frozen=True, init=False)
class RuntimeConfig:
    output_dir: Path
    profile_dir: Path
    template_path: Path
    detail_limit: int = 20
    trend_days: int = 7
    pages_per_category: int = 10
    primary_platform: PrimaryPlatformConfig = DEFAULT_PRIMARY_PLATFORM
    amazon_categories: tuple[AmazonCategory, ...] = DEFAULT_AMAZON_CATEGORIES

    _ALLOWED_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "output_dir",
            "profile_dir",
            "template_path",
            "detail_limit",
            "trend_days",
            "pages_per_category",
            "primary_platform",
            "echotik_categories",
            "amazon_categories",
        }
    )
    _PRIMARY_PLATFORM_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"adapter", "categories", "options"}
    )
    _SAFE_ADAPTER_KEY: ClassVar[re.Pattern[str]] = re.compile(
        r"[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*"
    )
    _ECHOTIK_CATEGORY_FIELDS: ClassVar[frozenset[str]] = frozenset({"path", "id"})
    _SKILL_DIRECTORY: ClassVar[Path] = Path(__file__).resolve().parents[2]

    def __init__(
        self,
        output_dir: Path,
        profile_dir: Path,
        template_path: Path,
        detail_limit: int = 20,
        trend_days: int = 7,
        pages_per_category: int = 10,
        primary_platform: PrimaryPlatformConfig | None = None,
        echotik_categories: tuple[EchoTikCategory, ...] | None = None,
        amazon_categories: tuple[AmazonCategory, ...] = DEFAULT_AMAZON_CATEGORIES,
    ) -> None:
        if primary_platform is not None and echotik_categories is not None:
            raise ValueError(
                "primary_platform and echotik_categories cannot be combined"
            )
        if primary_platform is None:
            categories = (
                DEFAULT_ECHOTIK_CATEGORIES
                if echotik_categories is None
                else echotik_categories
            )
            primary_platform = PrimaryPlatformConfig(
                adapter="echotik",
                categories=tuple(
                    self._category_mapping(category) for category in categories
                ),
                options=_freeze_mapping({}),
            )
        normalized_primary = self._normalize_primary_platform(primary_platform)
        normalized_amazon = tuple(
            category
            if isinstance(category, AmazonCategory)
            else AmazonCategory(str(category["name"]), str(category["url"]))
            for category in amazon_categories
        )

        object.__setattr__(self, "output_dir", Path(output_dir))
        object.__setattr__(self, "profile_dir", Path(profile_dir))
        object.__setattr__(self, "template_path", Path(template_path))
        object.__setattr__(self, "detail_limit", detail_limit)
        object.__setattr__(self, "trend_days", trend_days)
        object.__setattr__(self, "pages_per_category", pages_per_category)
        object.__setattr__(self, "primary_platform", normalized_primary)
        object.__setattr__(self, "amazon_categories", normalized_amazon)

    @property
    def echotik_categories(self) -> tuple[EchoTikCategory, ...]:
        if self.primary_platform.adapter != "echotik":
            return ()
        return tuple(
            EchoTikCategory(tuple(category["path"]), str(category["id"]))
            for category in self.primary_platform.categories
        )

    @classmethod
    def load(
        cls,
        path: Path,
        registry: PlatformAdapterRegistry | None = None,
    ) -> "RuntimeConfig":
        config_path = cls.ensure_outside_skill(path, "configuration file")
        try:
            import yaml
        except ImportError as error:
            raise RuntimeError("RuntimeConfig.load requires PyYAML") from error

        with config_path.open("r", encoding="utf-8") as config_file:
            mapping = yaml.safe_load(config_file) or {}
        if not isinstance(mapping, Mapping):
            raise ValueError("configuration must be a mapping")
        config = cls.from_mapping(config_path.parent, mapping)
        active_registry = registry or build_default_registry()
        adapter = active_registry.resolve(config.primary_platform.adapter)
        adapter.validate_config(config.primary_platform)
        config.validate()
        return config

    @classmethod
    def from_mapping(cls, base: Path, mapping: Mapping[str, Any]) -> "RuntimeConfig":
        for field in mapping:
            if field not in cls._ALLOWED_FIELDS:
                raise ValueError(f"unknown configuration field: {field}")

        if "primary_platform" in mapping and "echotik_categories" in mapping:
            raise ValueError(
                "primary_platform and echotik_categories cannot be combined"
            )

        config_base = Path(base).resolve()
        if "primary_platform" in mapping:
            primary_platform = cls._parse_primary_platform(mapping["primary_platform"])
        else:
            legacy_categories = mapping.get(
                "echotik_categories", DEFAULT_ECHOTIK_CATEGORIES
            )
            primary_platform = PrimaryPlatformConfig(
                adapter="echotik",
                categories=tuple(
                    cls._category_mapping(category) for category in legacy_categories
                ),
            )
        amazon_categories = tuple(
            category
            if isinstance(category, AmazonCategory)
            else AmazonCategory(str(category["name"]), str(category["url"]))
            for category in mapping.get("amazon_categories", DEFAULT_AMAZON_CATEGORIES)
        )

        return cls(
            output_dir=cls._resolve(config_base, mapping.get("output_dir", "./runtime/reports")),
            profile_dir=cls._resolve(config_base, mapping.get("profile_dir", "./runtime/browser-profile")),
            template_path=cls._resolve(config_base, mapping.get("template_path", "./assets/report-template.xlsx")),
            detail_limit=mapping.get("detail_limit", 20),
            trend_days=mapping.get("trend_days", 7),
            pages_per_category=mapping.get("pages_per_category", 10),
            primary_platform=primary_platform,
            amazon_categories=amazon_categories,
        )

    @classmethod
    def _parse_primary_platform(cls, value: Any) -> PrimaryPlatformConfig:
        if not isinstance(value, Mapping):
            raise ValueError("primary_platform must be a mapping")
        for field in value:
            if field not in cls._PRIMARY_PLATFORM_FIELDS:
                raise ValueError(f"unknown primary_platform field: {field}")

        adapter = value.get("adapter", "echotik")
        categories = value.get("categories", ())
        options = value.get("options", {})
        if not isinstance(adapter, str) or not adapter.strip():
            raise ValueError("primary_platform adapter must be a non-empty registry key")
        cls._validate_adapter_key(adapter)
        if not isinstance(categories, (list, tuple)):
            raise ValueError("primary_platform categories must be a sequence")
        if not isinstance(options, Mapping):
            raise ValueError("primary_platform options must be a mapping")
        return PrimaryPlatformConfig(
            adapter=adapter,
            categories=tuple(
                cls._category_mapping(category) for category in categories
            ),
            options=_freeze_mapping(options),
        )

    @staticmethod
    def _category_mapping(category: Any) -> Mapping[str, Any]:
        if isinstance(category, EchoTikCategory):
            return _freeze_mapping(
                {"path": category.path, "id": category.category_id}
            )
        if not isinstance(category, Mapping):
            raise ValueError("primary_platform category must be a mapping")
        return _freeze_mapping(category)

    @classmethod
    def _normalize_primary_platform(
        cls, config: PrimaryPlatformConfig
    ) -> PrimaryPlatformConfig:
        cls._validate_adapter_key(config.adapter)
        if not isinstance(config.categories, (list, tuple)):
            raise ValueError("primary_platform categories must be a sequence")
        if not isinstance(config.options, Mapping):
            raise ValueError("primary_platform options must be a mapping")
        return PrimaryPlatformConfig(
            adapter=config.adapter,
            categories=tuple(
                cls._category_mapping(category) for category in config.categories
            ),
            options=_freeze_mapping(config.options),
        )

    @classmethod
    def _validate_adapter_key(cls, adapter: str) -> None:
        if not isinstance(adapter, str) or not cls._SAFE_ADAPTER_KEY.fullmatch(adapter):
            raise ValueError(
                "primary_platform adapter must be a safe internal registry key"
            )

    @staticmethod
    def _resolve(base: Path, value: str | Path) -> Path:
        path = Path(value)
        return path.resolve() if path.is_absolute() else (base / path).resolve()

    @classmethod
    def ensure_outside_skill(cls, path: Path, label: str) -> Path:
        resolved = Path(path).resolve()
        if resolved.is_relative_to(cls._SKILL_DIRECTORY):
            raise ValueError(f"{label} must not be inside the Skill directory")
        return resolved

    def validate(self) -> None:
        if self.detail_limit != 20:
            raise ValueError("detail_limit must be 20")
        if self.trend_days != 7:
            raise ValueError("trend_days must be 7")
        for name, path in (("output_dir", self.output_dir), ("profile_dir", self.profile_dir)):
            self.ensure_outside_skill(path, name)
        self._validate_adapter_key(self.primary_platform.adapter)
        if self.primary_platform.adapter == "echotik":
            if not self.primary_platform.categories:
                raise ValueError("at least one EchoTik category is required")
            for category in self.primary_platform.categories:
                unknown = set(category) - self._ECHOTIK_CATEGORY_FIELDS
                if unknown:
                    raise ValueError(
                        f"unknown EchoTik category field: {sorted(map(str, unknown))[0]}"
                    )
                missing = self._ECHOTIK_CATEGORY_FIELDS - set(category)
                if missing:
                    raise ValueError(
                        f"missing EchoTik category field: {sorted(missing)[0]}"
                    )
                path = category["path"]
                if not isinstance(path, (list, tuple)) or not path or any(not isinstance(label, str) or not label.strip() for label in path):
                    raise ValueError("EchoTik category path must contain non-empty labels")
                if not str(category["id"]).isdigit():
                    raise ValueError("EchoTik category ID must contain digits only")
        if not self.amazon_categories:
            raise ValueError("at least one Amazon category is required")
        for category in self.amazon_categories:
            if not category.name.strip():
                raise ValueError("Amazon category name must not be empty")
            parsed_url = urlparse(category.url)
            if parsed_url.scheme.lower() != "https" or not parsed_url.hostname:
                raise ValueError("Amazon category URL must use HTTPS")
