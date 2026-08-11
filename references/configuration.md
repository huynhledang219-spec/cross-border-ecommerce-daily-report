# Configuration

## New Windows computer

Use Windows PowerShell, Python 3.12 or newer, and Google Chrome. The packaged code directly imports only the libraries in `scripts/requirements.txt`.

With user authorization, run these commands from the Skill root:

```powershell
python --version
python -m pip install -r ".\scripts\requirements.txt"
python -m playwright install chrome
```

These commands install software; do not run them merely to inspect or verify the Skill.

Create the local runtime outside the Skill directory:

```powershell
$reportRuntime = Join-Path $env:LOCALAPPDATA "CrossBorderEcommerceDailyReport"
New-Item -ItemType Directory -Force -Path $reportRuntime | Out-Null
$reportConfig = Join-Path $reportRuntime "config.yaml"
Copy-Item -LiteralPath ".\scripts\config.example.yaml" -Destination $reportConfig
```

In the local copy, set `output_dir` and `profile_dir` to locations under `$reportRuntime`, and set `template_path` to the absolute path of the packaged, sanitized `assets/report-template.xlsx`. Use forward slashes in absolute YAML paths on Windows. Keep `detail_limit: 20`, `trend_days: 7`, and the default pet-category mappings.

Account credentials, cookies, and the persistent Chrome profile are local runtime state. Never copy, publish, commit, or bundle them with the Skill. Never reuse the maintainer's profile.

## First manual login and run

From the Skill root, run:

```powershell
python ".\scripts\run_report.py" --config "$reportConfig"
```

Chrome opens visibly with the configured persistent profile. Let the user enter EchoTik credentials manually. Do not request, record, paste, or automate credentials. If the first run proceeds before login is complete and fails, finish the login, then rerun the same command; the local profile retains the session.

If EchoTik or Amazon displays a CAPTCHA, login challenge, or human-verification page, stop. Do not bypass it and do not continue to other product-detail pages. Resume only after the user completes it manually in the visible browser and explicitly requests a retry.

For an idempotent daily run after the manual run passes:

```powershell
python ".\scripts\run_daily.py" --config "$reportConfig"
```

The daily entry point reuses an existing report for the same date, permits retry after failure, and writes a concise sanitized failure record under `数据报表_失败原因`.

Register the 09:00 Windows scheduled task only when requested and only after the manual run and workbook verification pass:

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\install_scheduled_task.ps1" -ConfigPath "$reportConfig"
```

## Category configuration

The bundled example defaults to two matching pet segments:

- EchoTik: `宠物用品 > 猫狗配件 > 猫狗清洁美容` (`816392`) and `宠物用品 > 猫狗配件 > 猫狗服饰` (`813960`).
- Amazon: Pet Grooming Supplies and Pet Clothing & Accessories over HTTPS.

When the user asks for a different product category, they only need to provide its natural-language name. The Agent must do the discovery:

1. Open `https://echotik.live/products` in a visible Chrome window with the user's local session.
2. Navigate the complete visible menu hierarchy. Record the exact labels in root-to-leaf order.
3. Click the leaf and confirm the visible selected category matches the requested product type.
4. Read the numeric `product_categories` value from the resulting page URL and bind it to that exact full path. If the page does not prove both path and ID, stop without editing.
5. Open Amazon visibly. Choose an HTTPS Amazon category/search URL and confirm the displayed title/results represent the same requested product type. If the match is ambiguous, stop without editing.
6. Edit only the local `config.yaml`, replacing both lists as a coherent pair. Each `echotik_categories` entry contains the exact root-to-leaf `path` list and quoted numeric `id`; each `amazon_categories` entry contains the matching `name` and confirmed HTTPS `url`. Preserve this existing YAML shape and replace only values proven by the visible pages.

7. Load the local config before scraping to check its constraints:

   ```powershell
   python -c "from pathlib import Path; from scripts.ecommerce_report.config import RuntimeConfig; RuntimeConfig.load(Path(r'$reportConfig')); print('configuration valid')"
   ```

Do not guess an ID, copy one from a similar category, derive it from a label, or skip the matching Amazon confirmation. Deadline, authority, or convenience never replaces visible evidence. Leave the pet defaults and local config unchanged until every confirmation succeeds.

## Failure handling

- Configuration rejects limits other than exactly 20 details and 7 trend days, empty category lists, nonnumeric EchoTik IDs, and non-HTTPS Amazon URLs.
- Summarize a run failure as: `stage — concise sanitized reason — failure record path`.
- Treat a missing or unreadable failure record as an additional verification failure; do not invent a reason.
- Keep full tracebacks in private debugging output only when the user explicitly asks and after redacting secrets and local profile paths.
