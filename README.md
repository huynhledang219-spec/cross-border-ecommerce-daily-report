# Cross-Border E-Commerce Daily Report

A configurable Codex Skill for producing daily cross-border e-commerce product-intelligence workbooks on Windows. It collects a verified primary product platform together with Amazon, ranks the primary platform's strongest products, adds seven-day sales-amount trends, preserves a controlled XLSX layout, and rejects incomplete or unsafe output before publication.

EchoTik is the bundled default primary platform. Amazon remains a required supplementary source.

## What it does

The Skill turns visible, category-scoped product research into a local Excel workbook that can be reviewed, compared, and archived each day. It keeps collection, enrichment, workbook generation, and verification behind explicit gates so that a file is not treated as successful merely because it exists.

The generated report is based on the sanitized template in [`assets/report-template.xlsx`](assets/report-template.xlsx). Runtime configuration, browser state, reports, and failure records stay outside the repository.

## Key capabilities

- Confirms the selected product category through a visible browser workflow.
- Uses EchoTik by default through a closed, registered primary-platform adapter.
- Requires a matching Amazon category or search source as supplementary market evidence.
- Ranks the primary platform's Top 20 products by descending seven-day GMV.
- Freezes Top 20 identities before detail enrichment and opens no more than 20 product-detail pages.
- Reads exactly seven daily sales-amount values for each available seven-day trend.
- Keeps complete original Amazon titles and produces complete Chinese translations for the report.
- Preserves the approved workbook headers, column order, widths, row styles, hidden helper columns, filters, freeze pane, and chart dimensions.
- Writes concise, sanitized failure records without creating routine success logs.
- Supports an idempotent daily run and optional 09:00 Windows Task Scheduler registration.
- Validates report structure, formulas, source order, hyperlinks, charts, translations, and sensitive-content boundaries before replacing an existing output file.

## Workflow

```text
local configuration
  -> visible sign-in
  -> visible category confirmation
  -> primary-platform and Amazon collection
  -> Top 20 identity freeze and detail enrichment
  -> template-preserving XLSX generation
  -> independent workbook verification
```

Codex does not keep working after a task ends. Daily execution is provided by the local Python entry point and, when explicitly installed, Windows Task Scheduler.

## Requirements

- Windows 10 or Windows 11.
- Python 3.12 or newer.
- Google Chrome.
- A Codex installation that can load local Skills.
- Authorized access to EchoTik, or to a separately implemented and accepted primary-platform adapter.
- Access to the configured Amazon pages.
- User authorization before installing dependencies, registering a scheduled task, or starting a visible browser run.

## Installation

