# Product-Focused README Streamlining Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the long technical README with a polished 100-to-140-line product homepage that retains one complete collapsed Windows quick start and links to authoritative technical documentation.

**Architecture:** Change only the README presentation contract and its focused public-asset regression test. First make the new concise-page contract fail against the existing README, then replace the page in one cohesive rewrite, preview it, run all checks, and push the already-authorized local `main` only after verification succeeds.

**Tech Stack:** GitHub-flavored Markdown, HTML `<div>` and `<details>` elements supported by GitHub, Python `unittest`, Git.

## Global Constraints

- Keep `README.md` fully English, portable, and approximately 100 to 140 lines.
- Keep `assets/readme/report-showcase.png` near the top; do not embed `assets/readme/social-preview.png` in the README.
- Use exactly one fenced PowerShell block, inside one `<details>` block titled `Minimal Windows setup`.
- Preserve the minimum clone, dependency, external configuration, manual run, and workbook-verification path.
- Preserve EchoTik-default, Amazon-supplementary, Top 20, seven-day trend, visible sign-in, human-verification, external runtime-state, registered-adapter, and verified-XLSX facts.
- Link to `SKILL.md`, `references/configuration.md`, `references/report-schema.md`, and `LICENSE`.
- Do not modify or delete runtime code, tests unrelated to README expectations, Skill instructions, references, templates, images, plans, or specifications.
- Do not change GitHub settings or upload the social preview in this task.
- Push only after the focused test, full test suite, compile check, Skill validator, Markdown link checks, private-path scan, and visual preview pass.

---

## File Map

- Modify: `tests/test_public_asset.py` — replace the long-form README expectations with the product-page contract.
- Replace content: `README.md` — concise product-focused repository homepage.
- Use without modifying: `assets/readme/report-showcase.png`, `SKILL.md`, `references/configuration.md`, `references/report-schema.md`, and `LICENSE`.

## Task 1: Define the Concise Product README Contract

**Files:**
- Modify: `tests/test_public_asset.py`
- Test: `tests/test_public_asset.py`

**Interfaces:**
- Consumes: `README.md` and existing `PRIVATE_ABSOLUTE_PATH_PATTERNS`.
- Produces: one focused test that enforces hierarchy, compactness, minimal code, required claims, documentation links, and removal of long-form sections.

- [ ] **Step 1: Replace the existing README contract test**

Keep the method name `test_public_readme_is_complete_english_and_portable`, the English-only assertion, private-path assertion, and relative-link resolution loop. Replace its long-form heading and command assertions with:

```python
        lines = readme.splitlines()
        self.assertGreaterEqual(len(lines), 100)
        self.assertLessEqual(len(lines), 140)
        self.assertIn('<div align="center">', readme)
        self.assertIn("Minimal Windows setup", readme)
        self.assertEqual(readme.count("<details>"), 1)
        self.assertEqual(readme.count("</details>"), 1)
        self.assertEqual(readme.count("```powershell"), 1)

        required_headings = (
            "# Cross-Border E-Commerce Daily Report",
            "## Why this Skill",
            "## How it works",
            "## Quick start",
            "## Configuration and platform support",
            "## Report guarantees",
            "## Safety and limitations",
            "## Documentation",
            "## Contributing",
            "## License",
        )
        for heading in required_headings:
            self.assertIn(heading, readme)

        required_contract_text = (
            "EchoTik is the bundled default primary platform",
            "Amazon remains the required supplementary source",
            "Top 20",
            "seven-day GMV",
            "exactly seven daily sales-amount values",
            "registered adapter",
            "human-verification",
            "outside the repository",
            "verify_report",
            "assets/readme/report-showcase.png",
            "references/configuration.md",
            "references/report-schema.md",
        )
        for required_text in required_contract_text:
            self.assertIn(required_text, readme)

        removed_headings = (
            "## Requirements",
            "## Installation",
            "## Category configuration",
            "## Daily scheduling",
            "## Workbook contract",
            "## Replacing EchoTik",
            "## Troubleshooting",
            "## Known limitations",
            "## Repository structure",
            "## Testing",
        )
        for heading in removed_headings:
            self.assertNotIn(heading, readme)

        self.assertNotIn("python -m unittest discover", readme)
        self.assertNotIn("quick_validate.py", readme)
        self.assertNotIn("install_scheduled_task.ps1", readme)
```

Retain the existing relative-target extraction and existence assertions after these checks.

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_public_readme_is_complete_english_and_portable -v
```

Expected: `FAIL` because the existing README is longer than 140 lines, lacks the new headings and centered hero, contains multiple PowerShell blocks, and still exposes the removed technical sections.

- [ ] **Step 3: Commit the failing contract**

```powershell
git add -- tests/test_public_asset.py
git commit -m "test: define concise README contract"
```

## Task 2: Rewrite and Preview the Product-Focused README

**Files:**
- Replace content: `README.md`
- Test: `tests/test_public_asset.py`

