# Public README Design

## Objective

Add a complete, professional, English-language `README.md` for the public GitHub repository. The README must help a new user understand what the Skill does, decide whether it fits their environment, install it safely, configure a product category, run and verify a report, schedule daily execution, and understand how a replacement primary platform can be added without weakening the existing report contract.

The README is user-facing repository documentation. It does not replace `SKILL.md`, `references/configuration.md`, or `references/report-schema.md`; it introduces the project and routes readers to those authoritative documents.

## Audience and language

- Primary audience: Windows users who want a daily cross-border e-commerce product-intelligence workbook.
- Secondary audience: developers who want to implement and validate another primary-platform adapter.
- Public repository content added by this change is English only.
- A Chinese translation is delivered to the repository owner for review but is not committed.

## Content structure

The README will contain these sections in a concise onboarding order:

1. Project title and one-paragraph value proposition.
2. Key capabilities and the generated workbook outcome.
3. A short workflow overview from configuration through verification.
4. System requirements: Windows, Python 3.12 or newer, Google Chrome, and access to the configured data platforms.
5. Installation commands and the rule that dependency installation requires user authorization.
6. Quick start using a local configuration outside the repository.
7. First visible login and manual run, including the hard stop for CAPTCHA or human verification.
8. Category configuration for the primary platform and matching Amazon source.
9. Daily execution and optional 09:00 Windows Task Scheduler setup.
10. Workbook output and verification contract, including Top 20 by seven-day GMV, exact seven-value trends, source order, template preservation, and failure behavior.
11. Replacement-platform adapter model: EchoTik is the bundled default; another platform requires a local registered adapter and the equivalent-capability gate; Amazon remains supplementary.
12. Security and privacy rules for credentials, cookies, profiles, configuration, reports, and failure records.
13. Troubleshooting for sign-in, human verification, empty trend data, failed validation, and missing required sources.
14. Known limitations and non-goals.
15. Repository structure, testing commands, contribution guidance, and MIT license.

## Accuracy boundaries

The README must not claim arbitrary-site compatibility, unattended credential handling, CAPTCHA bypass, cross-platform operating-system support, or successful live collection without a user-authorized visible run. It must clearly distinguish:

- EchoTik as the only bundled primary-platform adapter.
- A replacement platform as an implementation and acceptance task, not a YAML-only switch.
- Amazon as a required supplementary source, not a replacement primary platform.
- A genuinely empty seven-day trend from operational, authentication, navigation, DOM, or challenge failures.
- Local runtime data from version-controlled Skill assets.

Commands and paths must be portable. No private absolute path, real account identifier, credential, cookie, token, generated report, browser profile, or failure record may appear in the README.

## Files and scope

### In scope

- Add `README.md`.
- Update `tests/test_public_asset.py` to replace the historical no-README assertion with a public README contract test.
- Add an implementation plan under `docs/superpowers/plans/` after this specification is approved.

### Out of scope

- Runtime collection, adapter, scheduling, workbook, and validation code.
- `assets/report-template.xlsx`.
- Live configuration, credentials, profiles, reports, and failure records.
- Installing dependencies or the Skill.
- GitHub metadata changes or pushing commits.

## Test-first implementation

Before adding `README.md`, change the public documentation test so it fails because the README is missing. The contract test will require:

- English-only public prose.
- The approved major sections.
- Correct installation, manual-run, daily-run, scheduling, and verification commands.
- Explicit EchoTik-default, Amazon-supplementary, replacement-adapter, Top-20, seven-day trend, and human-verification statements.
- Links only to repository files that exist.
- No private absolute paths or sensitive runtime content.

After observing the expected failure, add the smallest complete README that passes the contract. Run the focused public documentation tests, then the full test suite, Python compilation, Skill validation, diff checks, and tracked-public-text safety scan.

## Risks and mitigations

- **README conflicts with Skill guidance:** keep `SKILL.md` and reference documents authoritative; test key claims against the existing contract.
- **Documentation drifts from commands:** use commands already exercised by the repository tests and reference documentation.
- **Overpromising platform support:** state the closed registry and equivalent-capability requirements explicitly.
- **Sensitive local information leaks:** use portable environment-based examples and retain the tracked public-text scan.
- **Duplicated long-form reference material:** summarize onboarding in the README and link to detailed references.

## Completion criteria

The work is complete when the English README passes its focused contract test, all repository tests and validators pass, the diff contains only approved files, and a Chinese translation has been delivered to the owner for review. Implementation is committed locally but is not pushed without separate authorization.

## Rollback

Revert the local README implementation commit to remove `README.md` and restore the prior documentation test. Revert this specification commit separately if the design itself should be removed.
