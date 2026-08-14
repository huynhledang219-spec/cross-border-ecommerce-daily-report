# Configuration

## Local runtime on Windows

Use Windows PowerShell, Python 3.12 or newer, and Google Chrome. The packaged code directly imports only the libraries in `scripts/requirements.txt`.

With user authorization, run these commands from the Skill root:

```powershell
python --version
python -m pip install -r ".\scripts\requirements.txt"
python -m playwright install chrome
```

These commands install software. Do not run them merely to inspect or validate the Skill.

Create the runtime outside the Skill directory:

```powershell
$reportRuntime = Join-Path $env:LOCALAPPDATA "CrossBorderEcommerceDailyReport"
New-Item -ItemType Directory -Force -Path $reportRuntime | Out-Null
$reportConfig = Join-Path $reportRuntime "config.yaml"
Copy-Item -LiteralPath ".\scripts\config.example.yaml" -Destination $reportConfig
```

In the local copy, set `output_dir` and `profile_dir` under `$reportRuntime`. Set `template_path` to the absolute path of the packaged, sanitized `assets/report-template.xlsx`. Use forward slashes in absolute YAML paths on Windows. Keep `detail_limit: 20` and `trend_days: 7`.

Local configuration, credentials, cookies, persistent browser profiles, generated reports, and failure records must remain outside the Skill directory and outside Git. Never copy or publish another person's profile.

## Primary platform selection

`primary_platform.adapter` is a closed adapter key resolved from the internal registry. Configuration never imports an executable path or remote code. The bundled registry currently provides `echotik`, which remains the default when the adapter is omitted.

```yaml
primary_platform:
  adapter: echotik
  categories:
    - path: ["宠物用品", "猫狗配件", "猫狗清洁美容"]
      id: "816392"
  options: {}
```

Each registered adapter owns the schema and validation of `categories` and `options`. Unknown keys, unsupported options, missing capabilities, invalid categories, and arbitrary module paths fail closed before browser collection or workbook export.

Amazon is not a replacement adapter. It remains a required supplementary source configured through `amazon_categories`, and every category URL must use HTTPS.

## First visible login and manual run

Run from the Skill root:

```powershell
python ".\scripts\run_report.py" --config "$reportConfig"
```

Chrome opens visibly with the configured persistent profile. Let the user enter platform credentials manually. Do not request, record, paste, store, or automate credentials. If the first run starts before sign-in is complete, finish sign-in manually and rerun the same command; the local profile retains the session.

Human verification is a hard stop. If the primary platform or Amazon displays a CAPTCHA, login challenge, or human-verification page, do not bypass it and do not continue to another product-detail page. Resume only after the user completes it manually and explicitly requests a retry.

After the manual run passes, use the idempotent daily entry point:

```powershell
python ".\scripts\run_daily.py" --config "$reportConfig"
```

The daily entry point reuses an existing report for the same date, permits retry after failure, and writes a concise sanitized failure record to the configured failure location.

Register the 09:00 Windows scheduled task only when requested and only after the manual run and workbook verification pass:

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\install_scheduled_task.ps1" -ConfigPath "$reportConfig"
```

## Change an EchoTik category

The bundled example contains two pet segments:

- `宠物用品 > 猫狗配件 > 猫狗清洁美容` (`816392`)
- `宠物用品 > 猫狗配件 > 猫狗服饰` (`813960`)

To configure another EchoTik category:

1. Open `https://echotik.live/products` in visible Chrome with the user's local session.
2. Navigate the complete category hierarchy and record the exact root-to-leaf labels.
3. Select the leaf and confirm that the visible selection matches the requested product type.
4. Read the numeric `product_categories` value from the resulting URL and bind it to that exact path. Stop without editing if the page does not prove both values.
5. Open Amazon visibly and confirm an HTTPS category or search page whose displayed results represent the same product type.
6. Edit only the local `config.yaml`, replacing the primary-platform and Amazon category lists as a coherent pair.
7. Load the local configuration before scraping:

   ```powershell
   python -c "from pathlib import Path; from scripts.ecommerce_report.config import RuntimeConfig; RuntimeConfig.load(Path(r'$reportConfig')); print('configuration valid')"
   ```

Never guess an identifier, copy one from a similar category, derive it from a translated label, or skip Amazon confirmation. Leave the existing local configuration unchanged until every visible confirmation succeeds.

## Register a replacement platform

Naming a website does not make it compatible. Treat platform replacement as an implementation and validation task:

1. Check the internal registry for a local registered adapter.
2. If none exists, implement a dedicated adapter that produces the normalized record contract in [report-schema.md](report-schema.md). Keep platform-specific selectors, authentication-state checks, pagination, category evidence, number parsing, detail navigation, and trend extraction inside that adapter.
3. Declare and test all required capabilities: visible category confirmation, seven-day GMV, exact daily sales-amount trends, and human-verification detection.
4. Prove that Top-20 identities are frozen before detail visits and that no more than 20 detail pages open.
5. Run the equivalent-capability gate with unit tests and one user-authorized visible manual run.
6. Generate and verify a report using the same workbook contract as EchoTik.
7. Change only the local `primary_platform.adapter`, categories, and options after every gate passes.

Do not estimate missing fields, substitute a different trend, treat challenge pages as empty data, or claim compatibility without the registered adapter and evidence.

## Failure handling

- Reject limits other than exactly 20 detail pages and 7 trend days.
- Reject an empty required source, an unknown adapter, incomplete capabilities, invalid platform categories, and non-HTTPS Amazon URLs.
- Summarize a run failure as `stage — concise sanitized reason — failure record path`.
- Treat a missing or unreadable failure record as an additional verification failure; do not invent a reason.
- Keep detailed traces private and redact secrets and local profile paths before sharing them.
