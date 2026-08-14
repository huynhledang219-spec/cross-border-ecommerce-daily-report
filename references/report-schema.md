# Report schema and verification

## Normalized record contract

Every registered primary product-intelligence adapter must satisfy this normalized record contract before workbook export:

- Source label
- Complete original product title
- Complete Chinese product title
- Category
- Price in USD
- Product rating
- Review count
- Total GMV
- Seven-day GMV
- Seven-day sales volume
- Related video count
- Related creator count
- Product detail URL
- Optional seven-value daily sales-amount trend
- Concise diagnostic state

Missing required list-level fields fail the run. Accept an optional trend only when it contains exactly seven finite, nonnegative daily sales-amount values. Represent only a genuinely empty trend with `数据为空`; never use that diagnostic for navigation, controls, DOM changes, authentication, or human-verification failures.

## XLSX output contract

- Create `.xlsx` output from the bundled sanitized `assets/report-template.xlsx`.
- Preserve the reference layout: header, inventory row, alternating product-row styles, column widths, row heights, hidden helper columns, chart placement, freeze pane, and filter range.
- Use the default filename `YYYY.M.D数据报表.xlsx` in the configured local output directory.
- Write to a path outside the Skill directory. Never overwrite or modify the packaged template.
- Keep these 15 columns in order:

  1. `排名`
  2. `近7天重点选品`
  3. `来源`
  4. `品名关键词`
  5. `中文名称`
  6. `价格(USD)`
  7. `商品评分`
  8. `评论数`
  9. `GMV`
  10. `7天GMV`
  11. `7天销量`
  12. `关联视频`
  13. `关联达人`
  14. `商品详情链接`
  15. `诊断`

- Keep `商品详情链接` hidden. Store chart helper values in seven hidden columns named `趋势日1` through `趋势日7`.
- Freeze the header at `A2` and keep the filter over the 15 public columns.

## Top 20 and seven-day trends

These rules remain unchanged across registered adapters:

1. Rank only the configured primary platform's candidates by descending seven-day GMV.
2. Freeze no more than 20 identities as `Top 1` through `Top 20` before checking detail links.
3. Open detail pages only for those frozen identities and never open more than 20 in one run.
4. Select the platform's exact seven-day sales-amount view and accept exactly seven valid daily values.
5. Create one line chart for every Top row with a complete trend. Keep charts visible while hiding helper cells.
6. Put `数据为空` in `诊断` and omit the chart only when the selected product genuinely has no trend data.
7. Stop the run on human verification. Never convert a challenge into empty trend data.

Order source groups as inventory, the configured primary platform display name, then Amazon. Amazon remains required. Store complete original Amazon titles and nonempty complete Chinese translations.

## Required post-run verification

Set `$reportOutput` to the actual XLSX path, then run this read-only inspection from the Skill root:

```powershell
python -c "from pathlib import Path; from scripts.ecommerce_report.workbook import verify_report; print(verify_report(Path(r'$reportOutput')))"
```

`verify_report` raises a concise `ValueError` when a gate fails. Report success only when it returns an inspection and every check passes:

1. The file opens without a repair warning, and the packaged template remains unchanged.
2. `headers` exactly match the 15-column contract.
3. Top labels are unique, contiguous from `Top 1`, sorted by descending seven-day GMV, and number at most 20.
4. Every Top row has either one complete seven-day chart or `诊断 = 数据为空`; no non-Top row has a trend chart.
5. `chart_count` is at most 20, helper cells are hidden, and chart extents match the template.
6. Hidden columns include `商品详情链接` and all seven trend-helper columns.
7. `formula_errors` is empty. Source groups appear only in the required inventory, primary-platform, Amazon order.
8. Amazon titles retain complete original text and complete Chinese translations.
9. The workbook and every XLSX ZIP part contain no credentials, cookies, tokens, account identifiers, browser-profile content, local profile paths, or leftover sample data. Product URLs and report data are allowed.
10. No local configuration, credential, browser profile, generated report, or failure record was added to the Skill or staged for commit.

If any check fails, report the failed gate concisely. Do not call the workbook complete, distribute it, or install the schedule until verification passes.
