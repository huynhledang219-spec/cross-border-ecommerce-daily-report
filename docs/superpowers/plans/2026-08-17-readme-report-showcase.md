# README Report Showcase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one exact 1920×1080, privacy-safe README image that faithfully demonstrates the packaged report layout in the approved navy-and-gold visual direction.

**Architecture:** Build a synthetic workbook only in a temporary directory by importing the packaged public template with `@oai/artifact-tool`, preserving the template's visible structure and adding deterministic fictional rows and seven-day sparklines. Render the table, combine it with an image-generated decoration-only background using bundled Pillow, strip PNG metadata, then track only the final image and reference it from the English README.

**Tech Stack:** `@oai/artifact-tool` 2.8.6+, bundled Node.js, bundled Python and Pillow, built-in image generation, Python `unittest`, Git.

## Global Constraints

- The final file is `assets/readme/report-showcase.png`, exactly 1920×1080 PNG.
- The final composition uses deep navy, restrained dotted world-map details, warm gold accents, and a front-facing ivory report card.
- Use only fictional generic products and synthetic values; do not read private reports, profiles, cookies, credentials, account identifiers, stores, or live websites.
- Preserve the public template's header order, yellow header treatment, pale-green inventory row, alternating row treatment, and diagnosis-column seven-day trend pattern.
- The inventory row appears first, followed by EchoTik demonstration rows and Amazon demonstration rows.
- `DEMO DATA` is the only text rendered by image generation. All report text, numbers, and trends are rendered deterministically.
- Do not track temporary XLSX files, intermediate renders, generated backgrounds, builders, private paths, or image metadata.
- Do not change runtime collectors, adapters, browser automation, workbook production logic, scheduling, or configuration behavior.
- Do not upload a GitHub social preview and do not push without separate user authorization.

---

## File Map

- Create: `assets/readme/report-showcase.png` — final sanitized README image only.
- Modify: `README.md` — add one English-captioned relative image immediately after the introduction.
- Modify: `tests/test_public_asset.py` — enforce the image path, PNG dimensions, metadata boundary, size limit, and README reference.
- Use without modifying: `assets/report-template.xlsx` — source of the visible report structure.
- Temporary only: `$env:TEMP/cross-border-report-showcase/` — synthetic workbook, artifact-tool render, decoration-only background, and compositing script.

## Task 1: Lock the Public Image Contract with a Failing Test

**Files:**
- Modify: `tests/test_public_asset.py`
- Test: `tests/test_public_asset.py`

**Interfaces:**
- Consumes: repository root and `README.md`.
- Produces: `README_SHOWCASE_PATH: Path`, `_read_png_chunks(path) -> tuple[int, int, tuple[str, ...]]`, and a regression test that later tasks must satisfy.

- [ ] **Step 1: Add standard-library PNG inspection helpers**

Add `struct` to the imports, define the final path beside `ASSET_PATH`, and add this helper before the test classes:

```python
README_SHOWCASE_PATH = REPOSITORY_ROOT / "assets" / "readme" / "report-showcase.png"


def _read_png_chunks(path: Path) -> tuple[int, int, tuple[str, ...]]:
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError("README showcase is not a PNG")
    cursor = 8
    width = height = 0
    chunks: list[str] = []
    while cursor < len(payload):
        length = struct.unpack(">I", payload[cursor : cursor + 4])[0]
        chunk_type = payload[cursor + 4 : cursor + 8].decode("ascii")
        chunk_data = payload[cursor + 8 : cursor + 8 + length]
        chunks.append(chunk_type)
        if chunk_type == "IHDR":
            width, height = struct.unpack(">II", chunk_data[:8])
        cursor += 12 + length
        if chunk_type == "IEND":
            break
    return width, height, tuple(chunks)
```

- [ ] **Step 2: Add the failing showcase test**

Add this method to `PublicSkillGuidanceTests`:

