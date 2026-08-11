from __future__ import annotations

import json
from functools import lru_cache
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from .config import AmazonCategory


def _first_element(item, selectors: tuple[str, ...]):
    for selector in selectors:
        element = item.query_selector(selector)
        if element is not None:
            return element
    return None


def _has_human_challenge(page) -> bool:
    text = page.locator("body").inner_text().lower()
    return any(
        marker in text
        for marker in (
            "enter the characters you see below",
            "robot check",
            "sorry, we just need to make sure you're not a robot",
            "captcha",
            "人工验证",
        )
    )


@lru_cache(maxsize=2048)
def translate_amazon_title_to_chinese(title: str) -> str:
    """Translate the complete Amazon title to Chinese."""
    normalized = " ".join(str(title or "").split())
    if not normalized:
        return ""
    query = urlencode(
        {"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "q": normalized}
    )
    request = Request(
        f"https://translate.googleapis.com/translate_a/single?{query}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    translated = "".join(part[0] for part in payload[0] if part and part[0]).strip()
    if not translated:
        raise RuntimeError(f"Amazon 中文全称翻译为空: {normalized}")
    return translated


def scrape_amazon(context, categories: tuple[AmazonCategory, ...]) -> pd.DataFrame:
    """Collect the configured Amazon category pages."""
    products: list[dict] = []
    page = context.new_page()
    try:
        for category in categories:
            try:
                page.goto(
                    category.url,
                    wait_until="domcontentloaded",
                    timeout=20_000,
                )
                page.wait_for_timeout(1_500)
                if _has_human_challenge(page):
                    raise RuntimeError("Amazon 出现人工验证，已停止采集")
                items = page.query_selector_all("div.p13n-sc-uncoverable-faceout")
                if not items:
                    items = page.query_selector_all("[id*='zg-immersive']")
                if not items:
                    items = page.query_selector_all(
                        "[data-component-type='s-search-result']"
                    )
                for item in items[:15]:
                    try:
                        name_element = _first_element(
                            item,
                            (
                                "div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1",
                                "div[class*='p13n-sc-truncate']",
                                "h2 a span",
                            ),
                        )
                        name = name_element.inner_text().strip() if name_element else ""
                        price_element = _first_element(
                            item,
                            (
                                "span._cDEzb_p13n-sc-price_3mJ9Z",
                                "span.a-price span.a-offscreen",
                            ),
                        )
                        price_text = price_element.inner_text().strip() if price_element else "0"
                        price = float(
                            price_text.replace("$", "").replace(",", "").split("-")[0]
                        )
                        rating_element = item.query_selector("span.a-icon-alt")
                        rating = (
                            float(rating_element.inner_text().split()[0])
                            if rating_element
                            else 0
                        )
                        reviews_element = _first_element(
                            item,
                            (
                                "span.a-size-small",
                                "span.a-size-base.s-underline-text",
                            ),
                        )
                        reviews_text = (
                            reviews_element.inner_text().replace(",", "")
                            if reviews_element
                            else "0"
                        )
                        reviews = int(reviews_text) if reviews_text.isdigit() else 0
                        if name:
                            products.append(
                                {
                                    "source": "Amazon",
                                    "category": category.name,
                                    "name": name,
                                    "price": price,
                                    "rating": rating,
                                    "reviews": reviews,
                                }
                            )
                    except (AttributeError, TypeError, ValueError):
                        continue
            except RuntimeError:
                raise
            except Exception as error:
                raise RuntimeError(
                    f"Amazon 类目导航失败: {category.name}"
                ) from error
    finally:
        page.close()
    return pd.DataFrame(products)
