from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.ecommerce_report.browser import (
    chrome_launch_options,
    open_echotik_context,
)
from scripts.ecommerce_report.config import AmazonCategory, EchoTikCategory, RuntimeConfig
from scripts.ecommerce_report.platforms import (
    PlatformAdapterRegistry,
    PlatformCapabilities,
    PrimaryPlatformConfig,
)


class FakeAdapter:
    key = "marketpulse"
    display_name = "MarketPulse"
    capabilities = PlatformCapabilities(True, True, True, True)

    def validate_config(self, config: PrimaryPlatformConfig) -> None:
        if not config.categories:
            raise ValueError("MarketPulse requires at least one category")

    def collect(self, context, config, *, detail_limit, trend_days, pages_per_category):
        raise AssertionError("configuration loading must not collect data")


class UnsafePathAdapter(FakeAdapter):
    key = "C:/temp/adapter.py"


class PublicSkillDocumentationTests(unittest.TestCase):
    def test_public_skill_requires_the_verified_python_version(self) -> None:
        """Lowering the documented minimum would claim an unverified runtime."""
        skill_root = Path(__file__).resolve().parents[1]
        configuration_reference = (
            skill_root / "references" / "configuration.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Python 3.12 or newer", configuration_reference)

        public_text_files = [skill_root / "SKILL.md"]
        for directory in ("agents", "references", "scripts"):
            public_text_files.extend(
                path
                for path in (skill_root / directory).rglob("*")
                if path.is_file()
                and path.suffix.lower() in {".md", ".ps1", ".py", ".txt", ".yaml", ".yml"}
            )
        forbidden_version = "Python 3." + "10"
        offenders = [
            str(path.relative_to(skill_root))
            for path in public_text_files
            if forbidden_version in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])


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

    def write_yaml(self, content: str) -> Path:
        path = self.base / "generated-config.yaml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_default_primary_platform_is_echotik(self) -> None:
        config = RuntimeConfig.from_mapping(self.base, {})

        self.assertEqual(config.primary_platform.adapter, "echotik")
        self.assertEqual(config.primary_platform.categories[0]["id"], "816392")

    def test_new_primary_platform_block_loads_registered_adapter(self) -> None:
        path = self.write_yaml(
            "primary_platform:\n"
            "  adapter: marketpulse\n"
            "  categories:\n"
            "    - path: [Home, Kitchen]\n"
            '      id: "42"\n'
            "  options:\n"
            "    region: US\n"
        )

        config = RuntimeConfig.load(
            path,
            registry=PlatformAdapterRegistry((FakeAdapter(),)),
        )

        self.assertEqual(config.primary_platform.adapter, "marketpulse")
        self.assertEqual(config.primary_platform.options, {"region": "US"})

    def test_selected_adapter_validates_configuration_during_load(self) -> None:
        path = self.write_yaml(
            "primary_platform:\n"
            "  adapter: marketpulse\n"
            "  categories: []\n"
        )

        with self.assertRaisesRegex(
            ValueError, "MarketPulse requires at least one category"
        ):
            RuntimeConfig.load(
                path,
                registry=PlatformAdapterRegistry((FakeAdapter(),)),
            )

    def test_legacy_echotik_categories_migrate_in_memory(self) -> None:
        config = RuntimeConfig.from_mapping(
            self.base,
            {"echotik_categories": [{"path": ["Home", "Kitchen"], "id": "123456"}]},
        )

        self.assertEqual(config.primary_platform.adapter, "echotik")
        self.assertEqual(config.primary_platform.categories[0]["id"], "123456")

    def test_configuration_rejects_adapter_executable_path(self) -> None:
        path = self.write_yaml(
            "primary_platform:\n"
            "  adapter: C:/temp/adapter.py\n"
            "  categories:\n"
            "    - path: [Home, Kitchen]\n"
            '      id: "42"\n'
        )

        with self.assertRaisesRegex(ValueError, "safe internal registry key"):
            RuntimeConfig.load(path)

    def test_configuration_rejects_unsafe_adapter_key_even_when_registered(self) -> None:
        unsafe_values = (
            "C:/temp/adapter.py",
            "remote.module:Adapter",
            "../adapter.py",
            r"local\adapter.py",
        )
        for unsafe_value in unsafe_values:
            with self.subTest(adapter=unsafe_value):
                adapter = UnsafePathAdapter()
                adapter.key = unsafe_value
                path = self.write_yaml(
                    "primary_platform:\n"
                    f"  adapter: {unsafe_value!r}\n"
                    "  categories:\n"
                    "    - path: [Home, Kitchen]\n"
                    '      id: "42"\n'
                )

                with self.assertRaisesRegex(
                    ValueError, "safe internal registry key"
                ):
                    RuntimeConfig.load(
                        path,
                        registry=PlatformAdapterRegistry((adapter,)),
                    )

    def test_configuration_rejects_ambiguous_legacy_and_new_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be combined"):
            RuntimeConfig.from_mapping(
                self.base,
                {
                    "primary_platform": {"adapter": "echotik", "categories": []},
                    "echotik_categories": [],
                },
            )

    def test_primary_platform_rejects_unsupported_keys(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown primary_platform field: module"):
            RuntimeConfig.from_mapping(
                self.base,
                {
                    "primary_platform": {
                        "adapter": "echotik",
                        "categories": [],
                        "module": "remote.module:Adapter",
                    }
                },
            )

    def test_echotik_category_rejects_unsupported_keys(self) -> None:
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "primary_platform": {
                    "adapter": "echotik",
                    "categories": [
                        {
                            "path": ["Home", "Kitchen"],
                            "id": "123456",
                            "module": "remote.module:Adapter",
                        }
                    ],
                }
            },
        )

        with self.assertRaisesRegex(
            ValueError, "unknown EchoTik category field: module"
        ):
            config.validate()

    def test_echotik_categories_is_derived_from_primary_platform(self) -> None:
        config = RuntimeConfig(
            output_dir=self.base / "reports",
            profile_dir=self.base / "profile",
            template_path=self.base / "template.xlsx",
            primary_platform=PrimaryPlatformConfig(
                adapter="echotik",
                categories=({"path": ["Home", "Kitchen"], "id": "654321"},),
            ),
        )

        self.assertEqual(
            config.echotik_categories,
            (EchoTikCategory(("Home", "Kitchen"), "654321"),),
        )
        self.assertNotIn("echotik_categories", config.__dict__)

    def test_direct_construction_rejects_two_category_sources(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be combined"):
            RuntimeConfig(
                output_dir=self.base / "reports",
                profile_dir=self.base / "profile",
                template_path=self.base / "template.xlsx",
                primary_platform=PrimaryPlatformConfig(
                    adapter="echotik",
                    categories=({"path": ["Home"], "id": "111111"},),
                ),
                echotik_categories=(
                    EchoTikCategory(("Kitchen",), "222222"),
                ),
            )

    def test_primary_platform_nested_values_are_immutable_snapshots(self) -> None:
        category = {"path": ["Home", "Kitchen"], "id": "123456"}
        options = {"filters": {"region": "US"}}
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "primary_platform": {
                    "adapter": "echotik",
                    "categories": [category],
                    "options": options,
                }
            },
        )

        category["id"] = "999999"
        category["path"].append("Changed")
        options["filters"]["region"] = "GB"
        self.assertEqual(config.primary_platform.categories[0]["id"], "123456")
        self.assertEqual(
            config.primary_platform.categories[0]["path"], ("Home", "Kitchen")
        )
        self.assertEqual(config.primary_platform.options["filters"]["region"], "US")
        with self.assertRaises(TypeError):
            config.primary_platform.categories[0]["id"] = "777777"

    def test_primary_platform_set_options_are_immutable_snapshots(self) -> None:
        source_tags = {"sale", "seasonal"}
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "primary_platform": {
                    "adapter": "echotik",
                    "categories": [
                        {"path": ["Home", "Kitchen"], "id": "123456"}
                    ],
                    "options": {"tags": source_tags},
                }
            },
        )

        source_tags.add("changed")
        self.assertEqual(
            config.primary_platform.options["tags"],
            frozenset({"sale", "seasonal"}),
        )

        path = self.write_yaml(
            "primary_platform:\n"
            "  adapter: echotik\n"
            "  categories:\n"
            "    - path: [Home, Kitchen]\n"
            '      id: "123456"\n'
            "  options:\n"
            "    tags: !!set {sale: null, seasonal: null}\n"
        )
        loaded = RuntimeConfig.load(path)
        self.assertEqual(
            loaded.primary_platform.options["tags"],
            frozenset({"sale", "seasonal"}),
        )

    def test_relative_paths_resolve_from_the_configuration_directory(self) -> None:
        """A resolver change using the working directory would break this test."""
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": "./runtime/reports",
                "profile_dir": "./runtime/browser-profile",
                "template_path": "./assets/report-template.xlsx",
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
            "echotik_categories:\n"
            "  - path: [Home & Garden, Kitchen]\n"
            '    id: "123456"\n'
            "amazon_categories:\n"
            "  - name: Kitchen\n"
            "    url: https://www.amazon.com/kitchen/b?node=1055398\n",
            encoding="utf-8",
        )

        config = RuntimeConfig.load(config_path)

        self.assertEqual(config.output_dir, self.base / "runtime" / "reports")
        self.assertEqual(config.echotik_categories, (EchoTikCategory(("Home & Garden", "Kitchen"), "123456"),))
        self.assertEqual(
            config.amazon_categories,
            (AmazonCategory("Kitchen", "https://www.amazon.com/kitchen/b?node=1055398"),),
        )

    def test_example_configuration_keeps_runtime_data_outside_the_skill(self) -> None:
        """Changing the example back to Skill-local runtime paths would fail this test."""
        skill_directory = Path(__file__).resolve().parents[1]
        local_copy = self.base / "config.yaml"
        local_copy.write_bytes(
            (skill_directory / "scripts" / "config.example.yaml").read_bytes()
        )
        config = RuntimeConfig.load(local_copy)

        config.validate()
        self.assertFalse(config.output_dir.is_relative_to(skill_directory))
        self.assertFalse(config.profile_dir.is_relative_to(skill_directory))
        self.assertEqual(
            config.echotik_categories,
            (
                EchoTikCategory(("宠物用品", "猫狗配件", "猫狗清洁美容"), "816392"),
                EchoTikCategory(("宠物用品", "猫狗配件", "猫狗服饰"), "813960"),
            ),
        )
        self.assertTrue(all(category.url.startswith("https://www.amazon.com/") for category in config.amazon_categories))

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

    def test_load_rejects_an_invalid_amazon_url(self) -> None:
        """Omitting validation from load would permit a non-HTTPS Amazon URL."""
        config_path = self.base / "invalid-amazon-url.yaml"
        config_path.write_text(
            "amazon_categories:\n"
            "  - name: Books\n"
            "    url: http://www.amazon.com/books\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "Amazon category URL must use HTTPS"):
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
            },
        )

        with self.assertRaisesRegex(ValueError, "output_dir must not be inside the Skill directory"):
            config.validate()

    def test_configuration_file_is_rejected_before_loading_when_inside_skill(self) -> None:
        """Opening a Skill-local config first could consume committed secrets before rejecting it."""
        skill_directory = Path(__file__).resolve().parents[1]

        try:
            RuntimeConfig.load(skill_directory / "private-config.yaml")
        except Exception as error:
            self.assertIs(type(error), ValueError)
            self.assertEqual(
                str(error),
                "configuration file must not be inside the Skill directory",
            )
        else:
            self.fail("Skill-local configuration was accepted")

    def test_public_config_rejects_a_profile_inside_the_skill(self) -> None:
        """Removing the profile-directory guard would make this test fail."""
        skill_directory = Path(__file__).resolve().parents[1]
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": "./runtime/reports",
                "profile_dir": str(skill_directory / "runtime" / "browser-profile"),
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
                        },
                    )

    def test_public_config_accepts_non_pet_categories(self) -> None:
        """Reintroducing a product-specific allow-list would reject this valid config."""
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": "./runtime/reports",
                "profile_dir": "./runtime/browser-profile",
                "echotik_categories": [
                    {"path": ["Home & Garden", "Kitchen"], "id": "123456"},
                ],
                "amazon_categories": [
                    {"name": "Books", "url": "https://www.amazon.com/books-used-books-textbooks/b?node=283155"},
                ],
            },
        )

        config.validate()
        self.assertEqual(config.echotik_categories[0].path, ("Home & Garden", "Kitchen"))
        self.assertEqual(config.amazon_categories[0].name, "Books")

    def test_echotik_category_requires_a_non_empty_visible_path(self) -> None:
        """Dropping path validation would accept empty or invisible menu labels."""
        for path in ([], ["Home", ""]):
            with self.subTest(path=path):
                config = RuntimeConfig.from_mapping(
                    self.base,
                    {"echotik_categories": [{"path": path, "id": "123456"}]},
                )
                with self.assertRaisesRegex(ValueError, "EchoTik category path must contain non-empty labels"):
                    config.validate()

    def test_echotik_category_id_must_be_numeric(self) -> None:
        """Dropping ID validation would accept a label or malformed identifier."""
        config = RuntimeConfig.from_mapping(
            self.base,
            {"echotik_categories": [{"path": ["Home", "Kitchen"], "id": "12A456"}]},
        )

        with self.assertRaisesRegex(ValueError, "EchoTik category ID must contain digits only"):
            config.validate()

    def test_amazon_category_requires_a_name_and_https_url(self) -> None:
        """Dropping Amazon field validation would accept unusable records."""
        cases = (
            ({"name": "", "url": "https://www.amazon.com/books"}, "Amazon category name must not be empty"),
            ({"name": "Books", "url": "http://www.amazon.com/books"}, "Amazon category URL must use HTTPS"),
            ({"name": "Books", "url": "https:"}, "Amazon category URL must use HTTPS"),
        )
        for category, message in cases:
            with self.subTest(category=category):
                config = RuntimeConfig.from_mapping(self.base, {"amazon_categories": [category]})
                with self.assertRaisesRegex(ValueError, message):
                    config.validate()

    def test_amazon_category_rejects_a_port_only_authority(self) -> None:
        """Checking netloc instead of hostname would accept a URL with no host."""
        config = RuntimeConfig.from_mapping(
            self.base,
            {"amazon_categories": [{"name": "Books", "url": "https://:443/books"}]},
        )

        with self.assertRaisesRegex(ValueError, "Amazon category URL must use HTTPS"):
            config.validate()

    def test_each_source_requires_at_least_one_category(self) -> None:
        """Removing source minimums would permit a report with no source coverage."""
        for field, message in (
            ("echotik_categories", "at least one EchoTik category is required"),
            ("amazon_categories", "at least one Amazon category is required"),
        ):
            with self.subTest(field=field):
                config = RuntimeConfig.from_mapping(self.base, {field: []})
                with self.assertRaisesRegex(ValueError, message):
                    config.validate()

    def test_browser_context_uses_the_isolated_profile_and_chrome_options(self) -> None:
        """Using a shared profile or omitting Chrome's isolation options would fail this test."""
        config = RuntimeConfig.from_mapping(
            self.base,
            {
                "output_dir": "./runtime/reports",
                "profile_dir": "./runtime/browser-profile",
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
