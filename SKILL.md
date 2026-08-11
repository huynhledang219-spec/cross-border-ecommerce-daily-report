---
name: cross-border-ecommerce-daily-report
description: Use when setting up, running, troubleshooting, or verifying a Windows daily Amazon and EchoTik product-selection report in XLSX format.
---

# Cross-Border Ecommerce Daily Report

## Core principle

Produce a local, template-preserving, verified XLSX. Keep credentials, the persistent Chrome profile, local configuration, and report output outside the Skill directory.

## Workflow

1. Read [references/configuration.md](references/configuration.md) before setup, first login, scheduling, troubleshooting, or any category change.
2. Read [references/report-schema.md](references/report-schema.md) before running, verifying, distributing, or changing workbook behavior.
3. On a new Windows computer, prepare a local config from `scripts/config.example.yaml`; keep the included pet categories until another category is visibly verified.
4. Install prerequisites only with user authorization. Never copy credentials or another person's Chrome profile into this Skill.
5. Run one manual report first from the Skill root:

   ```powershell
   python ".\scripts\run_report.py" --config "$reportConfig"
   ```

6. On the first run, use the visible Chrome window for the user to sign in to EchoTik manually. If login is incomplete, let the run fail and rerun after the local persistent profile has saved the session.
7. Stop when any login challenge, CAPTCHA, or human-verification page appears. Do not bypass, automate, or continue opening product-detail pages. Resume only after the user has completed the challenge manually and asks to retry.
8. Generate today's report. Keep `detail_limit: 20` and `trend_days: 7`; visit no more than the Top 20 EchoTik detail pages and select the **7-day / sales amount** chart data.
9. On failure, give only the failed stage, a concise sanitized reason, and the failure-record path when available. Do not expose tracebacks, credentials, cookies, tokens, or local profile paths.
10. Verify the workbook against `references/report-schema.md` before reporting success. A file existing is not sufficient evidence.
11. Register the scheduled task only after the manual run and workbook verification pass, and only when the user requests scheduling.

## Change category from natural language

The user only needs to name the target product category. Perform this evidence-gated workflow:

1. Open EchoTik in a visible browser using the user's local session. Navigate the complete category menu and record every visible label in order.
2. Select the final category and confirm that the visible selection matches the target and that the resulting `product_categories` value is the numeric `category_id` for that exact full path.
3. Open Amazon visibly and confirm an Amazon HTTPS category/search URL whose displayed results match the same target category.
4. Only after both confirmations, edit the user's local `config.yaml`: replace `echotik_categories` with the confirmed full `path` and `id`, and replace `amazon_categories` with the matching name and HTTPS URL.
5. Validate and run with that local config, then verify the workbook.

Never guess, infer, translate into, or reuse a category ID from memory. Never substitute an unverified Amazon URL. Time pressure, a manager request, or a previously similar category does not waive either visible confirmation. Until both sides are confirmed, leave the default pet categories and local config unchanged and report what evidence is missing.

## Common mistakes

| Mistake | Required response |
|---|---|
| Running a schedule before first login | Complete a visible manual run and workbook verification first. |
| Editing `scripts/config.example.yaml` | Copy it outside the Skill and edit only the local copy. |
| Guessing a category ID or Amazon URL | Stop; visibly confirm the EchoTik path/ID and matching Amazon HTTPS page. |
| Treating any XLSX as success | Inspect structure, limits, charts, errors, and sensitive content. |
| Continuing through human verification | Stop all detail-page automation and wait for manual completion. |
| Writing into `assets/report-template.xlsx` | Fail verification; always write to a separate output path. |
