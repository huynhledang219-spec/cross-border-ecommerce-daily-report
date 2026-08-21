# GitHub Social Preview Design

## Objective

Create one privacy-safe social preview image for the Cross-Border E-Commerce Daily Report Skill. The image should communicate the repository's purpose at a glance while extending the approved navy, gold, and ivory visual identity used by the README report showcase.

This phase covers the repository asset only. Uploading it through GitHub repository settings is a separate external operation that requires explicit user authorization.

## Deliverable

- Final asset: `assets/readme/social-preview.png`.
- Canvas: exactly 1280 by 640 pixels.
- Format: opaque PNG with a solid background.
- File size: less than 1 MB.
- Repository role: a versioned source asset for GitHub's Social preview setting; it is not embedded in the README.

These dimensions and the file-size ceiling follow [GitHub's published social-preview recommendation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview).

## Visual Direction

Use the user's approved first concept: a two-column composition on a deep navy background with a restrained dotted world map and thin gold cross-border route details.

The left side contains the project identity and capability summary. The right side contains a simplified, front-facing ivory report card with a warm-gold header and several fictional data rows. The image should feel like credible B2B product-intelligence software: clear, composed, and professional.

Avoid logos, real product imagery, people, browser chrome, aggressive perspective, open-book styling, neon effects, glassmorphism, and decorative clutter.

## Exact Copy

Render all visible text deterministically and verbatim:

- Title: `Cross-Border E-Commerce Daily Report`
- Subtitle: `Verified product intelligence from EchoTik and Amazon`
- Capability labels:
  - `TOP 20 BY 7-DAY GMV`
  - `7-DAY SALES TRENDS`
  - `CONFIGURABLE CATEGORIES`
  - `VERIFIED XLSX OUTPUT`
- Footer badge: `CODEX SKILL · MIT LICENSE`

The title may wrap across two lines. The subtitle and all four capability labels must remain readable when the image is reduced to a social-card thumbnail.

## Report Card

The right-side report card is a visual abstraction of the public workbook rather than a literal screenshot. It includes:

- a gold header band;
- a small set of neutral icon or short text marks;
- fictional values for ranking, GMV, sales, and rating;
- distinct seven-day trend lines;
- a subtle pale-green highlighted row that recalls the inventory-row treatment.

No real product title, listing URL, account name, store name, credential, sales figure, or platform logo may appear. The card must not imply that the fictional values are live data.

## Production Approach

1. Use the approved concept and existing README showcase only as visual references.
2. Generate or derive only non-text decorative background material with image generation when useful.
3. Render the title, subtitle, capability labels, badge, report card, fictional values, and trend lines deterministically with local image tooling.
4. Composite and downsample the final image to exactly 1280 by 640 pixels.
5. Optimize the PNG below 1 MB without reducing text clarity.
6. Save only the final asset in the repository; keep generated scratch files outside tracked paths.

## Repository Scope

In scope:

- `assets/readme/social-preview.png`
- `tests/test_public_asset.py`
- This design specification and the later implementation plan

Out of scope:

- `README.md`, `SKILL.md`, runtime collectors, adapters, browser automation, workbook generation, scheduling, and configuration behavior
- Live website access or account sign-in
- GitHub repository-settings changes or social-preview upload
- Any push to GitHub without separate user authorization

## Verification

Before completion:

- Confirm dimensions are exactly 1280 by 640.
- Confirm the PNG is under 1 MB and uses a solid, non-transparent background.
- Confirm the PNG contains no text metadata, EXIF data, private paths, credentials, or real report data.
- Confirm every visible phrase matches the approved copy exactly.
- Inspect the image at full resolution and at social-card thumbnail size.
- Confirm the title, subtitle, capability labels, report card, and trend lines remain visually distinct.
- Run the relevant public-asset tests, full test suite, Skill validation, compile check, diff check, and tracked sensitive/private-path scans.

## Risks and Mitigations

- **AI text corruption:** render all readable content deterministically; use image generation only for non-text visual material.
- **Thumbnail cropping or weak hierarchy:** keep critical content inside generous safe margins and inspect a reduced preview.
- **Accidental disclosure:** use fictional data only and scan both repository files and PNG metadata before commit.
- **File-size overflow:** optimize the final PNG and enforce the limit with an automated test.
- **Mismatch with the README identity:** reuse the established navy, warm-gold, ivory, world-map, and trade-route visual vocabulary.

## Rollback

The repository change is additive and reversible. Revert the associated commits or remove `assets/readme/social-preview.png` and its dedicated public-asset assertions. No runtime state or external service is modified. If a later GitHub upload is separately authorized, GitHub's Social preview control can remove or replace the uploaded image independently.
