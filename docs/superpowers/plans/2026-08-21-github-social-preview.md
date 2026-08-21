# GitHub Social Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one exact 1280-by-640, privacy-safe GitHub social preview that presents the Skill in the approved navy-and-gold first-concept composition.

**Architecture:** Enforce the binary asset contract with a failing standard-library PNG test, then create the final raster in an isolated temporary directory. Use image generation only for a text-free navy world-map backdrop; render every word, report-card mark, fictional metric, and seven-day trend deterministically with bundled Python and Pillow before stripping metadata and copying only the final PNG into the repository.

**Tech Stack:** Built-in image generation, bundled Python and Pillow, Python `unittest`, PNG chunk inspection with the standard library, Git.

## Global Constraints

- The final file is `assets/readme/social-preview.png`, exactly 1280 by 640 pixels, opaque RGB PNG, and less than 1,000,000 bytes.
- Use a solid deep-navy background, restrained dotted world-map details, thin warm-gold trade routes, an ivory report card, and the approved two-column composition.
- Render the approved title, subtitle, four capability labels, and footer badge deterministically and verbatim.
- Use fictional abstract marks and metrics only; do not read private reports, profiles, cookies, credentials, accounts, stores, live websites, or real product data.
- Do not use platform logos, real product images, people, browser chrome, open-book styling, aggressive perspective, neon, glassmorphism, or watermarks.
- Do not modify `README.md`, `SKILL.md`, runtime code, workbook assets, collectors, adapters, scheduling, or configuration.
- Keep all generated backgrounds, scripts, thumbnails, and intermediates outside tracked repository paths.
- Do not upload the asset through GitHub Settings and do not push without separate user authorization.

---

## File Map

- Create: `assets/readme/social-preview.png` — final optimized public asset only.
- Modify: `tests/test_public_asset.py` — exact path, dimensions, RGB mode, chunk allowlist, and size-limit contract.
- Use without modifying: `assets/readme/report-showcase.png` — visual-identity reference only.
- Temporary only: `$env:TEMP/cross-border-social-preview/` — generated background, deterministic compositor, and thumbnail.

## Task 1: Define the Social-Preview Asset Contract

**Files:**
- Modify: `tests/test_public_asset.py`
- Test: `tests/test_public_asset.py`

**Interfaces:**
- Consumes: repository root and the existing `_read_png_chunks(path)` helper.
- Produces: `SOCIAL_PREVIEW_PATH: Path`, `_read_png_color_type(path) -> int`, and a focused regression test that Task 2 must satisfy.

- [ ] **Step 1: Add the asset constant and RGB inspection helper**

Add the constant beside `README_SHOWCASE_PATH`:

```python
SOCIAL_PREVIEW_PATH = REPOSITORY_ROOT / "assets" / "readme" / "social-preview.png"
```

Add this helper immediately after `_read_png_chunks`:

```python
def _read_png_color_type(path: Path) -> int:
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise AssertionError("social preview is not a structurally valid PNG")
    return payload[25]
```

- [ ] **Step 2: Add the failing focused test**

Add this method to `PublicSkillGuidanceTests`:

```python
def test_github_social_preview_is_exact_opaque_metadata_free_png(self) -> None:
    self.assertTrue(SOCIAL_PREVIEW_PATH.is_file(), "social preview image is absent")
    width, height, chunks = _read_png_chunks(SOCIAL_PREVIEW_PATH)
    self.assertEqual((width, height), (1280, 640))
    self.assertEqual(_read_png_color_type(SOCIAL_PREVIEW_PATH), 2)
    self.assertLess(SOCIAL_PREVIEW_PATH.stat().st_size, 1_000_000)
    self.assertEqual(chunks[0], "IHDR")
    self.assertEqual(chunks[-1], "IEND")
    self.assertTrue(
        set(chunks) <= {"IHDR", "IDAT", "IEND"},
        "social preview contains metadata, transparency, or ancillary PNG chunks",
    )
```

- [ ] **Step 3: Run the focused test and confirm RED**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_github_social_preview_is_exact_opaque_metadata_free_png -v
```

Expected: `FAIL` with `social preview image is absent` because the final asset has not been created.

- [ ] **Step 4: Run the existing README-showcase test**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_readme_showcase_is_exact_sanitized_png_and_linked -v
```

Expected: `PASS`; the new helper and constant do not weaken the existing public-image contract.

- [ ] **Step 5: Commit the RED contract**

```powershell
git add -- tests/test_public_asset.py
git commit -m "test: define GitHub social preview contract"
```

