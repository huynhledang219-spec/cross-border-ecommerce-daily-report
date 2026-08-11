from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.ecommerce_report.browser import (
    chrome_launch_options,
    open_echotik_context,
)
from scripts.ecommerce_report.config import RuntimeConfig


class RecordingChromium:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, dict]] = []

    def launch_persistent_context(self, user_data_dir: Path, **options: object) -> str:
        self.calls.append((user_data_dir, options))
        return "context"


class RecordingPlaywright:
    def __init__(self) -> None:
        self.chromium = RecordingChromium()


class ConfigAndBrowserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.base = Path(self.temp_dir.name) / "config"
        self.base.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_relative_paths_resolve_from_the_configuration_directory(self) -> None:
        """A resolver change using the working directory would break this test."""
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": "./runtime/reports",
                "profile_dir": "./runtime/browser-profile",
                "template_path": "./assets/report-template.xlsx",
                "categories": ["猫狗清洁美容", "猫狗服饰"],
            },
        )

        self.assertEqual(config.output_dir, self.base / "runtime" / "reports")
        self.assertEqual(config.profile_dir, self.base / "runtime" / "browser-profile")
        self.assertEqual(config.template_path, self.base / "assets" / "report-template.xlsx")

    def test_load_resolves_paths_from_the_yaml_file_directory(self) -> None:
        """Removing the YAML loader or resolving against cwd would break this test."""
        config_path = self.base / "config.yaml"
        config_path.write_text(
            "output_dir: ./runtime/reports\n"
            "profile_dir: ./runtime/browser-profile\n"
            "categories:\n"
            '  猫狗清洁美容: "816392"\n'
            '  猫狗服饰: "813960"\n',
            encoding="utf-8",
        )

        config = RuntimeConfig.load(config_path)

        self.assertEqual(config.output_dir, self.base / "runtime" / "reports")
        self.assertEqual(config.categories, ("猫狗清洁美容", "猫狗服饰"))
        config.validate()

    def test_example_configuration_keeps_runtime_data_outside_the_skill(self) -> None:
        """Changing the example back to Skill-local runtime paths would fail this test."""
        skill_directory = Path(__file__).resolve().parents[1]
        config = RuntimeConfig.load(skill_directory / "scripts" / "config.example.yaml")

        config.validate()
        self.assertFalse(config.output_dir.is_relative_to(skill_directory))
        self.assertFalse(config.profile_dir.is_relative_to(skill_directory))

    def test_load_rejects_invalid_detail_limit(self) -> None:
        """Omitting validation from load would let an invalid limit through."""
        config_path = self.base / "invalid-limit.yaml"
        config_path.write_text("detail_limit: 21\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "detail_limit must be 20"):
            RuntimeConfig.load(config_path)

    def test_load_rejects_a_runtime_path_inside_the_skill(self) -> None:
        """Omitting validation from load would permit Skill-local output."""
        skill_directory = Path(__file__).resolve().parents[1]
        config_path = self.base / "skill-local-output.yaml"
        config_path.write_text(
            f"output_dir: {skill_directory / 'runtime' / 'reports'}\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "output_dir must not be inside the Skill directory"):
            RuntimeConfig.load(config_path)

    def test_load_rejects_an_unknown_category(self) -> None:
        """Omitting validation from load would permit an unknown category."""
        config_path = self.base / "unknown-category.yaml"
        config_path.write_text("categories:\n  - unknown category\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "unsupported category: unknown category"):
            RuntimeConfig.load(config_path)

    def test_public_config_enforces_verified_limits(self) -> None:
        """Changing the verified detail limit would let an unsafe scrape through."""
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": "./runtime/reports",
                "profile_dir": "./runtime/browser-profile",
                "detail_limit": 21,
                "trend_days": 7,
                "categories": ["猫狗清洁美容", "猫狗服饰"],
            },
        )

        with self.assertRaisesRegex(ValueError, "detail_limit must be 20"):
            config.validate()

    def test_public_config_rejects_an_unverified_trend_window(self) -> None:
        """Changing the verified trend window would make this test fail."""
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": "./runtime/reports",
                "profile_dir": "./runtime/browser-profile",
                "detail_limit": 20,
                "trend_days": 8,
                "categories": ["猫狗清洁美容", "猫狗服饰"],
            },
        )

        with self.assertRaisesRegex(ValueError, "trend_days must be 7"):
            config.validate()

    def test_public_config_rejects_runtime_paths_inside_the_skill(self) -> None:
        """Removing the package-directory guard would make this test fail."""
        skill_directory = Path(__file__).resolve().parents[1]
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": str(skill_directory / "runtime" / "reports"),
                "profile_dir": "./runtime/browser-profile",
                "categories": ["猫狗清洁美容", "猫狗服饰"],
            },
        )

        with self.assertRaisesRegex(ValueError, "output_dir must not be inside the Skill directory"):
            config.validate()

    def test_public_config_rejects_a_profile_inside_the_skill(self) -> None:
        """Removing the profile-directory guard would make this test fail."""
        skill_directory = Path(__file__).resolve().parents[1]
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": "./runtime/reports",
                "profile_dir": str(skill_directory / "runtime" / "browser-profile"),
                "categories": ["猫狗清洁美容", "猫狗服饰"],
            },
        )

        with self.assertRaisesRegex(ValueError, "profile_dir must not be inside the Skill directory"):
            config.validate()

    def test_public_config_rejects_unknown_and_account_fields(self) -> None:
        """Removing the field allow-list would accept a private or misspelled setting."""
        for field, value in (
            ("account", "account-id"),
            ("username", "user-name"),
            ("email", "user@example.com"),
            ("password", "not-a-secret"),
            ("unknown_setting", "unexpected"),
        ):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, f"unknown configuration field: {field}"):
                    RuntimeConfig.from_mapping(
                        self.base,
                        {
                            "output_dir": "./runtime/reports",
                            "profile_dir": "./runtime/browser-profile",
                            field: value,
                            "categories": ["猫狗清洁美容", "猫狗服饰"],
                        },
                    )

    def test_public_config_rejects_unknown_category_labels(self) -> None:
        """Removing category allow-list validation would make this test fail."""
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": "./runtime/reports",
                "profile_dir": "./runtime/browser-profile",
                "categories": ["unknown category"],
            },
        )

        with self.assertRaisesRegex(ValueError, "unsupported category: unknown category"):
            config.validate()

    def test_browser_context_uses_the_isolated_profile_and_chrome_options(self) -> None:
        """Using a shared profile or omitting Chrome's isolation options would fail this test."""
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": "./runtime/reports",
                "profile_dir": "./runtime/browser-profile",
                "categories": ["猫狗清洁美容", "猫狗服饰"],
            },
        )
        playwright = RecordingPlaywright()

        context = open_echotik_context(playwright, config)

        self.assertEqual(context, "context")
        self.assertEqual(
            playwright.chromium.calls,
            [
                (
                    config.profile_dir,
                    {
                        "channel": "chrome",
                        "headless": False,
                        "no_viewport": True,
                    },
                )
            ],
        )
        self.assertEqual(chrome_launch_options(visible=True), playwright.chromium.calls[0][1])


if __name__ == "__main__":
    unittest.main()
