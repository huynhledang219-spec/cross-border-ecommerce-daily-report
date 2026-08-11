from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Mapping
from urllib.parse import urlparse


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


@dataclass(frozen=True)
class RuntimeConfig:
    output_dir: Path
    profile_dir: Path
    template_path: Path
    detail_limit: int = 20
    trend_days: int = 7
    pages_per_category: int = 10
    echotik_categories: tuple[EchoTikCategory, ...] = DEFAULT_ECHOTIK_CATEGORIES
    amazon_categories: tuple[AmazonCategory, ...] = DEFAULT_AMAZON_CATEGORIES

    _ALLOWED_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "output_dir",
            "profile_dir",
            "template_path",
            "detail_limit",
            "trend_days",
            "pages_per_category",
            "echotik_categories",
            "amazon_categories",
        }
    )
    _SKILL_DIRECTORY: ClassVar[Path] = Path(__file__).resolve().parents[2]

    @classmethod
    def load(cls, path: Path) -> "RuntimeConfig":
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
        config.validate()
        return config

    @classmethod
    def from_mapping(cls, base: Path, mapping: Mapping[str, Any]) -> "RuntimeConfig":
        for field in mapping:
            if field not in cls._ALLOWED_FIELDS:
                raise ValueError(f"unknown configuration field: {field}")

        config_base = Path(base).resolve()
        echotik_categories = tuple(
            category
            if isinstance(category, EchoTikCategory)
            else EchoTikCategory(tuple(category["path"]), str(category["id"]))
            for category in mapping.get("echotik_categories", DEFAULT_ECHOTIK_CATEGORIES)
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
            echotik_categories=echotik_categories,
            amazon_categories=amazon_categories,
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
        if not self.echotik_categories:
            raise ValueError("at least one EchoTik category is required")
        for category in self.echotik_categories:
            if not category.path or any(not isinstance(label, str) or not label.strip() for label in category.path):
                raise ValueError("EchoTik category path must contain non-empty labels")
            if not category.category_id.isdigit():
                raise ValueError("EchoTik category ID must contain digits only")
        if not self.amazon_categories:
            raise ValueError("at least one Amazon category is required")
        for category in self.amazon_categories:
            if not category.name.strip():
                raise ValueError("Amazon category name must not be empty")
            parsed_url = urlparse(category.url)
            if parsed_url.scheme.lower() != "https" or not parsed_url.hostname:
                raise ValueError("Amazon category URL must use HTTPS")