```python
def test_readme_showcase_is_exact_sanitized_png_and_linked(self) -> None:
    self.assertTrue(README_SHOWCASE_PATH.is_file(), "README showcase image is absent")
    width, height, chunks = _read_png_chunks(README_SHOWCASE_PATH)
    self.assertEqual((width, height), (1920, 1080))
    self.assertLess(README_SHOWCASE_PATH.stat().st_size, 3_000_000)
    self.assertTrue(
        {"tEXt", "zTXt", "iTXt", "eXIf"}.isdisjoint(chunks),
        "README showcase contains textual or EXIF metadata",
    )
    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    self.assertIn(
        "![Sanitized cross-border e-commerce daily report showcase]"
        "(assets/readme/report-showcase.png)",
        readme,
    )
```

- [ ] **Step 3: Run the focused test and confirm RED**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_readme_showcase_is_exact_sanitized_png_and_linked -v
```

Expected: `FAIL` because `assets/readme/report-showcase.png` does not exist.

- [ ] **Step 4: Commit the contract test**

```powershell
git add -- tests/test_public_asset.py
git commit -m "test: define README showcase contract"
```

## Task 2: Produce the Deterministic Sanitized Report Render

**Files:**
- Use without modifying: `assets/report-template.xlsx`
- Temporary create: `$env:TEMP/cross-border-report-showcase/build_showcase.mjs`
- Temporary create: `$env:TEMP/cross-border-report-showcase/sanitized-showcase.xlsx`
- Temporary create: `$env:TEMP/cross-border-report-showcase/report-render.png`

**Interfaces:**
- Consumes: packaged public template and loader-provided Node executable and `node_modules` path.
- Produces: a temporary synthetic workbook plus an exact report-range PNG with no private input.

- [ ] **Step 1: Reload bundled dependency paths and create an isolated work directory**

Call `load_workspace_dependencies`, record the returned Node executable and `node_modules` directory, then create `$env:TEMP/cross-border-report-showcase`. Create a Windows junction named `node_modules` inside that directory that targets only the loader-provided dependency directory. Do not modify the dependency bundle.

- [ ] **Step 2: Read the required spreadsheet instructions and inspect the template read-only**

Read `spreadsheets/SKILL.md`, `style_guidelines.md`, `artifact_tool_docs/API_QUICK_START.md`, and `features/charts.md` completely. Import `assets/report-template.xlsx`, inspect `Sheet1!A1:V4` for values and computed styles, inspect its drawings, and render `Sheet1!A1:O4`. Visually confirm the yellow header, green inventory row, alternating data rows, hidden detail/helper columns, and diagnosis-column drawing position before authoring.

- [ ] **Step 3: Mark the spreadsheet edit operation exactly once**

Immediately before the first authoring command, run the spreadsheet skill's required marker as an edit operation with one expected XLSX output:

```powershell
node container_tools/mark_artifact_operation_started.mjs --operation-kind edit --expected-output-count 1 --output-format xlsx
```

Expected: exit code `0`. If the required marker or bundled artifact runtime is unavailable, stop and report the tooling blocker; do not substitute another spreadsheet library.

- [ ] **Step 4: Create the one-off artifact-tool builder**

Create one executable `build_showcase.mjs` in the temporary directory. It must import the public template, remove the template's empty drawing, extend the existing row styles by copying row 3 and row 4 in an alternating pattern, write these exact fictional records to `A2:O9`, write the matching seven values to `P:V`, add line sparklines only for EchoTik rows, inspect the populated table, scan formula errors, render `A1:O9`, and export the temporary workbook.

Use these fictional rows in order:

```js
const records = [
  ["SKU", "", "你的库存", "Portable Desk Organizer", "便携式桌面收纳架", 18.90, "-", "-", "-", "-", "-", "-", "-", "", "库存12件｜建议售价$18.90"],
  [1, "Top 1", "EchoTik", "Reusable Travel Bottle Set", "可重复使用旅行分装瓶套装", 16.80, 4.7, 1842, 128450, 28640, 1640, 312, 86, "", ""],
  [2, "Top 2", "EchoTik", "Adjustable Drawer Organizer", "可调节抽屉收纳隔板套装", 22.50, 4.6, 1335, 109820, 24190, 1435, 276, 74, "", ""],
  [3, "Top 3", "EchoTik", "Rechargeable Cleaning Brush", "可充电多功能清洁刷", 29.90, 4.5, 978, 96300, 21870, 1264, 225, 61, "", ""],
  [4, "Top 4", "EchoTik", "Vacuum Storage Bag Kit", "真空压缩收纳袋套装", 19.40, 4.4, 864, 81750, 19320, 1088, 198, 53, "", ""],
  ["", "", "Amazon", "Stainless Steel Kitchen Tongs with Silicone Tips, Set of 3", "硅胶头不锈钢厨房夹三件套", 17.99, 4.6, 6240, "-", "-", "-", "-", "-", "", "补充市场参考"],
  ["", "", "Amazon", "Foldable Travel Packing Cubes, Lightweight 6-Piece Set", "轻量化可折叠旅行收纳袋六件套", 24.99, 4.5, 3812, "-", "-", "-", "-", "-", "", "补充市场参考"],
  ["", "", "Amazon", "Reusable Microfiber Cleaning Cloths, Pack of 12", "可重复使用超细纤维清洁布十二件套", 14.99, 4.7, 5291, "-", "-", "-", "-", "-", "", "补充市场参考"],
];

