---
name: cross-border-ecommerce-daily-report
description: Use when configuring, running, scheduling, troubleshooting, or validating a Windows daily product-intelligence report that uses EchoTik by default or a verified registered platform adapter, with Amazon as a supplementary source.
---

# Cross-Border E-Commerce Daily Report

## Core principle

Produce a local, template-preserving, verified XLSX through a registered product-intelligence platform adapter. EchoTik remains the default primary platform. Amazon remains a required supplementary source.

Keep credentials, cookies, persistent browser profiles, local configuration, generated reports, and failure records outside this Skill directory and outside Git.

## Run the report

1. Read [references/configuration.md](references/configuration.md) before setup, first login, scheduling, troubleshooting, or changing a platform or category.
2. Read [references/report-schema.md](references/report-schema.md) before generating, validating, distributing, or changing workbook behavior.
3. Copy `scripts/config.example.yaml` to a local runtime directory outside the Skill. Use EchoTik unless a different adapter has passed the equivalent-capability gate.
4. Install prerequisites only with user authorization. Never copy credentials or another person's Chrome profile into the Skill.
5. Run one visible manual report from the Skill root:

   ```powershell
   python ".\scripts\run_report.py" --config "$reportConfig"
   ```

6. Let the user sign in manually in the isolated visible Chrome profile. Never request, store, paste, publish, or automate account credentials.
7. Stop when a login challenge, CAPTCHA, or human-verification page appears. Do not bypass it or continue opening product-detail pages. Resume only after the user completes it manually and explicitly requests a retry.
8. Keep `detail_limit: 20` and `trend_days: 7`. Freeze the primary platform's Top 20 identities by descending seven-day GMV before opening any detail page. Open no more than those 20 detail pages.
9. Treat a genuinely empty seven-day trend as `数据为空`. Treat navigation, control, authentication, DOM, or challenge failures as run failures, not empty data.
10. Verify the workbook against [references/report-schema.md](references/report-schema.md). A file existing is not sufficient evidence of success.
11. Register the scheduled task only after a visible manual run and workbook verification pass, and only when the user requests scheduling.

## Change the product category

Use the configured adapter's visible category workflow. For EchoTik, record the complete root-to-leaf path and bind it to the numeric `product_categories` identifier visible in the resulting URL. Confirm a matching Amazon HTTPS category or search page. Edit only the user's local configuration after both confirmations pass.

Never guess, translate, infer, or reuse a category identifier from memory. Never substitute an unverified Amazon URL. Leave the local configuration unchanged until the primary platform and Amazon evidence both pass.

## Replace the primary platform

Naming a website does not make it compatible. A replacement requires a local registered adapter, the normalized record contract, a complete capability declaration, adapter tests, visible category confirmation, exact seven-day GMV and seven-value sales-amount trend support, human-verification detection, and one user-authorized visible manual run.

Use `build_default_registry()` in `scripts/ecommerce_report/platforms.py` as the local registration seam. Follow the non-executable adapter skeleton and acceptance steps in [references/configuration.md](references/configuration.md); never put an import path or adapter implementation in YAML.

Apply the equivalent-capability gate before editing local configuration:

1. Resolve an existing adapter by its closed registry key, or implement and register a dedicated local adapter.
2. Verify category evidence, required normalized fields, Top-20 identity freezing, the 20-detail-page ceiling, exact seven-day trends, and fail-closed challenge handling.
3. Generate a manual report and run the same workbook verification used by EchoTik.
4. Change `primary_platform.adapter` only after every gate passes.

Do not load adapter modules, executable paths, plugins, or remote code from YAML. Do not claim a platform is compatible when its adapter or equivalent evidence is missing. Do not estimate, fabricate, or silently substitute unavailable platform fields.

## Common mistakes

| Mistake | Required response |
|---|---|
| Scheduling before the first verified run | Complete a visible manual run and workbook verification first. |
| Editing `scripts/config.example.yaml` as live configuration | Copy it outside the Skill and edit only the local copy. |
| Naming an unsupported website and changing YAML immediately | Implement and validate a registered adapter before changing local configuration. |
| Guessing a category identifier or Amazon URL | Stop and obtain visible evidence for both sources. |
| Treating any XLSX as success | Verify structure, source order, Top 20, trends, formulas, and sensitive content. |
| Continuing through human verification | Stop detail-page automation and wait for manual completion. |
| Writing into `assets/report-template.xlsx` | Fail verification; always write to a separate output path. |