Choose a Codex home directory, clone the Skill, and enter its root:

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillRoot = Join-Path $codexHome "skills/cross-border-ecommerce-daily-report"
git clone https://github.com/huynhledang219-spec/cross-border-ecommerce-daily-report.git $skillRoot
Set-Location $skillRoot
```

Inspect the repository before installing anything. With user authorization, install only the declared Python dependencies and the Playwright Chrome channel:

```powershell
python --version
python -m pip install -r ".\scripts\requirements.txt"
python -m playwright install chrome
```

These commands install software. They are not required for read-only inspection of the Skill.

## Quick start

### 1. Create a local runtime directory

Keep the live configuration and all generated state outside the Skill directory:

```powershell
$reportRuntime = Join-Path $env:LOCALAPPDATA "CrossBorderEcommerceDailyReport"
New-Item -ItemType Directory -Force -Path $reportRuntime | Out-Null
$reportConfig = Join-Path $reportRuntime "config.yaml"
Copy-Item -LiteralPath ".\scripts\config.example.yaml" -Destination $reportConfig
```

### 2. Configure local paths and categories

Edit only the copied `$reportConfig` file. Set:

- `output_dir` and `profile_dir` to directories under `$reportRuntime`.
- `template_path` to the absolute path of the packaged `assets/report-template.xlsx`.
- `primary_platform.categories` to categories proven in the visible primary-platform interface.
- `amazon_categories` to matching Amazon HTTPS category or search pages.
- `detail_limit` to `20` and `trend_days` to `7`.

Use forward slashes for absolute Windows paths in YAML. Do not place passwords, cookies, tokens, adapter module paths, or executable code in the configuration.

See [Configuration](references/configuration.md) for the complete configuration contract.

### 3. Perform the first visible run

From the Skill root, run:

```powershell
python .\scripts\run_report.py --config "$reportConfig"
```

Chrome opens visibly with an isolated persistent profile. The user signs in manually. The Skill must not request, record, paste, store, or automate account credentials.

If a CAPTCHA, login challenge, or human verification page appears, stop the run. Do not bypass the challenge and do not continue opening detail pages. Resume only after the user completes the challenge manually and explicitly requests a retry.

### 4. Verify the generated workbook

Set `$reportOutput` to the generated XLSX path and run the read-only verifier:

```powershell
$reportOutput = Read-Host "Enter the full path to the generated XLSX"
python -c "from pathlib import Path; from scripts.ecommerce_report.workbook import verify_report; print(verify_report(Path(r'$reportOutput')))"
```

Use the actual generated filename. Treat the report as complete only when `verify_report` returns an inspection without raising an error.

## Category configuration

Category identifiers are evidence, not guesses.

For EchoTik:

1. Open the product library in visible Chrome using the local profile.
2. Navigate the complete root-to-leaf category hierarchy.
3. Confirm that the visible leaf represents the requested product type.
4. Record the numeric category identifier exposed by the selected page and bind it to that exact path.
5. Confirm an Amazon HTTPS category or search page whose visible results represent the same product type.
6. Update both source lists together in the local configuration.
7. Load and validate the local configuration before collecting data.

Never infer an identifier from a translated label, reuse an identifier from a similar category, or substitute an unverified Amazon URL. Leave the working local configuration unchanged until both sources have visible evidence.

Detailed steps are in [Configuration](references/configuration.md).

## Daily scheduling

After one visible manual run and workbook verification pass, use the idempotent daily entry point:

```powershell
python .\scripts\run_daily.py --config "$reportConfig"
```

The daily command reuses a completed report for the same date, allows a failed day to be retried, and writes a concise sanitized failure record when the run fails.

Register the 09:00 Windows task only when the user requests scheduling:

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\install_scheduled_task.ps1" -ConfigPath "$reportConfig"
```

The task is designed to wake the computer, run as soon as possible after a missed start, and reuse the isolated visible Chrome profile. A sleeping computer can be awakened; a powered-off computer cannot run the task.

## Workbook contract

The workbook contains 15 public columns covering rank, focus status, source, complete original title, complete Chinese title, price, rating, reviews, total GMV, seven-day GMV, seven-day sales, related videos, related creators, product-detail link, and diagnostic state.

The report contract requires:

- Source groups ordered as inventory, configured primary platform, then Amazon.
- Unique and contiguous Top labels ordered by descending seven-day GMV.
- No more than 20 Top rows and no more than 20 primary-platform detail visits.
- One visible trend chart for every Top row with a valid seven-value trend.
- A data-empty diagnostic and no chart only when the selected product genuinely has no trend data.
- Hidden product links and seven hidden trend-helper columns.
- The approved `A2` freeze pane, public filter range, row banding, dimensions, and chart extents.
- No unexpected formulas, formula-like web values, unsafe links, credentials, account identifiers, local profile paths, or sample business data.
- Complete Amazon original titles and complete Chinese translations.

Navigation, authentication, control, DOM, challenge, and malformed-trend failures are operational failures. They must never be converted into an empty-data result.

See [Report schema and verification](references/report-schema.md) for the authoritative field and verification rules.

## Replacing EchoTik

Naming another website in YAML does not make it compatible. The YAML file can select only a closed adapter key already registered in local code.

A replacement primary platform requires:

1. A dedicated local adapter with a stable key and display name.
2. Complete `PlatformCapabilities` for visible category confirmation, seven-day GMV, exact daily sales-amount trends, and human-verification detection.
3. Fail-closed configuration validation for category and option fields.
4. Normalized records matching the public report schema.
5. Top 20 identity freezing before detail visits and the same 20-page ceiling.
6. Tests for registry resolution, configuration, normalized fields, challenge handling, trends, pipeline behavior, and workbook integration.
7. The equivalent-capability gate and one user-authorized visible manual acceptance run.
8. Explicit registration in `build_default_registry()` only after the adapter passes every gate.