**Interfaces:**
- Consumes: the exact facts and links in the approved design specification.
- Produces: one 100-to-140-line GitHub homepage with one collapsed setup code block and no duplicated implementation documentation.

- [ ] **Step 1: Replace the hero and introduction**

Start with this structure:

```markdown
<div align="center">

# Cross-Border E-Commerce Daily Report

**A configurable Codex Skill for verified daily product-intelligence workbooks from EchoTik and Amazon.**

![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-Verified-2E7D4F)
[![MIT License](https://img.shields.io/badge/License-MIT-F3C557.svg)](LICENSE)

</div>

EchoTik is the bundled default primary platform. Amazon remains the required supplementary source.

![Sanitized cross-border e-commerce daily report showcase](assets/readme/report-showcase.png)

*Sanitized demonstration data. No live account, product, or sales records are included.*
```

- [ ] **Step 2: Add the concise product sections**

Use the approved headings in order. `Why this Skill` contains exactly six bullets covering visible category verification, Top 20 ranking, exact seven-day trends, complete Amazon title translation, template-preserving XLSX output, and sanitized failure handling.

Use one single-line flow in `How it works`:

```markdown
**Configure and confirm** → **Collect both sources** → **Rank and enrich the Top 20** → **Verify and export XLSX**
```

The configuration, report-guarantee, and safety sections each contain one short paragraph plus no more than five bullets. Do not repeat detailed procedures that exist in the linked references.

- [ ] **Step 3: Add one collapsed minimal setup**

Use exactly one details block and one PowerShell fence:

````markdown
<details>
<summary><strong>Minimal Windows setup</strong></summary>

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$skillRoot = Join-Path $codexHome "skills/cross-border-ecommerce-daily-report"
git clone https://github.com/huynhledang219-spec/cross-border-ecommerce-daily-report.git $skillRoot
Set-Location $skillRoot
python -m pip install -r ".\scripts\requirements.txt"
python -m playwright install chrome

$runtime = Join-Path $env:LOCALAPPDATA "CrossBorderEcommerceDailyReport"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$config = Join-Path $runtime "config.yaml"
Copy-Item ".\scripts\config.example.yaml" $config
notepad $config
python .\scripts\run_report.py --config $config

$output = Read-Host "Generated XLSX path"
python -c "from pathlib import Path; from scripts.ecommerce_report.workbook import verify_report; print(verify_report(Path(r'$output')))"
```

</details>
````

Explain immediately below it that sign-in remains manual in visible isolated Chrome and that CAPTCHA or human-verification requires stopping for the user.

- [ ] **Step 4: Add compact documentation and closing sections**

Use a four-item documentation list linking to `SKILL.md`, `references/configuration.md`, `references/report-schema.md`, and `LICENSE`. Keep `Contributing` to one sentence directing contributors to preserve tested limits and safety gates. Close with the MIT link.

- [ ] **Step 5: Run the focused test and confirm GREEN**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_public_readme_is_complete_english_and_portable -v
python -m unittest tests.test_public_asset -v
```

Expected: both commands pass.

- [ ] **Step 6: Preview the README**

Open or render `README.md` as GitHub-flavored Markdown. Inspect desktop and narrow-width layouts. Confirm hero centering, showcase scale, heading rhythm, details disclosure, code wrapping, badge accessibility, and relative links. Fix only presentation defects, then rerun the focused tests.

- [ ] **Step 7: Commit the README rewrite**

```powershell
git add -- README.md
git commit -m "docs: streamline public README"
```

## Task 3: Verify and Push the Public Repository

**Files:**
- Verify: `README.md`
- Verify: `tests/test_public_asset.py`
- Verify: entire tracked repository

**Interfaces:**
- Consumes: the concise README and its contract test.
- Produces: fresh release evidence and the user-authorized push of local `main` to `origin/main`.

- [ ] **Step 1: Run fresh repository verification**

Run:

```powershell
python -m unittest discover -s tests
python -m compileall -q scripts tests
git diff --check origin/main..HEAD
```

Run the installed Skill validator with portable `CODEX_HOME` or `$HOME/.codex` resolution. Expected: all tests pass, compileall exits `0`, diff check is clean, and the Skill validates.

- [ ] **Step 2: Run public-safety and link checks**

Confirm zero private absolute paths, sensitive runtime artifacts, tracked caches, generated reports, or broken README-relative links. Report filenames and counts only; never echo secret-like matches.

- [ ] **Step 3: Confirm the exact push range**

Run:

```powershell
git status --short --branch
git log --oneline origin/main..HEAD
```

Expected: clean `main`, with only the reviewed local commits ahead of `origin/main`.

- [ ] **Step 4: Push the authorized main branch**

```powershell
git push origin main
```

Do not force-push. If the remote has moved, stop and inspect rather than rewriting history.

- [ ] **Step 5: Verify remote state**

Run:

```powershell
git fetch origin main
git status --short --branch
git rev-parse main
git rev-parse origin/main
```

Expected: local `main` and `origin/main` resolve to the same commit and the worktree is clean.
