# Professional Public Metadata Design

## Objective

Improve the public discoverability and professional positioning of `cross-border-ecommerce-daily-report` without changing its scraping logic, report template, category defaults, runtime behavior, or security boundaries.

All repository-facing content added or revised by this change will be written in English. A Chinese explanation will be provided to the maintainer for review before implementation.

## Audience and Positioning

The primary audience is Codex users, cross-border e-commerce operators, product researchers, and automation engineers who need a configurable Windows workflow for daily product-intelligence reporting.

Use the following domain terminology consistently:

- Cross-border e-commerce product intelligence
- Multi-source data acquisition
- Category-level product discovery
- Top-20 GMV ranking
- Seven-day sales trend analysis
- Template-preserving XLSX generation
- Automated workbook validation
- Human-verification safeguards
- Credential and runtime isolation
- Windows Task Scheduler integration
- Sanitized failure reporting
- Natural-language category reconfiguration

## Approved Changes

### Skill metadata

Revise `SKILL.md` to use product-intelligence terminology in its title, trigger description, overview, and capability summary. Preserve the existing operational workflow, hard limits, category-verification requirements, human-verification stop conditions, and workbook-validation contract.

Revise `agents/openai.yaml` so its display name, short description, and default prompt are fully English and accurately reflect the updated Skill positioning.

### GitHub repository metadata

Set the repository description to:

> Configurable Codex Skill for automated cross-border e-commerce product intelligence, integrating EchoTik and Amazon data into validated daily XLSX reports with Top-20 seven-day GMV trend analysis.

Add these repository topics:

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

### Packaging decision

Do not add a `README.md`. Keep `SKILL.md` as the canonical Skill entry point and avoid duplicating operational guidance across repository files.

## Files and Systems in Scope

- `SKILL.md`
- `agents/openai.yaml`
- This design specification
- The GitHub description and topics for `huynhledang219-spec/cross-border-ecommerce-daily-report`

## Explicitly Out of Scope

- Python or PowerShell implementation changes
- `assets/report-template.xlsx`
- Category IDs, category paths, Amazon URLs, and local runtime configuration
- Dependencies, credentials, browser profiles, generated reports, and scheduled tasks
- Repository visibility, collaborators, permissions, releases, packages, or GitHub Actions

## Accuracy and Safety Constraints

- Every public capability claim must be supported by existing code, tests, or reference documentation.
- Do not imply unattended CAPTCHA handling, credential automation, cross-platform support, real-time analytics, API-based data access, or unlimited detail-page collection.
- Preserve the fixed Top-20 detail limit and seven-day trend window.
- Preserve the requirement for visible category confirmation and manual completion of human-verification challenges.
- Do not add secrets, account identifiers, local paths, credentials, cookies, tokens, or private runtime artifacts.

## Validation

Before committing the implementation:

1. Run the full automated test suite.
2. Run the Skill quick validator.
3. Parse and inspect `agents/openai.yaml` as UTF-8 YAML.
4. Check the diff for unintended runtime, template, or configuration changes.
5. Scan tracked files for sensitive values and forbidden runtime artifacts.
6. Confirm the working tree is clean after the implementation commit.
7. After pushing, verify the GitHub repository remains public, uses `main`, shows the approved description and topics, and exposes the expected Skill files.

## Rollback

- Revert the implementation commit to restore the previous Skill metadata.
- Restore the previous GitHub description and remove the added topics.
- Do not alter or delete prior report-generation commits.

## Acceptance Criteria

- Public-facing Skill metadata is fully English and uses the approved professional terminology.
- The GitHub description and topics match this specification exactly.
- Runtime behavior and report output remain unchanged.
- All validation checks pass with fresh evidence.
- The maintainer receives a Chinese explanation of the final English changes before implementation approval.
