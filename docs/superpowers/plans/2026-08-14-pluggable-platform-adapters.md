# Pluggable Product-Intelligence Platform Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep EchoTik as the default product-intelligence source while allowing validated, registered platform adapters to produce the same Top-20, seven-day trend, Amazon-supplemented XLSX report.

**Architecture:** Introduce a small platform contract and registry between configuration and collection. Refactor EchoTik behind that contract, pass the selected primary source through the pipeline, and make workbook ranking, source ordering, link storage, and verification platform-neutral. Reject unknown or capability-incomplete adapters before export.

**Tech Stack:** Python 3.12+, `dataclasses`, `typing.Protocol`, pandas, Playwright synchronous API, openpyxl, PyYAML, Windows PowerShell, `unittest`.

## Global Constraints

- EchoTik remains the default adapter under the stable key `echotik` and display name `EchoTik`.
- Amazon remains a required supplementary source after the configured primary platform.
- `detail_limit` remains exactly `20`; `trend_days` remains exactly `7`.
- Open no more than the frozen Top 20 primary-platform detail pages.
- Accept only seven finite, nonnegative daily sales-amount values for a valid trend.
- Stop on login challenges, CAPTCHAs, or human-verification pages; never bypass or automate them.
- Preserve the 15 visible workbook columns and the current visible template layout.
- Rename only the hidden link header from `EchoTik详情链接` to `商品详情链接`.
- Keep credentials, cookies, browser profiles, local configuration, generated reports, and failure records outside the Skill directory.
- Configuration selects adapters only by an internal registry key and never loads executable paths or remote code.
- All new repository-facing prose and metadata is English.
- Use regression-first tests for every behavior change and commit after each independently passing task.

## File Map

- Create `scripts/ecommerce_report/platforms.py`: platform contract, capability declaration, registry, normalized-record validation, and default registry factory.
- Modify `scripts/ecommerce_report/config.py`: platform-neutral primary configuration plus legacy EchoTik migration.
- Modify `scripts/ecommerce_report/browser.py`: platform-neutral persistent Chrome context name with a compatibility alias.
- Modify `scripts/ecommerce_report/echotik.py`: `EchoTikAdapter` wrapper and EchoTik-specific configuration parsing.
- Modify `scripts/ecommerce_report/trends.py`: source-neutral Top-20 identity selection while keeping EchoTik DOM extraction local.
- Modify `scripts/ecommerce_report/pipeline.py`: resolve and run the configured primary adapter.
- Modify `scripts/ecommerce_report/workbook.py`: dynamic primary-source ranking, ordering, link header, and verification.
- Modify `assets/report-template.xlsx`: hidden header migration only.
- Modify `scripts/config.example.yaml`, `references/configuration.md`, `references/report-schema.md`, `SKILL.md`, and `agents/openai.yaml`: public contract and setup guidance.
- Create `tests/test_platforms.py`; modify the existing configuration, pipeline, source, workbook, and public-asset tests.

---

### Task 1: Platform Contract, Capabilities, and Registry

**Files:**
- Create: `scripts/ecommerce_report/platforms.py`
- Create: `tests/test_platforms.py`

**Interfaces:**
- Produces: `PlatformCapabilities`, `PrimaryPlatformConfig`, `PlatformAdapter`, `PlatformAdapterRegistry`, `validate_normalized_records()`, and `build_default_registry()`.
- `PlatformAdapter.collect(context, config, *, detail_limit, trend_days, pages_per_category) -> pandas.DataFrame` is the only collection interface consumed by the pipeline.

- [ ] **Step 1: Write registry and capability failure tests**

```python
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
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m unittest tests.test_platforms -v
```

Expected: import failure because `scripts.ecommerce_report.platforms` does not exist.

- [ ] **Step 3: Implement the minimal contract and closed registry**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

import pandas as pd


