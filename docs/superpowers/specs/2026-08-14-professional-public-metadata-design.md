# Pluggable Product-Intelligence Platform and Public Metadata Design

## Objective

Keep EchoTik as the default product-intelligence platform while allowing another user to replace it with a compatible platform adapter without changing the daily report workflow, Top-20 selection model, seven-day trend charts, Amazon supplementary source, failure handling, scheduling, or workbook validation.

All repository-facing content added or revised by this change will be written in English. A Chinese explanation will be provided to the maintainer for review before implementation.

## Product Positioning

The Skill is a configurable Windows workflow for cross-border e-commerce product intelligence. It performs multi-source data acquisition, category-level product discovery, Top-20 GMV ranking, seven-day sales trend analysis, template-preserving XLSX generation, and automated workbook validation.

EchoTik remains the bundled default and reference implementation. Alternative platforms are optional adapters that must satisfy the same capability contract before they can be enabled.

## Design Options Considered

### Configuration-only selectors

Storing URLs and selectors in YAML would be simple, but it would not safely model platform-specific authentication, pagination, category evidence, localized number formats, challenge detection, or chart extraction. This option is rejected.

### Pluggable platform adapters

Each platform implements one stable adapter contract and emits normalized product records. The report pipeline and workbook layer consume only that contract. This is the approved design.

### Unstructured agent-driven scraping

Letting an agent reinterpret every website on each run would maximize breadth but would make unattended daily execution unreliable and difficult to verify. This option is rejected.

## Architecture

### Primary platform adapter contract

Introduce a platform-neutral adapter interface with the following responsibilities:

1. Validate its platform-specific configuration.
2. Open and reuse the configured visible Chrome profile without handling credentials.
3. Detect login challenges, CAPTCHAs, and human-verification pages before collection and before each detail-page visit.
4. Confirm a complete visible category path and bind it to a platform-native category identifier or canonical URL.
5. Collect paginated product-list records.
6. Normalize every record to the shared product schema.
7. Freeze the Top 20 identities by descending seven-day GMV before checking detail links.
8. Open no more than those 20 detail pages.
9. Select and extract exactly seven finite, nonnegative daily sales-amount values for each available trend.
10. Distinguish a genuinely empty trend from navigation, control, DOM, authentication, or challenge failures.

The adapter exposes its stable key and human-readable source label. Configuration selects adapters only from the internal registry; it cannot import arbitrary executable code from a YAML path.

### Normalized product record

Every enabled primary-platform adapter must produce the fields required by the current report contract:

- Source label
- Complete original product title
- Complete Chinese product title
- Category
- Price in USD
- Product rating
- Review count
- Total GMV
- Seven-day GMV
- Seven-day sales volume
- Related video count
- Related creator count
- Product detail URL
- Optional seven-value daily sales-amount trend
- Concise diagnostic state

Missing optional trend data is represented only by the established `数据为空` diagnostic. Missing required list-level fields or platform capabilities fail the run before export.

### EchoTik adapter

Refactor the existing EchoTik collection and trend logic behind the new adapter interface without changing its visible workflow or selectors. Register it under the stable key `echotik` and use it when the local configuration omits an explicit primary platform.

The packaged example keeps the existing EchoTik pet-category paths and IDs. Existing EchoTik users must receive the same visible report layout and the same Top-20 behavior after the refactor.

### Adapter registry and configuration

Replace the EchoTik-only primary-source configuration with a platform-neutral primary-platform block. The default configuration resolves to EchoTik and preserves the current category values.

Each registered adapter owns validation of its category and platform options. Unknown adapter keys, missing required capabilities, invalid categories, and arbitrary module paths fail closed during configuration loading.

Amazon remains a separate supplementary source with its existing validated HTTPS category URLs and complete-title Chinese translation behavior.

### Pipeline orchestration

The pipeline resolves the configured primary adapter from the registry, opens one isolated visible Chrome context, collects the primary records, then collects Amazon records. A required source returning no products remains a failed run.

Operator-facing stages use the selected platform display name instead of hard-coded EchoTik stage names. Browser shutdown, sanitized failure reporting, retry behavior, and output isolation remain unchanged.

### Workbook generation and verification

Keep the 15 visible columns, template layout, widths, heights, colors, chart placement, hidden trend helpers, freeze pane, and filter range unchanged.

Make these internal rules platform-neutral:

- Rank only the configured primary-platform records as `Top 1` through `Top 20`.
- Sort those records by descending seven-day GMV.
- Require one valid seven-day chart or `数据为空` for every Top row.
- Order sources as inventory, configured primary platform, then Amazon.
- Store the actual adapter display name in the visible source column.
- Rename the hidden `EchoTik详情链接` header to the platform-neutral `商品详情链接` while preserving its hidden state and hyperlink behavior.

The default EchoTik report must remain visually identical because the renamed column is hidden.

## Equivalent-Capability Gate

An alternative platform can be enabled only when its adapter proves all required capabilities through tests and one user-authorized visible manual run. The gate verifies:

