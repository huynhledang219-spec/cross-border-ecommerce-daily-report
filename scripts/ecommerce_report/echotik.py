from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

import pandas as pd

from .config import RuntimeConfig
from .trends import read_7d_gmv_trend, select_top_detail_rows


_WAIT_DURATIONS = {
    "navigation": 5_000,
    "filter": 3_000,
    "pagination": 3_000,
    "detail": 5_000,
}


def _wait(page, stage: str) -> None:
    page.wait_for_timeout(_WAIT_DURATIONS[stage])


def _echotik_number(value) -> float:
    text = str(value or "").strip().replace(",", "")
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*([万亿]?)", text)
    if not match:
        return 0.0
    result = float(match.group(1))
    if match.group(2) == "万":
        result *= 10_000
    elif match.group(2) == "亿":
        result *= 100_000_000
    return result


def parse_echotik_row(
    cells: list[str],
    product_name: str | None = None,
    name_cn: str | None = None,
) -> dict:
    """Map one visible EchoTik product-table row to report fields."""
    if len(cells) < 9:
        raise ValueError("EchoTik 商品行缺少必要列")
    details = [line.strip() for line in str(cells[0]).splitlines() if line.strip()]
    if len(details) < 2:
        raise ValueError("EchoTik 商品名称或价格为空")
    price_line = next((line for line in details if line.startswith("$")), "")
    numeric_details = [
        line for line in details if re.fullmatch(r"\d+(?:\.\d+)?(?:万|亿)?", line)
    ]
    rating = _echotik_number(numeric_details[-2]) if len(numeric_details) >= 2 else 0.0
    reviews = int(_echotik_number(numeric_details[-1])) if numeric_details else 0
    original_title = (product_name or details[0]).strip()
    translated_title = (name_cn or "").strip()
    return {
        "source": "echotik",
        "name": original_title,
        "name_cn": translated_title,
        "raw_title": original_title,
        "raw_title_cn": translated_title,
        "price": _echotik_number(price_line),
        "rating": rating,
        "reviews": reviews,
        "gmv": _echotik_number(cells[6]),
        "gmv_7d": _echotik_number(cells[3]),
        "sold_7d": int(_echotik_number(cells[2])),
        "videos": int(_echotik_number(cells[8])),
        "creators": int(_echotik_number(cells[7])),
        "shop": str(cells[1]).splitlines()[0].strip(),
    }


def _extract_visible_title(title_texts: list[str]) -> str:
    for title in title_texts:
        if str(title).strip():
            return str(title).strip()
    raise ValueError("EchoTik 商品标题为空")


def _is_promotion_modal(text: str) -> bool:
    value = str(text or "")
    return "续费" in value or "会员倒计时" in value


def _dismiss_promotion_modal(page) -> None:
    for modal in page.locator(".arco-modal-wrapper").all():
        if _is_promotion_modal(modal.inner_text()):
            modal.evaluate("node => node.remove()")


def _set_bulk_translation(page, enabled: bool) -> None:
    switch = page.get_by_role("switch")
    checked = switch.get_attribute("aria-checked") == "true"
    if checked != enabled:
        _dismiss_promotion_modal(page)
        switch.click(timeout=15_000, force=True)
        _wait(page, "filter")
    if (switch.get_attribute("aria-checked") == "true") != enabled:
        raise RuntimeError("EchoTik 一键翻译开关未生效")


def _select_category(page, path: tuple[str, ...], category_id: str) -> None:
    for index, label in enumerate(path):
        target = page.get_by_text(label, exact=True)
        if index == len(path) - 1:
            target.click(timeout=15_000)
        else:
            target.hover(timeout=15_000)
        _wait(page, "filter")

    selected_ids = parse_qs(urlparse(page.url).query).get("product_categories", [])
    if selected_ids != [category_id]:
        raise RuntimeError("类目筛选未生效")


def _has_human_verification(page) -> bool:
    page_text = page.locator("body").inner_text()
    return "真人验证" in page_text or "请完成验证" in page_text


def scrape_echotik(context, config: RuntimeConfig) -> pd.DataFrame:
    """Collect configured EchoTik categories and enrich at most twenty details."""
    products: list[dict] = []
    page = context.new_page()
    try:
        for category in config.echotik_categories:
            page.goto(
                "https://echotik.live/products",
                wait_until="domcontentloaded",
                timeout=30_000,
            )
            _wait(page, "navigation")
            try:
                _dismiss_promotion_modal(page)
                _set_bulk_translation(page, False)
                _select_category(page, category.path, category.category_id)
            except Exception as error:
                visible_path = " > ".join(category.path)
                raise RuntimeError(
                    f"无法在 EchoTik 页面确认类目：{visible_path}"
                ) from error

            for page_number in range(1, config.pages_per_category + 1):
                _dismiss_promotion_modal(page)
                _set_bulk_translation(page, False)
                rows = page.locator("tr")
                row_count = rows.count()
                if row_count <= 1:
                    break

                page_rows: list[tuple[int, list[str], str, str | None]] = []
                for row_index in range(1, row_count):
                    row = rows.nth(row_index)
                    cells = row.locator("td").all_inner_texts()
                    try:
                        product_name = _extract_visible_title(
                            row.locator("td")
                            .first.locator("a .et-table-cell-title")
                            .all_inner_texts()
                        )
                    except ValueError:
                        continue
                    detail_url = (
                        row.locator("td").first.locator("a").first.get_attribute("href")
                    )
                    page_rows.append((row_index, cells, product_name, detail_url))

                _dismiss_promotion_modal(page)
                _set_bulk_translation(page, True)
                _wait(page, "filter")
                translated_titles: dict[int, str] = {}
                for row_index, _, _, _ in page_rows:
                    row = rows.nth(row_index)
                    try:
                        translated_titles[row_index] = _extract_visible_title(
                            row.locator("td")
                            .first.locator("a .et-table-cell-title")
                            .all_inner_texts()
                        )
                    except ValueError:
                        continue

                added = 0
                for row_index, cells, product_name, detail_url in page_rows:
                    translated_name = translated_titles.get(row_index)
                    if not translated_name:
                        continue
                    item = parse_echotik_row(cells, product_name, translated_name)
                    item["category"] = category.path[-1]
                    item["detail_url"] = detail_url
                    products.append(item)
                    added += 1

                if page_number == config.pages_per_category or added == 0:
                    break
                try:
                    page.get_by_text(str(page_number + 1), exact=True).last.click(
                        timeout=10_000
                    )
                    _wait(page, "pagination")
                except Exception:
                    break

        for product in select_top_detail_rows(products, config.detail_limit):
            detail_url = product["detail_url"]
            url = (
                detail_url
                if str(detail_url).startswith("http")
                else f"https://echotik.live{detail_url}"
            )
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            _wait(page, "detail")
            if _has_human_verification(page):
                raise RuntimeError("EchoTik 出现人工验证，已停止继续打开商品页面")
            try:
                product["gmv_trend_7d"] = read_7d_gmv_trend(page)
            except ValueError:
                product["diagnostic"] = "数据为空"
    finally:
        page.close()
    return pd.DataFrame(products)
