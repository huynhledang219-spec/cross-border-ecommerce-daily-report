# Public README Feature Description Design

## Goal

Expand the public GitHub homepage so a non-technical visitor can understand the Skill's complete, proven value without turning the README into an implementation guide.

## Audience

The primary audience is cross-border e-commerce operators, product researchers, and potential Skill users evaluating the repository for the first time.

## Approved presentation

Keep the existing compact README structure and the `Why this Skill` heading. Replace its short feature list with four result-oriented capability groups:

1. **Verified multi-source collection** — configurable category confirmation in visible isolated Chrome, EchoTik as the bundled default, Amazon as the required supplementary source, and tested replacement-platform adapters.
2. **Top-20 product intelligence** — descending seven-day GMV ranking, exact seven-day sales-amount trends, commercial metrics, complete Amazon titles, and complete Chinese translations.
3. **Daily workbook automation** — template-preserving XLSX output, scheduled Windows execution, wake-to-run, missed-run recovery, same-day retry, and stable source ordering.
4. **Verification, recovery, and privacy** — independent workbook gates, fail-closed human-verification handling, sanitized failure information, and separation of credentials and runtime artifacts from Git.

Update the centered hero subtitle so it communicates the collection, ranking, and verified daily workbook outcome in one sentence.

## Content constraints

- Keep all public README prose in English.
- Describe only behavior already implemented and verified by the repository.
- Keep the README between 100 and 140 lines.
- Preserve the existing report showcase image, workflow, compact setup disclosure, documentation links, limitations, and license.
- Do not add implementation code, installation detail, unsupported-platform claims, or live-site success guarantees.

## Files and behavior

- Change only `README.md`; keep the existing public-asset tests unchanged.
- Do not change `SKILL.md`, `agents/openai.yaml`, runtime code, report behavior, templates, images, or GitHub settings.
- Do not install, schedule, or run live browser collection as part of this documentation update.

## Validation

1. Run the existing focused public-asset test before and after editing the README.
2. Confirm the existing English-only, line-count, heading, link, portability, and compactness gates still pass.
3. Run the complete test suite, Skill validation, compilation check, and `git diff --check`.
4. Confirm the final diff contains only the approved README, plan, and specification changes.