## Task 2: Produce the Approved Deterministic Social Preview

**Files:**
- Use without modifying: `assets/readme/report-showcase.png`
- Temporary create: `$env:TEMP/cross-border-social-preview/background.png`
- Temporary create: `$env:TEMP/cross-border-social-preview/draw_social_preview.py`
- Temporary create: `$env:TEMP/cross-border-social-preview/social-preview-thumbnail.png`
- Create: `assets/readme/social-preview.png`

**Interfaces:**
- Consumes: the approved design specification, the selected first-concept composition, a text-free generated background, and bundled Pillow.
- Produces: one exact RGB PNG that satisfies the Task 1 contract.

- [ ] **Step 1: Create an isolated temporary work directory**

Resolve the temporary target without using a private absolute path:

```powershell
$previewWork = Join-Path $env:TEMP 'cross-border-social-preview'
New-Item -ItemType Directory -Force -Path $previewWork | Out-Null
```

Confirm `git status --short` is clean except for the committed Task 1 state before creating any intermediate file.

- [ ] **Step 2: Generate only the decoration-only background**

Use the built-in image-generation tool with this prompt:

```text
Use case: ads-marketing
Asset type: GitHub repository social-preview background
Primary request: Create a premium 2:1 decoration-only background for a cross-border e-commerce product-intelligence project.
Scene/backdrop: deep matte navy field with a restrained dotted world map and a few thin warm-gold trade-route arcs and nodes.
Composition/framing: keep the left half calm enough for large typography and the right half calm enough for an ivory report card; preserve generous edge margins.
Lighting/mood: credible, calm, professional B2B editorial finish.
Constraints: background decoration only; no text, no letters, no numbers, no spreadsheet, no product, no icon, no logo, no people, no watermark, no browser UI.
Avoid: neon, glassmorphism, heavy glow, photographic objects, open-book imagery, strong perspective, clutter.
```

Inspect the result. Reject it if it contains any text-like marks, product imagery, logos, browser UI, or distracting high-contrast detail. Copy only the accepted background to `$previewWork/background.png`; do not track it.

- [ ] **Step 3: Create the deterministic compositor**

Create `$previewWork/draw_social_preview.py` with the loader-provided or active project Python and Pillow. Use these exact constants and copy:

```python
CANVAS = (1280, 640)
PALETTE = {
    "navy": "#071A33",
    "navy_light": "#173654",
    "gold": "#F3C557",
    "gold_dark": "#C99B34",
    "ivory": "#FFFDF6",
    "ink": "#10233D",
    "muted": "#617087",
    "green": "#2E7D4F",
    "green_pale": "#EAF5EC",
    "red": "#C94735",
    "grid": "#D8D9D4",
}

TITLE = "Cross-Border E-Commerce\nDaily Report"
SUBTITLE = "Verified product intelligence from EchoTik and Amazon"
CHIPS = (
    "TOP 20 BY 7-DAY GMV",
    "7-DAY SALES TRENDS",
    "CONFIGURABLE CATEGORIES",
    "VERIFIED XLSX OUTPUT",
)
BADGE = "CODEX SKILL · MIT LICENSE"
```

Use `ImageOps.fit(background, CANVAS, method=Image.Resampling.LANCZOS)` and darken it with a translucent `#071A33` overlay so all deterministic content remains dominant. Draw all text with an installed sans-serif font selected in this order: `Segoe UI Variable Display Semibold`, `Segoe UI Semibold`, then `Arial Bold`; use matching regular faces for supporting copy. Stop with a clear error if none exists.

Use this geometry:

```python
LEFT_X = 72
LEFT_WIDTH = 520
TITLE_Y = 106
SUBTITLE_Y = 270
CHIP_RECTS = ((72, 334, 286, 376), (300, 334, 520, 376),
              (72, 390, 286, 432), (300, 390, 520, 432))
BADGE_RECT = (72, 516, 310, 558)
CARD_RECT = (650, 72, 1210, 568)
CARD_HEADER_BOTTOM = 146
```

Render the title in ivory at approximately 50 pixels with 1.02 line spacing, the subtitle in a muted light-blue at 20 pixels, chip labels in navy on warm-gold rounded rectangles at 13 pixels, and the footer badge as a restrained outlined gold capsule at 14 pixels. Measure text and reduce only within the specified size ranges if a phrase exceeds its rectangle; never truncate or alter the approved copy.