const trends = [
  [3020, 3380, 3710, 3650, 4210, 4870, 5800],
  [2850, 3120, 2980, 3470, 3860, 3740, 4170],
  [2410, 2260, 2690, 3010, 2870, 3380, 4250],
  [3200, 2890, 2740, 3010, 2670, 2500, 2310],
];
```

Use the documented APIs:

```js
const input = await FileBlob.load(templatePath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sheet = workbook.worksheets.getItem("Sheet1");
sheet.deleteAllDrawings();
for (let row = 5; row <= 9; row += 1) {
  const source = row % 2 === 1 ? sheet.getRange("A3:V3") : sheet.getRange("A4:V4");
  source.copyTo(sheet.getRange(`A${row}:V${row}`), "all");
}
sheet.getRange("A2:O9").values = records;
sheet.getRange("P3:V6").values = trends;
for (let row = 3; row <= 6; row += 1) {
  sheet.getRange(`O${row}`).sparklines.add(
    "line",
    sheet.getRange(`P${row}:V${row}`),
    {seriesColor: "#0B4F8A", markers: {show: true}}
  );
}
```

Render with:

```js
const preview = await workbook.render({
  sheetName: "Sheet1",
  range: "A1:O9",
  scale: 1.5,
  format: "png",
});
```

- [ ] **Step 5: Run the builder and verify the temporary workbook and render**

Run the builder with the loader-provided Node executable from the temporary directory. Inspect `A1:V9`, scan `#REF!|#DIV/0!|#VALUE!|#NAME\?|#N/A`, and save `report-render.png`. Visually confirm exact Chinese headers, the inventory-first order, EchoTik-before-Amazon grouping, four distinct sparklines, readable values, and no clipping.

Do not continue if the template import changes the public template file or if the render contains corrupted text.

## Task 3: Build the Final 1920×1080 Showcase Image

**Files:**
- Temporary create: `$env:TEMP/cross-border-report-showcase/background.png`
- Temporary create: `$env:TEMP/cross-border-report-showcase/composite_showcase.py`
- Create: `assets/readme/report-showcase.png`

**Interfaces:**
- Consumes: the deterministic `report-render.png` from Task 2 and a decoration-only image-generated background.
- Produces: the final metadata-free 1920×1080 PNG.

- [ ] **Step 1: Generate only the decorative background**

Use the built-in image-generation tool with this exact intent:

```text
Create a 16:9 decoration-only background for a professional cross-border e-commerce product-intelligence report. Deep navy matte field, restrained dotted world map, a few thin warm-gold trade-route arcs and nodes, subtle vignette, calm B2B editorial quality. Keep the center area quiet and dark for a large report card. No spreadsheet, no text, no numbers, no icons, no logos, no people, no watermark, no neon, no glassmorphism.
```

Copy the selected preview into the temporary work directory. Do not track the raw generated background.

- [ ] **Step 2: Composite deterministically with bundled Pillow**

Create one temporary Python compositor using only the loader-provided Python and Pillow. It must:

1. Resize and center-crop the background to 1920×1080.
2. Resize the deterministic report render to fit within 1720×780 without distortion.
3. Add a restrained soft shadow and 14-pixel ivory frame behind the report.
4. Center the report horizontally and place it around y=190.
5. Draw an exact `DEMO DATA` badge in the top-right safe area with a Windows sans-serif bold font.
6. Convert the image to RGB and save with `optimize=True`, without EXIF, comments, text chunks, or an ICC profile.

The final save target is `assets/readme/report-showcase.png`. Do not overwrite another asset.

- [ ] **Step 3: Inspect the final image at full and thumbnail size**

Open the final PNG at original resolution and a 640-pixel-wide preview. Confirm:

- every visible report label is readable and unobscured;
- no AI-generated report text appears;
- the inventory row is first;
- EchoTik rows precede Amazon rows;
- all four visible seven-day trends differ;
- the background supports rather than competes with the report;
- `DEMO DATA` is readable without looking like a watermark over the table.

- [ ] **Step 4: Run the focused image-contract test**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_readme_showcase_is_exact_sanitized_png_and_linked -v
```

Expected: still `FAIL`, now only because README does not yet contain the image reference.

## Task 4: Add the Showcase to the English README

**Files:**
- Modify: `README.md`
- Test: `tests/test_public_asset.py`

**Interfaces:**
- Consumes: tracked `assets/readme/report-showcase.png`.
- Produces: one relative Markdown image reference with English-only alt text.

- [ ] **Step 1: Insert the image after the introductory platform paragraph**

After `EchoTik is the bundled default primary platform. Amazon remains a required supplementary source.`, add exactly:

```markdown
![Sanitized cross-border e-commerce daily report showcase](assets/readme/report-showcase.png)

*Sanitized demonstration data. No live account, product, or sales records are included.*
```

- [ ] **Step 2: Run focused public-asset tests**

Run:

```powershell
python -m unittest tests.test_public_asset.PublicSkillGuidanceTests.test_readme_showcase_is_exact_sanitized_png_and_linked -v
python -m unittest tests.test_public_asset -v
```

Expected: both commands pass.

- [ ] **Step 3: Commit the final visual asset and README integration**

```powershell
git add -- assets/readme/report-showcase.png README.md
git commit -m "docs: add sanitized report showcase"
```

## Task 5: Final Privacy, Visual, and Repository Verification

**Files:**
- Verify: `assets/readme/report-showcase.png`
- Verify: `README.md`
- Verify: `tests/test_public_asset.py`
- Verify: entire tracked repository

**Interfaces:**
- Consumes: completed public image change.
- Produces: evidence that the asset is accurate, private-data-free, portable, and repository-safe.

- [ ] **Step 1: Run all fresh automated checks**

Run:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q scripts tests
git diff --check HEAD~2..HEAD
```

Run the installed Skill validator using the portable `CODEX_HOME` or `$HOME/.codex` resolution already documented by the repository. Expected: all tests pass, compileall exits `0`, diff check is clean, and Skill validation reports valid.

- [ ] **Step 2: Scan tracked files and PNG structure**

Confirm:

- no tracked private absolute paths;
- no credentials, cookies, tokens, browser profiles, private reports, or temporary XLSX files;
- no forbidden generated directories or cache files;
- the PNG has no `tEXt`, `zTXt`, `iTXt`, or `eXIf` chunks;
- the final image contains no real account, store, product, or sales information.

The scan must report filenames and counts only; do not echo any matched secret-like text.

- [ ] **Step 3: Perform the final visual pass**

Inspect the 1920×1080 image at original size and at README thumbnail size. Compare it against the approved design specification and the packaged template. Record facts separately from assumptions and unresolved limitations.

- [ ] **Step 4: Confirm repository state and hand off without pushing**

Run:

```powershell
git status --short --branch
git log -3 --oneline
```

Expected: clean worktree; local `main` ahead of `origin/main`; no push performed. Report the final image path, commits, exact check results, and the next optional phase: GitHub social preview design.
