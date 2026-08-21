# Product-Focused README Streamlining Design

## Objective

Restructure the public README as a concise product-facing repository homepage. A visitor should understand what the Skill produces, why it is useful, and how to begin without scrolling through implementation-level commands, internal verification rules, or contributor detail.

This change edits presentation only. It does not remove repository code, tests, assets, Skill instructions, reference documentation, or runtime behavior.

## Audience and Tone

Write for three audiences in this order:

1. A potential user deciding whether the Skill solves their reporting problem.
2. A user preparing to install and run it.
3. A technical contributor looking for deeper documentation.

Use professional, plain English. Lead with outcomes and visible capabilities. Move operational and architectural depth behind links or collapsible sections instead of presenting it in the default reading path.

## Page Structure

The README uses this order:

1. Centered hero with project title, one-sentence value proposition, and restrained badges.
2. Sanitized report showcase image and disclosure.
3. `Why this Skill` with six concise capability bullets.
4. `How it works` with a compact four-stage flow.
5. `Quick start` with the minimum installation, configuration, run, and verification commands inside one collapsible section.
6. `Configuration and platform support` with a short explanation of EchoTik as the default, Amazon as the supplementary source, and links to the authoritative configuration and adapter documentation.
7. `Report guarantees` with a compact summary of Top 20 ranking, seven-day trends, template preservation, failure handling, and verification.
8. `Safety and limitations` with only the user-facing boundaries that affect operation.
9. `Documentation`, `Contributing`, and `License` links.

Target approximately 100 to 140 lines, subject to readable Markdown formatting.

## Hero

Use HTML centering only for the hero block. Do not introduce a logo.

The hero contains:

- `Cross-Border E-Commerce Daily Report`
- `A configurable Codex Skill for verified daily product-intelligence workbooks from EchoTik and Amazon.`
- badges for Python 3.12+, Windows, MIT License, and test status without claiming live-site availability.

The existing report showcase remains the main visual. The social-preview image is not embedded in the README because it serves GitHub link sharing rather than page content.

## Content to Keep

Keep these public facts:

- EchoTik is the bundled default primary platform.
- Amazon is the required supplementary source.
- Categories are configurable and must be visibly verified.
- The primary platform is replaceable only through a tested, registered adapter.
- The report ranks at most 20 primary-platform products by descending seven-day GMV.
- Trends use exactly seven daily sales-amount values when available.
- Reports preserve the controlled XLSX layout and pass verification before publication.
- Visible sign-in and human-verification challenges require user action.
- Runtime configuration, profiles, reports, and failure records stay outside the repository.
- Windows Task Scheduler support is optional and user-authorized.

## Content to Compress or Move

Remove the following from the default reading path while preserving the authoritative information in `SKILL.md` and `references/`:

- the text workflow code block;
- the long requirements list;
- repeated PowerShell setup blocks;
- the seven-step category-evidence procedure;
- detailed scheduler behavior and separate scheduler command block;
- the full workbook contract list;
- the eight-step EchoTik replacement procedure;
- the long security checklist;
- the troubleshooting table;
- the full known-limitations list;
- the repository-structure table;
- testing and validator command blocks;
- detailed contributor implementation rules.

The README must link to `references/configuration.md`, `references/report-schema.md`, `SKILL.md`, and `LICENSE` so no authoritative material becomes undiscoverable.

## Quick Start

Keep one collapsed `<details>` block titled `Minimal Windows setup`. Inside it, retain only:

1. Clone the repository into the user's Codex Skills directory.
2. Install the declared requirements and Playwright Chrome channel.
3. Copy `scripts/config.example.yaml` to an external runtime directory and edit the copied file.
4. Run `scripts/run_report.py` with the external configuration path.
5. Verify the generated workbook with the documented verifier entry point.

Do not show scheduling, adapter development, test-suite, Skill-validator, or internal inspection commands in Quick Start.

## Links and Navigation

Use repository-relative links only for tracked files. Every linked path must exist. The documentation section provides a compact index:

- `SKILL.md` — operational workflow and safety gates.
- `references/configuration.md` — configuration, category evidence, scheduling, and adapter registration.
- `references/report-schema.md` — normalized fields, workbook contract, and verification.
- `LICENSE` — MIT terms.

## Repository Scope

In scope:

- `README.md`
- `tests/test_public_asset.py`
- This design specification and the later implementation plan

Out of scope:

- `SKILL.md`, `agents/`, `assets/`, `references/`, and `scripts/`
- Existing test coverage unrelated to the README contract
- Runtime behavior, platform adapters, collection selectors, workbook generation, scheduling, and configuration
- Deleting tracked code, tests, plans, specifications, images, or templates
- GitHub repository settings and social-preview upload

Pushing the completed README is authorized by the user but occurs only after the rewritten page and full repository pass verification.

## Verification

Before push:

- Confirm the README remains fully English and contains no private absolute paths.
- Confirm the required hero copy, showcase image, six capability bullets, four-stage flow, collapsed quick start, platform summary, report guarantees, safety summary, and documentation links are present.
- Confirm removed technical sections and commands do not reappear outside the collapsed minimal setup.
- Confirm all relative Markdown links resolve to tracked files.
- Render or preview the Markdown and inspect hierarchy, spacing, image scale, tables, details disclosure, and mobile-width readability.
- Run the focused README contract tests, complete test suite, compile check, Skill validator, diff check, and tracked sensitive/private-path scans.

## Risks and Mitigations

- **Oversimplifying setup:** retain one complete minimal setup path inside a collapsible section.
- **Hiding authoritative behavior:** link every compressed technical area to `SKILL.md` or the two reference documents.
- **Breaking repository links:** enforce relative-link resolution in the public README test.
- **Marketing overclaim:** state verified local behavior and limitations without claiming universal live-site compatibility.
- **Visual clutter:** keep one showcase image, short sections, no decorative tables, and no additional hero image.

## Rollback

Revert the README and its focused test commit. No runtime code, external state, generated report, or GitHub setting is changed by the rewrite. If the later push has occurred, a normal follow-up revert commit restores the previous README without rewriting remote history.
