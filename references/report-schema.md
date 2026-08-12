# Report schema and verification

## Output contract

- Format: `.xlsx` created from the bundled sanitized `assets/report-template.xlsx`, whose header, inventory row, alternating product-row styles, column widths, hidden helper columns, row heights, and chart extent mirror the `2026.8.11` reference layout without retaining its business data.
- Default filename: `YYYY.M.D数据报表.xlsx` in the configured local output directory.
- Template safety: output must be a different path from the asset. Never overwrite or modify `assets/report-template.xlsx`.
- Active-sheet columns, in order:

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
  14. `EchoTik详情链接`
  15. `诊断`

- Keep the EchoTik detail-link column hidden. Store chart helper values in seven hidden columns named `趋势日1` through `趋势日7`.
- Preserve template styling and row dimensions, freeze the header at `A2`, and keep the filter over the 15 public columns.

## Top 20 and seven-day charts

- Rank EchoTik candidates by `7天GMV` and mark no more than 20 as `Top 1` through `Top 20`.
- Open product-detail pages only for those selected rows and never for more than 20 rows in one run.
- On each selected EchoTik detail page, explicitly choose `7 天` and `销售额`; accept only seven finite, nonnegative daily values.
- Create one line chart for each selected row with a complete seven-value trend. Charts must remain visible while their helper cells are hidden.
- If the seven-day sales-amount trend is missing or invalid, put `数据为空` in `诊断` and do not fabricate values or a chart.
- A human-verification page ends detail-page processing; it is not an empty-data result.

## Required post-run verification

Set `$reportOutput` to the actual XLSX path, then run this read-only inspection from the Skill root:

```powershell
python -c "from pathlib import Path; from scripts.ecommerce_report.workbook import verify_report; print(verify_report(Path(r'$reportOutput')))"
```

`verify_report` raises a concise `ValueError` when any gate fails. Report success only when it returns an inspection and all checks pass:

1. The file opens as XLSX without a repair warning, and the bundled template still exists unchanged.
2. `headers` exactly match the 15-column contract above.
3. EchoTik Top labels are unique, contiguous from `Top 1`, sorted by descending `7天GMV`, and number at most 20.
4. Every Top row has either one complete seven-day sales-amount chart or `诊断 = 数据为空`; no non-Top row has a trend chart.
5. `chart_count` is at most 20, all `visible_cells_only` values are false, and chart extents are consistent with the template.
6. Hidden columns include `EchoTik详情链接` and all seven `趋势日` helper columns.
7. `formula_errors` is empty. Source rows retain the intended order when present: `你的库存`, `echotik`, then `Amazon`.
8. Amazon titles retain their complete original text and a nonempty complete Chinese translation when a title exists.
9. The workbook and its ZIP parts contain no credentials, cookies, tokens, account identifiers, browser-profile content, local profile paths, or leftover sample/test data. Product URLs and report data are allowed. This is the sanitized-XLSX gate.
10. The output is outside the Skill directory. No credential, browser profile, local config, generated report, or failure record was added to the Skill or staged for commit.

If any check fails, report verification failure and the failed check concisely. Do not call the workbook complete, distribute it, or install the schedule until verification passes.
