# README Report Showcase Design

## Objective

Create one privacy-safe README image that shows the practical XLSX output of the Cross-Border E-Commerce Daily Report Skill. The asset should make the report immediately understandable while matching the approved premium navy-and-gold visual direction.

This phase covers only the README report showcase. The GitHub social preview remains a separate later phase.

## Deliverable

- Final asset: `assets/readme/report-showcase.png`.
- Canvas: exactly 1920 by 1080 pixels.
- Format: PNG, optimized for GitHub README display.
- README placement: near the introductory project description, before the detailed capability list.
- Visible disclosure: an exact `DEMO DATA` badge.

## Visual Direction

Use a deep navy background, restrained dotted world map and trade-route details, warm gold accents, and a large front-facing ivory report card. The composition should feel like professional B2B product intelligence: credible, calm, and practical.

The workbook must remain the dominant subject. It must not use an open-book metaphor, center fold, aggressive perspective, browser chrome, platform logos, people, neon effects, glassmorphism, or excessive decoration.

## Report Fidelity

The displayed report is derived from the packaged public template at `assets/report-template.xlsx`, not from an AI-invented spreadsheet. It preserves the approved header order, yellow header treatment, pale-green inventory row, alternating product-row styling, and the diagnosis-column trend-chart pattern.

The visible sample includes:

1. One inventory row first.
2. A small set of ranked EchoTik demonstration rows.
3. A small set of Amazon demonstration rows.
4. Distinct seven-day trend shapes for the ranked primary-platform products.

All readable spreadsheet text is rendered deterministically. AI image generation may supply only the decorative background or concept reference; it must not render the final Chinese headers, product titles, metrics, or charts.

## Sanitized Demonstration Data

All rows and numbers are fictional. The showcase must not read or reuse private daily reports, browser profiles, cookies, credentials, account identifiers, store names, real product listings, or actual sales data.

Use neutral generic product examples and synthetic values. The visible source values may be `你的库存`, `EchoTik`, and `Amazon` because they are part of the public report contract. No platform logo is used.

The synthetic data should look internally varied and plausible: prices, ratings, GMV, sales, related-video counts, related-creator counts, and trend shapes must not repeat mechanically.

## Production Approach

1. Import and render the packaged public template read-only with the approved spreadsheet tooling.
2. Use the rendered template as the deterministic geometry and style reference for a synthetic report image; do not create or modify an XLSX.
3. Draw all fictional rows, Chinese text, metrics, and seven-day trends deterministically with bundled image tooling.
4. Create or select a navy-and-gold decorative background consistent with the approved concept.
5. Composite the deterministic report image onto the background without altering its readable contents.
6. Save only the final sanitized PNG inside the repository.
7. Add the image to `README.md` and add public-asset regression checks.

No intermediate XLSX is created. No browser data, generated-image scratch files, credentials, or private reports are committed.

## Repository Scope

In scope:

- `assets/readme/report-showcase.png`
- `README.md`
- `tests/test_public_asset.py`
- This design specification and the later implementation plan

Out of scope:

- Runtime collectors, adapters, browser automation, workbook production logic, scheduling, and configuration behavior
- GitHub social-preview upload or repository-settings changes
- Live website access or account sign-in
- Any push to GitHub without separate user authorization

## Verification

Before completion:

- Confirm PNG dimensions are exactly 1920 by 1080.
- Confirm the image opens and passes a full visual inspection at normal and thumbnail sizes.
- Confirm the workbook content is legible, unobscured, and free of AI-generated text errors.
- Confirm the inventory row appears before EchoTik and Amazon rows.
- Confirm visible trends are distinct and the `DEMO DATA` badge is readable.
- Confirm `README.md` references the tracked image using a relative path.
- Run the relevant public-asset tests, full test suite, Skill validation, compile check, diff check, and tracked sensitive/private-path scans.

## Risks and Mitigations

- **AI text corruption:** render all report text and charts deterministically, using image generation only for decoration.
- **Accidental data disclosure:** use only synthetic input and scan the final repository and PNG package metadata before commit.
- **Misrepresenting the actual report:** derive the displayed table from the packaged public template and preserve its contract.
- **Poor GitHub readability:** verify the final asset both at full resolution and at README thumbnail scale.

## Rollback

The change is additive and reversible. Remove `assets/readme/report-showcase.png`, revert its README reference and tests, and revert the associated commit. No runtime state or external service is modified.