REQUIRED_PRODUCT_FIELDS = frozenset(
    {
        "source", "name", "name_cn", "category", "price", "rating",
        "reviews", "gmv", "gmv_7d", "sold_7d", "videos", "creators",
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
        return tuple(
            name
            for name, enabled in vars(self).items()
            if not enabled
        )


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
```

Implement `build_default_registry()` with a local import of `ECHOTIK_ADAPTER` so `platforms.py` does not create an import cycle with `config.py`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_platforms -v
```

Expected: all `PlatformRegistryTests` pass.

- [ ] **Step 5: Commit**

```powershell
git add scripts/ecommerce_report/platforms.py tests/test_platforms.py
git commit -m "feat: add product platform adapter contract"
```

---

### Task 2: Platform-Neutral Configuration with EchoTik Compatibility

**Files:**
- Modify: `scripts/ecommerce_report/config.py`
- Modify: `scripts/config.example.yaml`
- Modify: `tests/test_config_browser.py`

**Interfaces:**
- Consumes: `PrimaryPlatformConfig` and `PlatformAdapterRegistry` from Task 1.
- Produces: `RuntimeConfig.primary_platform: PrimaryPlatformConfig` and `RuntimeConfig.load(path, registry=None)`.
- Preserves: legacy `echotik_categories` input when `primary_platform` is absent.

- [ ] **Step 1: Add failing tests for default, new, legacy, and unsafe configuration**

```python
def test_default_primary_platform_is_echotik(self) -> None:
    config = RuntimeConfig.from_mapping(self.base, {})
    self.assertEqual(config.primary_platform.adapter, "echotik")
    self.assertEqual(config.primary_platform.categories[0]["id"], "816392")

def test_new_primary_platform_block_loads_registered_adapter(self) -> None:
    registry = PlatformAdapterRegistry((FakeAdapter(),))
    path = self.write_yaml(
        {
            "primary_platform": {
                "adapter": "marketpulse",
                "categories": [{"path": ["Home", "Kitchen"], "id": "42"}],
                "options": {"region": "US"},
            }
        }
    )
    config = RuntimeConfig.load(path, registry=registry)
    self.assertEqual(config.primary_platform.adapter, "marketpulse")

def test_legacy_echotik_categories_migrate_in_memory(self) -> None:
    config = RuntimeConfig.from_mapping(
        self.base,
        {"echotik_categories": [{"path": ["Home", "Kitchen"], "id": "123456"}]},
    )
    self.assertEqual(config.primary_platform.adapter, "echotik")
    self.assertEqual(config.primary_platform.categories[0]["id"], "123456")

def test_configuration_rejects_adapter_and_executable_path(self) -> None:
    path = self.write_yaml(
        {"primary_platform": {"adapter": "C:/temp/adapter.py", "categories": [{}]}}
    )
    with self.assertRaisesRegex(ValueError, "unknown primary platform adapter"):
        RuntimeConfig.load(path)

def test_configuration_rejects_ambiguous_legacy_and_new_fields(self) -> None:
    with self.assertRaisesRegex(ValueError, "cannot be combined"):
        RuntimeConfig.from_mapping(
            self.base,
            {
                "primary_platform": {"adapter": "echotik", "categories": []},
                "echotik_categories": [],
            },
        )
```

- [ ] **Step 2: Run focused configuration tests and verify RED**

Run:

```powershell
python -m unittest tests.test_config_browser -v
```

Expected: failures for the missing `primary_platform` field and registry-aware load path.

- [ ] **Step 3: Implement parsing and registry validation**

Add `primary_platform` to `RuntimeConfig`, retain `echotik_categories` only as a recognized legacy input field, and normalize both forms into `PrimaryPlatformConfig`.

```python
DEFAULT_PRIMARY_PLATFORM = PrimaryPlatformConfig(
    adapter="echotik",
    categories=tuple(
        {"path": category.path, "id": category.category_id}
        for category in DEFAULT_ECHOTIK_CATEGORIES
    ),
)

@classmethod
def load(cls, path: Path, registry=None) -> "RuntimeConfig":
    config_path = cls.ensure_outside_skill(path, "configuration file")
    with config_path.open("r", encoding="utf-8") as config_file:
        mapping = yaml.safe_load(config_file) or {}
    config = cls.from_mapping(config_path.parent, mapping)
    active_registry = registry or build_default_registry()
    adapter = active_registry.resolve(config.primary_platform.adapter)
    adapter.validate_config(config.primary_platform)
    config.validate()
    return config
```

Update `scripts/config.example.yaml` to:

```yaml
primary_platform:
  adapter: echotik
  categories:
    - path: ["宠物用品", "猫狗配件", "猫狗清洁美容"]
      id: "816392"
    - path: ["宠物用品", "猫狗配件", "猫狗服饰"]
      id: "813960"
  options: {}
```

- [ ] **Step 4: Run configuration and public-asset tests**

Run:

```powershell
python -m unittest tests.test_config_browser tests.test_public_asset -v
```

Expected: all tests pass, including the unchanged default EchoTik IDs and UTF-8 labels.

- [ ] **Step 5: Commit**

```powershell
git add scripts/ecommerce_report/config.py scripts/config.example.yaml tests/test_config_browser.py tests/test_public_asset.py
git commit -m "feat: configure a registered primary platform"
```

---

### Task 3: Refactor EchoTik into the Default Adapter

**Files:**
- Modify: `scripts/ecommerce_report/echotik.py`
- Modify: `scripts/ecommerce_report/trends.py`
- Modify: `scripts/ecommerce_report/browser.py`
- Modify: `tests/test_sources_trends.py`
- Modify: `tests/test_platforms.py`

**Interfaces:**
- Consumes: `PrimaryPlatformConfig`, `PlatformCapabilities`, and `PlatformAdapter`.
- Produces: `EchoTikAdapter`, `ECHOTIK_ADAPTER`, `select_top_detail_rows(records, source, limit)`, and `open_platform_context()`.

- [ ] **Step 1: Write failing EchoTik adapter compatibility tests**

```python
def test_echotik_adapter_declares_complete_capabilities(self) -> None:
    self.assertEqual(ECHOTIK_ADAPTER.key, "echotik")
    self.assertEqual(ECHOTIK_ADAPTER.display_name, "EchoTik")
    self.assertEqual(ECHOTIK_ADAPTER.capabilities.missing_required(), ())

def test_top_selection_uses_the_selected_source(self) -> None:
    records = [
        {"source": "MarketPulse", "gmv_7d": 200},
        {"source": "EchoTik", "gmv_7d": 300},
        {"source": "MarketPulse", "gmv_7d": 100},
    ]
    selected = select_top_detail_rows(records, "MarketPulse", 20)
    self.assertEqual([row["gmv_7d"] for row in selected], [200, 100])

def test_echotik_adapter_rejects_unproven_category_id(self) -> None:
    config = PrimaryPlatformConfig(
        adapter="echotik",
        categories=({"path": ["宠物用品", "猫狗配件"], "id": "not-numeric"},),
    )
    with self.assertRaisesRegex(ValueError, "digits only"):
        ECHOTIK_ADAPTER.validate_config(config)
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
python -m unittest tests.test_sources_trends tests.test_platforms -v
```

Expected: failures for the missing adapter and the old EchoTik-only Top selector signature.

- [ ] **Step 3: Add the EchoTik adapter without changing DOM logic**

```python
class EchoTikAdapter:
    key = "echotik"
    display_name = "EchoTik"
    capabilities = PlatformCapabilities(True, True, True, True)

    def validate_config(self, config: PrimaryPlatformConfig) -> None:
        _parse_echotik_categories(config.categories)

    def collect(
        self,
        context,
        config: PrimaryPlatformConfig,
        *,
        detail_limit: int,
        trend_days: int,
        pages_per_category: int,
    ) -> pd.DataFrame:
        if trend_days != 7:
            raise ValueError("EchoTik trend_days must be 7")
        return scrape_echotik(
            context,
            _parse_echotik_categories(config.categories),
            detail_limit=detail_limit,
            pages_per_category=pages_per_category,
        )


ECHOTIK_ADAPTER = EchoTikAdapter()
```

Change normalized EchoTik records from `source: "echotik"` to `source: "EchoTik"`. Change the Top selector to accept an explicit source label. Keep `read_7d_gmv_trend()` EchoTik-specific and preserve its current failure classes.

Rename `open_echotik_context()` to `open_platform_context()` and keep:

```python
open_echotik_context = open_platform_context
```

until all callers and tests migrate.

- [ ] **Step 4: Run EchoTik source, trend, and browser tests**

Run:

```powershell
python -m unittest tests.test_sources_trends tests.test_config_browser tests.test_platforms -v
```

Expected: all focused tests pass; existing challenge and empty-trend distinctions remain covered.

- [ ] **Step 5: Commit**

```powershell
git add scripts/ecommerce_report/echotik.py scripts/ecommerce_report/trends.py scripts/ecommerce_report/browser.py tests/test_sources_trends.py tests/test_platforms.py
git commit -m "refactor: expose EchoTik as the default adapter"
```

---

### Task 4: Platform-Neutral Pipeline and Synthetic Adapter Integration

**Files:**
- Modify: `scripts/ecommerce_report/pipeline.py`
- Modify: `tests/test_pipeline_daily.py`
- Modify: `tests/test_platforms.py`

**Interfaces:**
- Consumes: `RuntimeConfig.primary_platform`, `PlatformAdapterRegistry.resolve()`, and `validate_normalized_records()`.
- Produces: `run_pipeline(config, output_path, registry=None)` with dynamic primary stages and `write_report(..., primary_source=adapter.display_name)`.

- [ ] **Step 1: Write a failing synthetic non-EchoTik pipeline test**

```python
def test_pipeline_runs_registered_non_echotik_adapter(self) -> None:
    adapter = RecordingAdapter(
        key="marketpulse",
        display_name="MarketPulse",
        records=complete_platform_dataframe("MarketPulse", count=21),
    )
    registry = PlatformAdapterRegistry((adapter,))
    config = make_runtime_config(
        primary_platform=PrimaryPlatformConfig(
            adapter="marketpulse",
            categories=({"path": ["Home", "Kitchen"], "id": "42"},),
        )
    )
    with patch.object(pipeline, "_playwright_session", fake_session), patch.object(
        pipeline, "scrape_amazon", return_value=complete_amazon_dataframe()
    ), patch.object(pipeline, "write_report", return_value=self.output_path) as write_report:
        result = pipeline.run_pipeline(config, self.output_path, registry=registry)
    self.assertEqual(result, self.output_path)
    self.assertEqual(adapter.collect_calls, 1)
    self.assertEqual(write_report.call_args.kwargs["primary_source"], "MarketPulse")
```

Add negative tests proving that primary collection exceptions use `MarketPulse采集`, empty primary records fail before export, and normalized-field failures are not downgraded to empty data.

- [ ] **Step 2: Run pipeline tests and verify RED**

Run:

```powershell
python -m unittest tests.test_pipeline_daily -v
```

Expected: failure because `run_pipeline()` does not accept a registry and still calls `scrape_echotik()` directly.

- [ ] **Step 3: Resolve and execute the configured adapter**

```python
def run_pipeline(
    config: RuntimeConfig,
    output_path: Path,
    registry: PlatformAdapterRegistry | None = None,
) -> Path:
    active_registry = registry or build_default_registry()
    adapter = active_registry.resolve(config.primary_platform.adapter)
    adapter.validate_config(config.primary_platform)
    context = _at_stage(
        "启动浏览器", lambda: open_platform_context(playwright, config)
    )
    primary_records = _at_stage(
        f"{adapter.display_name}采集",
        lambda: adapter.collect(
            context,
            config.primary_platform,
            detail_limit=config.detail_limit,
            trend_days=config.trend_days,
            pages_per_category=config.pages_per_category,
        ),
    )
    validate_normalized_records(primary_records, adapter.display_name)
```

Preserve the existing `try/finally` shutdown structure, Amazon collection, empty-source failures, output isolation, and staged workbook export. Pass `primary_source=adapter.display_name` into `write_report()`.

- [ ] **Step 4: Run pipeline and daily-entrypoint tests**

Run:

```powershell
python -m unittest tests.test_pipeline_daily tests.test_platforms -v
```

Expected: all focused tests pass with sanitized dynamic stage names.

- [ ] **Step 5: Commit**

```powershell
git add scripts/ecommerce_report/pipeline.py tests/test_pipeline_daily.py tests/test_platforms.py
git commit -m "feat: run the configured product platform"
```

---

### Task 5: Platform-Neutral Workbook and Hidden Link Migration

**Files:**
- Modify: `scripts/ecommerce_report/workbook.py`
- Modify: `assets/report-template.xlsx`
- Modify: `tests/test_workbook.py`
- Modify: `tests/test_public_asset.py`

**Interfaces:**
- Consumes: normalized records and `primary_source` from Task 4.
- Produces: `write_report(records, output_path, template_path, primary_source="EchoTik")` and platform-neutral `verify_report()`.

- [ ] **Step 1: Write failing workbook tests for a non-EchoTik primary source**

```python
def test_report_ranks_configured_primary_source_and_keeps_amazon_last(self) -> None:
    records = make_records(primary_source="MarketPulse", primary_count=21, amazon_count=2)
    result = write_report(
        records,
        self.output_path,
        self.template_path,
        primary_source="MarketPulse",
    )
    workbook = load_workbook(result)
    worksheet = workbook.active
    self.assertEqual([worksheet.cell(row, 2).value for row in range(2, 22)], [f"Top {n}" for n in range(1, 21)])
    self.assertTrue(all(worksheet.cell(row, 3).value == "MarketPulse" for row in range(2, 22)))
    self.assertEqual(worksheet.cell(1, 14).value, "商品详情链接")
    self.assertTrue(worksheet.column_dimensions["N"].hidden)
    self.assertEqual(verify_report(result, self.template_path).source_order, ("MarketPulse", "Amazon"))

def test_verifier_rejects_top_rows_from_two_primary_sources(self) -> None:
    result = build_valid_report(primary_source="MarketPulse")
    workbook = load_workbook(result)
    workbook.active["C3"] = "EchoTik"
    workbook.save(result)
    with self.assertRaisesRegex(ValueError, "primary platform source"):
        verify_report(result, self.template_path)
```

Retain tests for 20-row maximum, descending seven-day GMV, row-bound charts, hidden trend data, chart dimensions, Amazon Chinese full titles, formulas, source continuity, and sensitive ZIP content.

- [ ] **Step 2: Run workbook and asset tests and verify RED**

Run:

```powershell
python -m unittest tests.test_workbook tests.test_public_asset -v
```

Expected: failures because ranking and verification are hard-coded to lowercase `echotik`, source order is static, and the hidden header is EchoTik-specific.

- [ ] **Step 3: Implement dynamic ranking and verification**

```python
REPORT_HEADERS = [
    "排名", "近7天重点选品", "来源", "品名关键词", "中文名称",
    "价格(USD)", "商品评分", "评论数", "GMV", "7天GMV",
    "7天销量", "关联视频", "关联达人", "商品详情链接", "诊断",
]

def _source_priority(source: str, primary_source: str) -> int:
    return {"你的库存": 0, primary_source: 1, "Amazon": 2}.get(source, 3)

def _prepare_records(records: pd.DataFrame, primary_source: str) -> list[dict[str, Any]]:
    prepared = [dict(record) for record in records.to_dict(orient="records")]
    primary = [record for record in prepared if record.get("source") == primary_source]
    top_records = sorted(
        primary,
        key=lambda record: _number(record.get("gmv_7d")),
        reverse=True,
    )[:20]
    # Preserve the existing Top label and stable source-group sorting logic.
```

In `verify_report()`, infer the primary source from nonempty Top rows, require exactly one primary source for all Top rows, reject `你的库存` or `Amazon` as the primary source, and validate group order as inventory, inferred primary, Amazon.

Update only cell `N1` in the sanitized template from `EchoTik详情链接` to `商品详情链接`. Preserve every other cell, style, dimension, chart, relationship, and archive part.

- [ ] **Step 4: Run workbook and asset tests and verify GREEN**

Run:

```powershell
python -m unittest tests.test_workbook tests.test_public_asset -v
```

Expected: all tests pass for both EchoTik and MarketPulse synthetic records; the public asset remains sanitized.

- [ ] **Step 5: Commit**

```powershell
git add scripts/ecommerce_report/workbook.py assets/report-template.xlsx tests/test_workbook.py tests/test_public_asset.py
git commit -m "feat: make report verification platform neutral"
```

---

### Task 6: English Skill Guidance and Public Metadata Files

**Files:**
- Modify: `SKILL.md`
- Modify: `agents/openai.yaml`
- Modify: `references/configuration.md`
- Modify: `references/report-schema.md`
- Modify: `scripts/config.example.yaml`
- Test: `tests/test_public_asset.py`

**Interfaces:**
- Documents: default EchoTik behavior, the registered-adapter workflow, equivalent-capability gate, local-only configuration, and unchanged human-verification boundaries.

- [ ] **Step 1: Add failing documentation-contract assertions**

```python
def test_public_guidance_documents_default_and_replaceable_platform(self) -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    config_reference = (ROOT / "references" / "configuration.md").read_text(encoding="utf-8")
    self.assertIn("EchoTik remains the default", skill)
    self.assertIn("equivalent-capability gate", skill)
    self.assertIn("registered adapter", config_reference)
    self.assertNotIn("README.md", {path.name for path in ROOT.iterdir()})

def test_openai_metadata_is_fully_english(self) -> None:
    metadata = yaml.safe_load((ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    serialized = yaml.safe_dump(metadata, allow_unicode=True)
    self.assertIsNone(re.search(r"[\u3400-\u9fff]", serialized))
    self.assertIn("product intelligence", metadata["interface"]["short_description"].lower())
```

- [ ] **Step 2: Run the public documentation tests and verify RED**

Run:

```powershell
python -m unittest tests.test_public_asset -v
```

Expected: failures because current metadata is EchoTik-specific and `agents/openai.yaml` contains Chinese display text.

- [ ] **Step 3: Update English guidance and interface metadata**

Use this frontmatter trigger description:

```yaml
---
name: cross-border-ecommerce-daily-report
description: Use when configuring, running, scheduling, troubleshooting, or validating a Windows daily product-intelligence report that uses EchoTik by default or a verified registered platform adapter, with Amazon as a supplementary source.
---
```

Use this interface metadata:

```yaml
interface:
  display_name: "Cross-Border E-Commerce Daily Report"
  short_description: "Generate validated multi-source product-intelligence reports"
  default_prompt: "Use $cross-border-ecommerce-daily-report to configure, generate, and verify today's cross-border e-commerce product-intelligence report."
```

Document that naming a website does not make it compatible: a new adapter, tests, visible evidence, and equivalent-capability validation are required before local configuration changes.

- [ ] **Step 4: Validate documentation and Skill metadata**

Run:

```powershell
python -m unittest tests.test_public_asset -v
$codexHome = $env:CODEX_HOME
if (-not $codexHome) { $codexHome = Join-Path $HOME ".codex" }
python (Join-Path $codexHome "skills/.system/skill-creator/scripts/quick_validate.py") "."
```

Expected: public documentation tests pass and quick validation reports a valid Skill.

- [ ] **Step 5: Commit**

```powershell
git add SKILL.md agents/openai.yaml references/configuration.md references/report-schema.md scripts/config.example.yaml tests/test_public_asset.py
git commit -m "docs: explain pluggable product platforms"
```

---

### Task 7: Full Regression, Security, and Synthetic Report Audit

**Files:**
- Modify only if a validation defect is found: relevant test or implementation file from Tasks 1–6
- Do not create tracked runtime reports, browser profiles, local configuration, credentials, or logs

**Interfaces:**
- Verifies the complete default EchoTik path and a synthetic non-EchoTik adapter path.

- [ ] **Step 1: Run the complete automated test suite**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: zero failures and zero errors.

- [ ] **Step 2: Compile every Python module**

Run:

```powershell
python -m compileall -q scripts tests
```

Expected: exit code `0`.

- [ ] **Step 3: Validate the Skill package**

Run:

```powershell
$codexHome = $env:CODEX_HOME
if (-not $codexHome) { $codexHome = Join-Path $HOME ".codex" }
python (Join-Path $codexHome "skills/.system/skill-creator/scripts/quick_validate.py") "."
```

Expected: valid Skill output and exit code `0`.

- [ ] **Step 4: Generate and verify a synthetic non-EchoTik report outside the Skill**

Use the test helpers to create one inventory row, 21 `MarketPulse` rows, and two Amazon rows under a temporary directory. Give 19 Top rows complete seven-value trends and one Top row `数据为空`. Run `write_report(..., primary_source="MarketPulse")`, then `verify_report()`.

Expected inspection:

```text
Top labels: Top 1 through Top 20
Primary source: MarketPulse
Amazon group: after MarketPulse
Charts: 19
Empty trend diagnostics: 1
Hidden columns: 商品详情链接 plus 趋势日1 through 趋势日7
Formula errors: 0
Sensitive content findings: 0
```

- [ ] **Step 5: Scan tracked files and Git state**

Run:

```powershell
git diff --check
git status --short
git ls-files
```

Inspect tracked paths and content for credentials, account identifiers, cookies, tokens, browser profiles, generated reports, failure records, `__pycache__`, `.pyc`, and private local configuration. Expected: no forbidden tracked artifacts and no unrelated changes.

- [ ] **Step 6: Handle a validation defect without an ambiguous commit**

If Step 1–5 exposes a defect, stop Task 7 and return to the owning task above. Add the failing regression test to that task's named test file, apply the smallest correction to that task's named implementation files, rerun both its focused command and every Task 7 command, then use that task's explicit `git add` list and commit command. If no correction is necessary, do not create an empty commit.

---

### Task 8: GitHub Metadata, Push, and Public Verification

**Files and external state:**
- Local Git branch: `main`
- GitHub repository: `huynhledang219-spec/cross-border-ecommerce-daily-report`
- GitHub description and repository topics

**Interfaces:**
- Publishes only commits that passed Task 7.
- Does not change visibility, permissions, collaborators, releases, packages, or Actions.

- [ ] **Step 1: Present the final English diff and Chinese explanation**

Show the maintainer the exact English Skill metadata, GitHub description, topics, visible workbook compatibility, hidden-header migration, and validation evidence in Chinese. Obtain explicit approval for the file changes, commits, GitHub metadata edit, and push.

- [ ] **Step 2: Update the GitHub description and topics**

Set the description exactly to:

```text
Configurable Codex Skill for cross-border e-commerce product intelligence, using EchoTik by default and validated platform adapters to generate daily Top-20 GMV and seven-day trend XLSX reports.
```

Set topics exactly to:

```text
amazon codex-skill cross-border-ecommerce ecommerce-analytics echotik playwright product-intelligence product-research windows-automation xlsx-reporting
```

Verify on the visible repository page that the repository remains public and the metadata is displayed.

- [ ] **Step 3: Push `main`**

Run:

```powershell
git push origin main
```

Expected: `main -> main` succeeds without force.

- [ ] **Step 4: Verify local and remote commit identity**

Run:

```powershell
git rev-parse HEAD
git ls-remote origin refs/heads/main
git status --short --branch
```

Expected: local and remote SHA values match; the working tree is clean and `main` tracks `origin/main` without ahead/behind counts.

- [ ] **Step 5: Verify the public repository contents**

Confirm the public `main` branch exposes `SKILL.md`, `agents/openai.yaml`, `assets/report-template.xlsx`, the platform contract, EchoTik adapter, references, and tests. Confirm no runtime files or sensitive values are public.

---

## Final Acceptance Checklist

- [ ] EchoTik is the default registered adapter and retains the established visible report behavior.
- [ ] A synthetic registered non-EchoTik adapter generates the same Top-20 and seven-day trend report contract.
- [ ] Unsupported or capability-incomplete platforms fail before local configuration changes or workbook export.
- [ ] No primary adapter opens more than 20 detail pages.
- [ ] Human-verification failures remain distinct from empty trend data.
- [ ] Amazon remains required and is ordered after the configured primary platform.
- [ ] The hidden detail-link header is `商品详情链接`; the 15 visible columns and visual layout are unchanged.
- [ ] Skill metadata and GitHub public metadata are fully English and professionally describe the verified behavior.
- [ ] Full tests, compilation, Skill validation, synthetic report audit, secret scan, artifact scan, and remote verification pass with fresh evidence.
