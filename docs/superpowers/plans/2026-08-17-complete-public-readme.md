# Complete Public README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a complete English public README that accurately onboards Windows users and replacement-adapter developers without changing the Skill's runtime behavior.

**Architecture:** Treat `README.md` as the public onboarding layer and keep `SKILL.md`, `references/configuration.md`, and `references/report-schema.md` authoritative. Replace the historical no-README assertion with a focused documentation contract that verifies required content, English-only prose, portable repository links, and the existing safety boundaries.

**Tech Stack:** Markdown, Python 3.12+, `unittest`, Git, existing Skill validation tooling.

## Global Constraints

- Add public prose in English only; deliver the Chinese translation to the owner without committing it.
- Keep EchoTik as the only bundled primary-platform adapter and Amazon as the required supplementary source.
- Do not claim arbitrary-site compatibility, credential automation, CAPTCHA bypass, cross-platform operating-system support, or live-site success without visible manual acceptance.
- Keep `detail_limit: 20` and `trend_days: 7`; describe Top 20 selection as descending seven-day GMV with no more than 20 detail-page visits.
- Keep credentials, cookies, browser profiles, local configuration, generated reports, and failure records outside the repository and Git.
- Do not modify runtime collection, adapters, workbook code, scheduling code, `SKILL.md`, reference documents, or `assets/report-template.xlsx`.
- Do not install dependencies, change GitHub metadata, or push commits.

---

## File map

- Create `README.md`: public project overview, setup, operation, verification, extension, safety, and contribution guidance.
- Modify `tests/test_public_asset.py`: replace the historical absence assertion with an explicit README contract test.
- Do not create a separate installation guide, quick-reference file, changelog, screenshot, generated workbook, or example credential file.

### Task 1: Define the public README contract

**Files:**
- Modify: `tests/test_public_asset.py`
- Test: `tests/test_public_asset.py`

**Interfaces:**
- Consumes: `REPOSITORY_ROOT`, `PRIVATE_ABSOLUTE_PATH_PATTERNS`, and the existing `PublicSkillGuidanceTests` class.
- Produces: `PublicSkillGuidanceTests.test_public_readme_is_complete_english_and_portable`, which becomes the executable README contract.

- [ ] **Step 1: Replace the historical no-README assertion with the failing contract test**

Remove this assertion from `test_public_guidance_documents_default_and_replaceable_platform`:

```python
self.assertNotIn("README.md", {path.name for path in REPOSITORY_ROOT.iterdir()})
```

Add this method to `PublicSkillGuidanceTests`:

```python
def test_public_readme_is_complete_english_and_portable(self) -> None:
    readme_path = REPOSITORY_ROOT / "README.md"
    self.assertTrue(readme_path.is_file(), "public README is absent")
    readme = readme_path.read_text(encoding="utf-8")

    self.assertIsNone(
        re.search(r"[\u3400-\u9fff]", readme),
        "public README must remain English-only",
    )

    required_headings = (
        "# Cross-Border E-Commerce Daily Report",
        "## What it does",
        "## Key capabilities",
        "## Workflow",
        "## Requirements",
        "## Installation",
        "## Quick start",
        "## Category configuration",
        "## Daily scheduling",
        "## Workbook contract",
        "## Replacing EchoTik",
        "## Security and privacy",
        "## Troubleshooting",
        "## Known limitations",
        "## Repository structure",
        "## Testing",
        "## Contributing",
        "## License",
    )
    for heading in required_headings:
        self.assertIn(heading, readme)

    required_contract_text = (
        "EchoTik is the bundled default primary platform",
        "Amazon remains a required supplementary source",
        "equivalent-capability gate",
        "Top 20",
        "seven-day GMV",
        "exactly seven",
        "human verification",
        "python .\\scripts\\run_report.py --config \"$reportConfig\"",
        "python .\\scripts\\run_daily.py --config \"$reportConfig\"",
        "install_scheduled_task.ps1",
        "verify_report",
        "python -m unittest discover -s tests -v",
    )
    for required_text in required_contract_text:
        self.assertIn(required_text, readme)

    relative_targets = re.findall(r"\[[^\]]+\]\((?!https?://|#)([^)#]+)(?:#[^)]+)?\)", readme)
    self.assertTrue(relative_targets, "README must link to repository documentation")
    for relative_target in relative_targets:
        self.assertTrue(
            (REPOSITORY_ROOT / relative_target).exists(),
            f"README link target does not exist: {relative_target}",
        )
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_public_readme_is_complete_english_and_portable -v
```

Expected: FAIL with `public README is absent`. A pass means the test is not exercising the missing deliverable and must be corrected before implementation.

### Task 2: Add the complete English README

**Files:**
- Create: `README.md`
- Test: `tests/test_public_asset.py`

**Interfaces:**
- Consumes: the public contract from Task 1 and authoritative behavior in `SKILL.md`, `references/configuration.md`, `references/report-schema.md`, and `scripts/config.example.yaml`.
- Produces: an English public onboarding document whose local links and commands are executable from the repository root.

- [ ] **Step 1: Create the README with the approved onboarding structure**

Use these exact top-level headings in this order:

```markdown
# Cross-Border E-Commerce Daily Report

## What it does
## Key capabilities
## Workflow
## Requirements
## Installation
## Quick start
## Category configuration
## Daily scheduling
## Workbook contract
## Replacing EchoTik
## Security and privacy
## Troubleshooting
## Known limitations
## Repository structure
## Testing
## Contributing
## License
```

Write the sections to satisfy this content recipe:

