from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Mapping


@dataclass(frozen=True)
class RuntimeConfig:
    output_dir: Path
    profile_dir: Path
    template_path: Path
    detail_limit: int = 20
    trend_days: int = 7
    pages_per_category: int = 10
    categories: tuple[str, ...] = ("猫狗清洁美容", "猫狗服饰")

    SUPPORTED_CATEGORIES: ClassVar[dict[str, str]] = {
        "猫狗清洁美容": "816392",
        "猫狗服饰": "813960",
    }
    _ALLOWED_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {
            "output_dir",
            "profile_dir",
            "template_path",
            "detail_limit",
            "trend_days",
            "pages_per_category",
            "categories",
        }
    )
    _SKILL_DIRECTORY: ClassVar[Path] = Path(__file__).resolve().parents[2]

    @classmethod
    def load(cls, path: Path) -> "RuntimeConfig":
        try:
            import yaml
        except ImportError as error:
            raise RuntimeError("RuntimeConfig.load requires PyYAML") from error

        config_path = Path(path).resolve()
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
        raw_categories = mapping.get("categories", tuple(cls.SUPPORTED_CATEGORIES))
        if isinstance(raw_categories, Mapping):
            categories = tuple(raw_categories)
            for label, category_id in raw_categories.items():
                if cls.SUPPORTED_CATEGORIES.get(label) != str(category_id):
                    raise ValueError(f"unsupported category: {label}")
        else:
            categories = tuple(raw_categories)

        return cls(
            output_dir=cls._resolve(config_base, mapping.get("output_dir", "./runtime/reports")),
            profile_dir=cls._resolve(config_base, mapping.get("profile_dir", "./runtime/browser-profile")),
            template_path=cls._resolve(config_base, mapping.get("template_path", "./assets/report-template.xlsx")),
            detail_limit=mapping.get("detail_limit", 20),
            trend_days=mapping.get("trend_days", 7),
            pages_per_category=mapping.get("pages_per_category", 10),
            categories=categories,
        )

    @staticmethod
    def _resolve(base: Path, value: str | Path) -> Path:
        path = Path(value)
        return path.resolve() if path.is_absolute() else (base / path).resolve()

    def validate(self) -> None:
        if self.detail_limit != 20:
            raise ValueError("detail_limit must be 20")
        if self.trend_days != 7:
            raise ValueError("trend_days must be 7")
        for name, path in (("output_dir", self.output_dir), ("profile_dir", self.profile_dir)):
            if path.is_relative_to(self._SKILL_DIRECTORY):
                raise ValueError(f"{name} must not be inside the Skill directory")
        for category in self.categories:
            if category not in self.SUPPORTED_CATEGORIES:
                raise ValueError(f"unsupported category: {category}")