- Category evidence is visible and repeatable.
- Required list-level fields are available and correctly normalized.
- The platform exposes seven-day GMV and seven individual daily sales-amount values.
- Top-20 identity selection and the 20-detail-page ceiling are enforced.
- Human-verification pages stop all detail-page automation.
- The generated workbook passes the same structural, chart, sorting, formula, translation, and sensitive-content checks as the EchoTik default.

If the platform does not expose an equivalent field or trend, the adapter is not declared fully compatible. The Skill reports the missing capability and leaves the existing configuration unchanged. It never estimates, fabricates, or silently substitutes data.

## Natural-Language Platform Replacement Workflow

When a user names a replacement platform and category:

1. Check whether a registered adapter already exists.
2. If it exists, visibly confirm the target platform, session, complete category path, identifier, required fields, and seven-day sales-amount trend.
3. If it does not exist, create a dedicated adapter module and tests without modifying the workbook core for platform-specific selectors.
4. Run the equivalent-capability gate.
5. Edit only the user's local configuration after all evidence passes.
6. Run and verify one manual report before scheduling.

Changing a platform is an implementation task, not a free-form runtime instruction. The Agent must not claim that an unsupported site is compatible before its adapter and verification evidence exist.

## Public Metadata

Use the following GitHub description:

> Configurable Codex Skill for cross-border e-commerce product intelligence, using EchoTik by default and validated platform adapters to generate daily Top-20 GMV and seven-day trend XLSX reports.

Use these repository topics:

- `codex-skill`
- `cross-border-ecommerce`
- `product-intelligence`
- `ecommerce-analytics`
- `product-research`
- `echotik`
- `amazon`
- `playwright`
- `xlsx-reporting`
- `windows-automation`

Revise `SKILL.md` and `agents/openai.yaml` to use fully English, platform-aware product-intelligence terminology. Keep `SKILL.md` as the canonical Skill entry point and do not add a `README.md`.

## Security and Safety Constraints

- Credentials, cookies, browser profiles, local configuration, generated reports, and failure records remain outside the Skill directory.
- Adapters do not request, store, publish, or automate account credentials.
- CAPTCHAs and human-verification challenges require manual completion and explicit user instruction before retrying.
- Configuration cannot load arbitrary executable files or remote code.
- Collected strings remain protected against XLSX formula injection.
- Reports and all XLSX ZIP parts remain subject to sensitive-content scanning.

## Files Expected to Change During Implementation

- `SKILL.md`
- `agents/openai.yaml`
- `scripts/config.example.yaml`
- `scripts/ecommerce_report/config.py`
- `scripts/ecommerce_report/pipeline.py`
- `scripts/ecommerce_report/echotik.py`
- `scripts/ecommerce_report/trends.py`
- `scripts/ecommerce_report/workbook.py`
- New platform-neutral adapter and normalized-model modules under `scripts/ecommerce_report/`
- Relevant references and tests
- `assets/report-template.xlsx` only for the hidden detail-link header migration
- GitHub description and topics

Amazon scraping logic is out of scope except for integration with the platform-neutral pipeline. Scheduled-task timing, output naming, dependency installation, repository permissions, visibility, releases, packages, and GitHub Actions remain out of scope.

## Validation Strategy

Implementation uses regression-first tests and includes:

1. A default EchoTik compatibility test proving unchanged visible report output and Top-20 behavior.
2. A synthetic non-EchoTik adapter test proving registry selection, source labeling, Top-20 ranking, trend charts, and Amazon ordering.
3. Negative tests for unknown adapters, arbitrary module paths, missing capabilities, invalid categories, empty required sources, challenge pages, more than 20 detail visits, invalid trends, and unsupported platform fields.
4. Workbook tests for the generic hidden link header, chart-row identity, source order, formula safety, template dimensions, translations, and sensitive-content scanning.
5. Full automated tests, Skill quick validation, UTF-8 YAML parsing, compilation, diff checks, tracked-file secret scanning, forbidden-artifact scanning, and a synthetic report audit.
6. A user-authorized visible EchoTik manual run before claiming live-site compatibility.

## Rollback

- Revert the implementation commits to restore the EchoTik-only pipeline and original hidden header.
- Restore the prior sanitized template asset.
- Restore the prior GitHub description and remove any newly added topics.
- Preserve local configuration and runtime data; migration must never overwrite them in place without an explicit backup and user authorization.

## Acceptance Criteria

- EchoTik remains the default adapter and produces the established visible report format.
- A synthetic non-EchoTik adapter produces the same report capabilities without workbook-core platform branching.
- Unsupported platforms fail the equivalent-capability gate with a concise missing-capability explanation.
- No run opens more than 20 primary-platform detail pages.
- Amazon remains the supplementary source and follows the primary-platform group.
- The hidden detail-link field is platform-neutral while the visible workbook layout remains unchanged.
- Public metadata is fully English and accurately describes default EchoTik plus validated adapter extensibility.
- All validation checks pass with fresh evidence before push.