- `What it does`: identify the repository as a configurable Codex Skill that creates a local, template-preserving, verified XLSX. State verbatim: `EchoTik is the bundled default primary platform. Amazon remains a required supplementary source.`
- `Key capabilities`: list visible category confirmation, multi-source collection, primary-platform Top 20 ranking by descending seven-day GMV, at most 20 detail visits, exactly seven daily sales-amount trend values, complete Amazon English titles with Chinese translations, template preservation, sanitized failure records, and optional Windows scheduling.
- `Workflow`: show the sequence `local configuration -> visible sign-in -> category confirmation -> collection -> Top 20 enrichment -> XLSX generation -> verification` without claiming background persistence by Codex.
- `Requirements`: Windows, Python 3.12+, Google Chrome, access to the selected data platforms, and authorization before dependency installation or scheduling.
- `Installation`: clone/download the repository, check Python, then show:

  ```powershell
  python -m pip install -r ".\scripts\requirements.txt"
  python -m playwright install chrome
  ```

- `Quick start`: create `$reportRuntime` under `$env:LOCALAPPDATA`, copy `scripts/config.example.yaml` to `$reportConfig`, edit the local copy, and run:

  ```powershell
  python .\scripts\run_report.py --config "$reportConfig"
  ```

  Explain that the user signs in manually in the isolated visible Chrome profile. Stop on CAPTCHA, login challenge, or human verification; resume only after the user completes it and requests a retry.
- `Category configuration`: require visible evidence for the complete primary-platform path and identifier plus a matching Amazon HTTPS category/search page. Link to `[Configuration](references/configuration.md)` and never instruct users to guess IDs.
- `Daily scheduling`: show the idempotent command and optional scheduler command:

  ```powershell
  python .\scripts\run_daily.py --config "$reportConfig"
  powershell -ExecutionPolicy Bypass -File ".\scripts\install_scheduled_task.ps1" -ConfigPath "$reportConfig"
  ```

  State that scheduling occurs only after a verified visible manual run and only when requested.
- `Workbook contract`: link to `[Report schema and verification](references/report-schema.md)`, summarize the 15 public columns, source order, Top 20 and chart rules, hidden helper columns, formula/sensitive-content checks, and show the read-only `verify_report` command.
- `Replacing EchoTik`: explain that YAML selects only a closed registered key. A different platform requires a dedicated local adapter, complete `PlatformCapabilities`, normalized records, category evidence, tests, human-verification detection, an equivalent-capability gate, and visible manual acceptance. Amazon is not a primary-platform replacement.
- `Security and privacy`: prohibit committed credentials, cookies, profiles, local configuration, reports, and failure records; prohibit credential automation and CAPTCHA bypass; distinguish sanitized failure reasons from private detailed traces.
- `Troubleshooting`: provide a compact table for not signed in, human verification, genuine empty trend, operational trend failure, empty required source, and workbook verification failure.
- `Known limitations`: Windows-only verified workflow, EchoTik as the only bundled adapter, website UI drift risk, visible manual sign-in, exactly 20 detail pages and seven trend days, and no guarantee that third-party platform access remains available.
- `Repository structure`: list `SKILL.md`, `agents/`, `assets/`, `references/`, `scripts/`, and `tests/` with one-line responsibilities.
- `Testing`: show `python -m unittest discover -s tests -v`, `python -m compileall -q scripts tests`, and the portable Skill validator command using `$env:CODEX_HOME` with `$HOME/.codex` fallback.
- `Contributing`: require tests, no private runtime artifacts, and evidence for any new adapter's equivalent capabilities.
- `License`: link to `[MIT License](LICENSE)`.

- [ ] **Step 2: Run the focused public guidance suite and verify GREEN**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests -v
```

Expected: all public guidance tests PASS, including the new README contract and private-path scan.

- [ ] **Step 3: Inspect the README diff for accuracy and scope**

Run:

```powershell
git diff -- README.md tests/test_public_asset.py
git diff --check
```

Expected: only the approved README and test contract changes, no whitespace errors, no credentials, no private absolute paths, and no runtime behavior changes.

### Task 3: Complete repository verification and commit locally

**Files:**
- Verify: `README.md`
- Verify: `tests/test_public_asset.py`

**Interfaces:**
- Consumes: the GREEN deliverable from Tasks 1 and 2.
- Produces: one reviewed local commit; no remote push.

- [ ] **Step 1: Run the full test suite**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected: every test passes with zero failures and zero errors.

- [ ] **Step 2: Run compilation and Skill validation**

Run:

```powershell
python -m compileall -q scripts tests
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
python (Join-Path $codexHome "skills/.system/skill-creator/scripts/quick_validate.py") "."
```

Expected: compilation exits `0`; validator prints `Skill is valid!`.

- [ ] **Step 3: Run final public-safety and scope checks**

Run:

```powershell
git diff --check
git status --short
git diff --stat
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_tracked_public_text_has_no_literal_private_absolute_paths -v
```

Expected: only `README.md` and `tests/test_public_asset.py` are changed; the private-path test passes.

- [ ] **Step 4: Commit the README and contract test locally**

Run:

```powershell
git add -- README.md tests/test_public_asset.py
git diff --cached --check
git commit -m "docs: add complete public readme"
```

Expected: one local commit containing only the README and its contract test. Do not run `git push`.

- [ ] **Step 5: Prepare the owner handoff**

Report the commit hash, files changed, focused and full test results, compilation and Skill-validation results, remaining live-site limitations, and confirmation that no push occurred. Translate the final English README into Chinese in the response without adding a Chinese repository file.
