# Public README Feature Description Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the public README so non-technical visitors can understand the Skill's verified collection, analysis, automation, recovery, and privacy capabilities.

**Architecture:** Keep the existing compact README structure and strengthen only the centered subtitle and `Why this Skill` section. Reuse the repository's existing README structure, language, portability, and link checks; do not add brittle exact-prose assertions for human-facing marketing copy.

**Tech Stack:** GitHub-flavored Markdown, Python 3.12 `unittest`, the existing Skill validator, and Git.

## Global Constraints

- Keep all public README prose in English.
- Keep `README.md` between 100 and 140 lines.
- Describe only behavior already implemented and verified by this repository.
- Preserve the report showcase image, existing workflow, compact setup disclosure, documentation links, limitations, and license.
- Do not modify `SKILL.md`, `agents/openai.yaml`, runtime code, templates, images, or GitHub settings.
- Do not install dependencies, run live browser collection, alter scheduling, or push to GitHub.

---

### Task 1: Guard and publish the expanded public feature description

**Files:**
- Modify: `README.md:1-31`
- Reference: `docs/superpowers/specs/2026-08-21-readme-feature-description-design.md`
- Verify without modification: `tests/test_public_asset.py:634-716`

**Interfaces:**
- Consumes: the existing `test_public_readme_is_complete_english_and_portable` public README contract.
- Produces: a compact English README that names the four approved capability groups and keeps every existing portability and safety gate intact.

- [x] **Step 1: Run the existing focused README contract test**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_public_readme_is_complete_english_and_portable -v
```

Expected: `PASS`. This establishes that the starting README satisfies the existing English-only, 100-to-140-line, compact-code, required-heading, required-contract, and relative-link gates.

- [x] **Step 2: Update the centered README subtitle**

Replace the current centered subtitle with this exact sentence:

```markdown
**A configurable Codex Skill that collects cross-border product intelligence, ranks the Top 20 products by seven-day GMV, and generates verified daily XLSX reports.**
```

- [x] **Step 3: Replace the short feature list with the approved grouped copy**

Keep the existing `## Why this Skill` heading and replace only its current bullets with:

```markdown
### Verified multi-source collection

- Confirms configurable product categories through a visible, isolated Chrome workflow before collection.
- Uses EchoTik as the bundled default platform and Amazon as the required supplementary market source.
- Supports replacement product-intelligence platforms through tested adapters that preserve the same report capabilities.

### Top-20 product intelligence

- Ranks up to 20 primary-platform products by descending seven-day GMV.
- Adds exact seven-day sales-amount trends, product ratings, reviews, related videos, related creators, prices, GMV, and detail links.
- Preserves complete original Amazon titles and complete Chinese translations.

### Daily workbook automation

- Generates a template-preserving XLSX with controlled columns, styles, hyperlinks, hidden helper data, and individual trend charts.
- Supports scheduled Windows execution, wake-to-run, missed-run recovery, and same-day retries after failure.
- Keeps inventory first, followed by the primary platform and Amazon in a consistent source order.

### Verification, recovery, and privacy

- Independently validates required sources, Top-20 ordering, chart data, formulas, links, layout, and sensitive-content boundaries before reporting success.
- Stops safely when login challenges, CAPTCHA, or human verification appears.
- Keeps credentials, cookies, browser profiles, local configuration, generated reports, and sanitized failure records outside Git.
```

- [x] **Step 4: Run the focused test after the README update**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_public_readme_is_complete_english_and_portable -v
```

Expected: `PASS` with the README still satisfying every existing public contract. No exact-prose assertion is added for human-facing marketing copy.

- [x] **Step 5: Run the complete verification gates**

Run:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q scripts tests
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
python (Join-Path $codexHome "skills/.system/skill-creator/scripts/quick_validate.py") "."
git diff --check
```

Expected: the complete test suite passes, compilation exits `0`, Skill validation reports `Skill is valid!`, and the diff check emits no errors.

- [x] **Step 6: Inspect scope and create the approved local implementation commit**

Run:

```powershell
git status --short
git diff -- README.md docs/superpowers/plans/2026-08-21-readme-feature-description.md
git add -- README.md docs/superpowers/plans/2026-08-21-readme-feature-description.md
git diff --cached --check
git commit -m "docs: expand public feature description"
```

Expected: only the approved README and plan changes are included in the second local commit. Do not push.