Amazon is not a replacement primary platform. It remains the required supplementary source regardless of which accepted primary adapter is selected.

The registration seam and acceptance sequence are documented in [Configuration](references/configuration.md). The normalized interface is documented in [Report schema and verification](references/report-schema.md).

## Security and privacy

- Keep credentials, cookies, browser profiles, local configuration, generated reports, and failure records outside this repository and outside Git.
- Never publish another person's browser profile or session state.
- Never put passwords, tokens, executable paths, adapter imports, plugins, or remote code in YAML.
- Let users enter credentials manually in the visible isolated Chrome profile.
- Stop on CAPTCHA or human verification; do not attempt bypasses or evasive automation.
- Store only concise sanitized failure reasons in the configured failure directory.
- Keep detailed traces private and redact accounts, secrets, URLs with sensitive query values, and local profile paths before sharing.
- Write reports to a separate local output path. Never overwrite the packaged template.

## Troubleshooting

| Symptom | Required response |
|---|---|
| The platform opens signed out | Complete sign-in manually in the visible isolated Chrome profile, close no required state, and rerun. |
| A CAPTCHA or verification challenge appears | Stop collection, complete it manually, then retry only after explicit user direction. |
| A selected Top product has no seven-day bars | Record the data-empty diagnostic for that product and continue with the remaining frozen Top identities. |
| Trend controls, chart DOM, navigation, or authentication fail | Fail the run; do not label the product as empty data. |
| The primary platform or Amazon returns no required rows | Fail before workbook export and report the exact collection stage. |
| The workbook verifier raises an error | Keep the previous report, correct the failed gate, and regenerate. Do not distribute the rejected workbook. |
| A scheduled run is missed while the computer sleeps | Windows runs the task as soon as possible after wake if the task was installed with the provided script. |
| The computer was powered off | Start the computer and run the daily entry point; a powered-off computer cannot be awakened by the task. |

## Known limitations

- The verified runtime is Windows with Python 3.12 or newer and Google Chrome.
- EchoTik is the only bundled primary-platform adapter.
- Another platform requires implementation, tests, equivalent evidence, and visible manual acceptance; changing YAML alone is insufficient.
- Amazon remains mandatory as the supplementary source.
- Platform user interfaces and selectors can change and may require a tested adapter update.
- Initial sign-in and every CAPTCHA or human-verification event require manual user action.
- The verified contract fixes detail enrichment at 20 products and the trend window at seven days.
- Third-party membership, availability, permissions, data coverage, rate limits, and terms remain outside this repository's control.
- No live-site success is implied by unit tests or synthetic workbook verification.

## Repository structure

| Path | Responsibility |
|---|---|
| [`SKILL.md`](SKILL.md) | Core instructions and operational safety rules loaded by Codex. |
| [`agents/`](agents) | Codex-facing display metadata. |
| [`assets/`](assets) | Sanitized workbook template used to generate reports. |
| [`references/`](references) | Detailed configuration and workbook contracts. |
| [`scripts/`](scripts) | Entry points, collectors, adapters, scheduling, and report verification code. |
| [`tests/`](tests) | Configuration, collection, adapter, pipeline, workbook, and public-asset regression tests. |

## Testing

Run the complete regression suite from the Skill root:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q scripts tests
```

Validate the Skill package using a portable Codex home lookup:

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
python (Join-Path $codexHome "skills/.system/skill-creator/scripts/quick_validate.py") "."
```

Tests do not replace one user-authorized visible manual run when a platform, category, selector, authentication boundary, or adapter changes.

## Contributing

Keep changes narrow, test-first, and evidence-backed.

- Add or update regression tests before changing behavior.
- Preserve the 20-detail-page ceiling, seven-day trend contract, workbook layout, and fail-closed challenge handling.
- Do not commit live configuration, credentials, cookies, profiles, reports, failure records, or private absolute paths.
- Require an equivalent-capability gate and visible manual acceptance evidence for every new primary-platform adapter.
- Run the full test suite, compilation check, Skill validator, and public-safety checks before proposing a change.

## License

Released under the [MIT License](LICENSE).