Construct the report card as a front-facing rounded ivory rectangle with a subtle shadow, a gold header band, five body rows, thin neutral grid lines, one pale-green highlighted row, abstract product glyphs, short neutral bars instead of product names, fictional metric strings, rating stars, and five distinct seven-point trend lines. Use only these fictional metrics:

```python
ROWS = (
    ("24,560", "$128,450", "+18.6%", "1,842", "4.6", "up"),
    ("3,210", "$18,750", "+24.3%", "312", "4.7", "up"),
    ("2,980", "$14,560", "+12.1%", "278", "4.5", "mixed"),
    ("4,150", "$22,300", "+8.7%", "356", "4.6", "up"),
    ("2,450", "$15,120", "-3.2%", "219", "4.3", "down"),
)

TRENDS = (
    (3, 4, 6, 5, 7, 8, 10),
    (2, 5, 6, 8, 8, 9, 10),
    (8, 6, 7, 5, 6, 4, 9),
    (2, 3, 3, 5, 4, 7, 8),
    (9, 6, 8, 5, 7, 4, 3),
)
```

Keep all card details within `CARD_RECT`, with a minimum 32-pixel interior margin. Do not render `EchoTik` or `Amazon` logos. The subtitle is the only place those platform names appear.

Convert the final image to RGB. Save first to the temporary directory with `optimize=True` and no EXIF, comment, text, or ICC data. If it exceeds 1,000,000 bytes, quantize only the generated background before recompositing; do not raster-resize or blur the deterministic text layer. Copy the validated final output to `assets/readme/social-preview.png`.

- [ ] **Step 4: Create and inspect a thumbnail**

Use the compositor to save a temporary 640-by-320 LANCZOS thumbnail. Inspect both files and confirm:

- title, subtitle, four capability labels, and badge match the approved copy exactly;
- the title and report card remain distinct at 640-by-320;
- the table contains five visibly different trend shapes and one pale-green row;
- no AI-generated text or text-like artifacts remain in the background;
- no real product, account, store, listing URL, or sales record appears;
- no content touches the crop-safe outer 48 pixels.

If any check fails, change one compositing variable at a time and repeat the full-size and thumbnail inspection.

- [ ] **Step 5: Run the focused contract and public-asset suite**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_github_social_preview_is_exact_opaque_metadata_free_png -v
python -m unittest tests.test_public_asset -v
```

Expected: both commands pass. Inspect the reported file size separately and confirm it is below 1,000,000 bytes.

- [ ] **Step 6: Commit the final asset**

```powershell
git add -- assets/readme/social-preview.png
git commit -m "docs: add GitHub social preview"
```

Do not add the temporary background, compositor, or thumbnail.

## Task 3: Final Privacy, Visual, and Repository Verification

**Files:**
- Verify: `assets/readme/social-preview.png`
- Verify: `tests/test_public_asset.py`
- Verify: entire tracked repository

**Interfaces:**
- Consumes: the completed test and final PNG commits.
- Produces: fresh evidence that the new asset is accurate, metadata-free, private-data-free, and repository-safe.

- [ ] **Step 1: Run fresh automated checks**

Run:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q scripts tests
git diff --check HEAD~2..HEAD
```

Run the installed Skill validator using the repository's existing portable `CODEX_HOME` or `$HOME/.codex` resolution. Expected: all tests pass, compileall exits `0`, diff check is clean, and Skill validation reports valid.

- [ ] **Step 2: Scan the tracked repository and PNG structure**

Confirm filenames and counts only:

- zero tracked private absolute paths;
- zero credentials, cookies, tokens, browser profiles, private reports, or newly created XLSX files;
- zero tracked temporary scripts, generated backgrounds, thumbnails, cache files, or build directories;
- the final PNG contains only `IHDR`, one or more `IDAT`, and `IEND` chunks;
- the final PNG is RGB color type 2, exactly 1280 by 640, and below 1,000,000 bytes.

Do not print any matched secret-like content.

- [ ] **Step 3: Perform the final visual pass**

Inspect the final PNG at original resolution and at 640-by-320. Compare it against `docs/superpowers/specs/2026-08-21-github-social-preview-design.md` and record facts separately from assumptions and unresolved limitations.

- [ ] **Step 4: Confirm repository state and hand off without uploading or pushing**

Run:

```powershell
git status --short --branch
git log -5 --oneline
```

Expected: clean worktree, local `main` ahead of `origin/main`, no GitHub Settings change, and no push. Report the final asset path, commit hashes, exact check results, final prompt, and whether the built-in image-generation path was used.
