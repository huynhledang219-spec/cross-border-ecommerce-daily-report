from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from scripts.ecommerce_report.amazon import scrape_amazon, translate_amazon_title_to_chinese
from scripts.ecommerce_report.config import (
    DEFAULT_AMAZON_CATEGORIES,
    AmazonCategory,
    EchoTikCategory,
    RuntimeConfig,
)
from scripts.ecommerce_report.echotik import (
    ECHOTIK_ADAPTER,
    parse_echotik_row,
    scrape_echotik,
)
from scripts.ecommerce_report.platforms import PrimaryPlatformConfig
from scripts.ecommerce_report.trends import (
    TrendDataEmpty,
    read_7d_gmv_trend,
    select_top_detail_rows,
)


class FakeAmazonElement:
    def __init__(self, text: str) -> None:
        self.text = text

    def inner_text(self) -> str:
        return self.text


class FakeAmazonItem:
    VALUES = {
        "div._cDEzb_p13n-sc-css-line-clamp-3_g3dy1": "A complete product title",
        "span._cDEzb_p13n-sc-price_3mJ9Z": "$12.50",
        "span.a-icon-alt": "4.7 out of 5 stars",
        "span.a-size-small": "1,234",
    }

    def query_selector(self, selector: str):
        value = self.VALUES.get(selector)
        return FakeAmazonElement(value) if value is not None else None


class FakeAmazonPage:
    def __init__(self) -> None:
        self.navigations: list[str] = []
        self.waits: list[int] = []
        self.closed = False

    def goto(self, url: str, **_: object) -> None:
        self.navigations.append(url)

    def wait_for_timeout(self, duration: int) -> None:
        self.waits.append(duration)

    def query_selector_all(self, selector: str) -> list[FakeAmazonItem]:
        if selector == "div.p13n-sc-uncoverable-faceout":
            return [FakeAmazonItem()]
        return []

    def locator(self, selector: str):
        if selector != "body":
            raise AssertionError(selector)
        return FakeAmazonElement("")

    def close(self) -> None:
        self.closed = True


class FakeAmazonContext:
    def __init__(self) -> None:
        self.page = FakeAmazonPage()

    def new_page(self) -> FakeAmazonPage:
        return self.page


class FakeAmazonSearchItem(FakeAmazonItem):
    VALUES = {
        "h2 a span": "A search result complete title",
        "span.a-price span.a-offscreen": "$17.25",
        "span.a-icon-alt": "4.6 out of 5 stars",
        "span.a-size-base.s-underline-text": "987",
    }


class FakeAmazonSearchPage(FakeAmazonPage):
    def query_selector_all(self, selector: str) -> list[FakeAmazonItem]:
        if selector == "[data-component-type='s-search-result']":
            return [FakeAmazonSearchItem()]
        return []


class FailingAmazonNavigationPage(FakeAmazonPage):
    def goto(self, url: str, **_: object) -> None:
        raise TimeoutError("navigation timed out")


class FakeAmazonBody:
    def inner_text(self) -> str:
        return "Enter the characters you see below"


class ChallengedAmazonPage(FakeAmazonPage):
    def locator(self, selector: str) -> FakeAmazonBody:
        if selector != "body":
            raise AssertionError(selector)
        return FakeAmazonBody()


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps([[['完整', 'complete'], ['商品标题', 'product title']]]).encode("utf-8")


class FakeSwitch:
    def __init__(self, page: "FakeEchoTikPage") -> None:
        self.page = page

    def get_attribute(self, name: str) -> str | None:
        if name == "aria-checked":
            return "true" if self.page.translation_enabled else "false"
        return None

    def click(self, **_: object) -> None:
        self.page.translation_enabled = not self.page.translation_enabled


class FakeTextTarget:
    def __init__(self, page: "FakeEchoTikPage", text: str) -> None:
        self.page = page
        self.text = text

    @property
    def last(self) -> "FakeTextTarget":
        return self

    def hover(self, **_: object) -> None:
        self.page.category_actions.append(("hover", self.text))

    def click(self, **_: object) -> None:
        self.page.category_actions.append(("click", self.text))
        category_id = self.page.category_ids_by_final_label.get(self.text)
        if category_id is not None:
            self.page.url = f"https://echotik.live/products?product_categories={category_id}"


class FakeControl:
    def __init__(self, page: "FakeEchoTikPage", name: str) -> None:
        self.page = page
        self.name = name

    @property
    def first(self) -> "FakeControl":
        return self

    def check(self, **_: object) -> None:
        if self.page.failing_control == self.name:
            raise TimeoutError(f"{self.name} control did not become selectable")
        self.page.checked_controls.append(self.name)


class FakeCollection:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def all(self) -> list[object]:
        return self.values


class FakeTitleList:
    def __init__(self, page: "FakeEchoTikPage", row: dict) -> None:
        self.page = page
        self.row = row

    def all_inner_texts(self) -> list[str]:
        key = "translated" if self.page.translation_enabled else "title"
        return [self.row[key]]


class FakeLink:
    def __init__(self, href: str) -> None:
        self.href = href

    @property
    def first(self) -> "FakeLink":
        return self

    def get_attribute(self, name: str) -> str | None:
        return self.href if name == "href" else None


class FakeFirstCell:
    def __init__(self, page: "FakeEchoTikPage", row: dict) -> None:
        self.page = page
        self.row = row

    def locator(self, selector: str):
        if selector == "a .et-table-cell-title":
            return FakeTitleList(self.page, self.row)
        if selector == "a":
            return FakeLink(self.row["href"])
        raise AssertionError(f"unexpected first-cell selector: {selector}")


class FakeCells:
    def __init__(self, page: "FakeEchoTikPage", row: dict) -> None:
        self.page = page
        self.row = row

    @property
    def first(self) -> FakeFirstCell:
        return FakeFirstCell(self.page, self.row)

    def all_inner_texts(self) -> list[str]:
        return self.row["cells"]


class FakeRow:
    def __init__(self, page: "FakeEchoTikPage", row: dict) -> None:
        self.page = page
        self.row = row

    def locator(self, selector: str) -> FakeCells:
        if selector != "td":
            raise AssertionError(f"unexpected row selector: {selector}")
        return FakeCells(self.page, self.row)


class FakeRows:
    def __init__(self, page: "FakeEchoTikPage") -> None:
        self.page = page

    def count(self) -> int:
        return len(self.page.rows) + 1

    def nth(self, index: int) -> FakeRow:
        return FakeRow(self.page, self.page.rows[index - 1])


class FakeBody:
    def __init__(self, page: "FakeEchoTikPage") -> None:
        self.page = page

    def inner_text(self) -> str:
        return self.page.body_text


class FakeBars:
    def __init__(self, page: "FakeEchoTikPage") -> None:
        self.page = page

    @property
    def first(self) -> "FakeBars":
        return self

    def wait_for(self, **_: object) -> None:
        return None

    def evaluate_all(self, script: str) -> list[float | None]:
        if "bars.slice(-7)" in script:
            return self.page.trend_values[-7:]
        return self.page.trend_values


class FakeSales:
    def __init__(self, page: "FakeEchoTikPage") -> None:
        self.page = page

    def wait_for(self, **_: object) -> None:
        if self.page.missing_chart:
            raise TimeoutError("chart did not appear")
        return None

    def locator(self, selector: str) -> FakeBars:
        if selector != "path[name='日销售额']":
            raise AssertionError(f"unexpected chart selector: {selector}")
        return FakeBars(self.page)


class FakeEchoTikPage:
    def __init__(
        self,
        rows: list[dict],
        category_ids_by_final_label: dict[str, str],
        trend_values: list[float | None] | None = None,
        verification_on_detail: bool = False,
        verification_on_listing: bool = False,
        missing_chart: bool = False,
        failing_control: str | None = None,
    ) -> None:
        self.rows = rows
        self.category_ids_by_final_label = category_ids_by_final_label
        self.trend_values = trend_values or [1, 2, 3, 4, 5, 6, 7]
        self.verification_on_detail = verification_on_detail
        self.verification_on_listing = verification_on_listing
        self.missing_chart = missing_chart
        self.failing_control = failing_control
        self.url = ""
        self.body_text = ""
        self.translation_enabled = False
        self.category_actions: list[tuple[str, str]] = []
        self.checked_controls: list[str] = []
        self.navigations: list[str] = []
        self.waits: list[int] = []
        self.closed = False

    def goto(self, url: str, **_: object) -> None:
        self.url = url
        self.navigations.append(url)
        if "/product/" in url and self.verification_on_detail:
            self.body_text = "请完成验证"
        elif "/products" in url and self.verification_on_listing:
            self.body_text = "真人验证"
        else:
            self.body_text = ""

    def wait_for_timeout(self, duration: int) -> None:
        self.waits.append(duration)

    def get_by_text(self, text: str, **_: object) -> FakeTextTarget:
        return FakeTextTarget(self, text)

    def get_by_role(self, role: str, name: str | None = None, **_: object):
        if role == "switch":
            return FakeSwitch(self)
        if role == "radio" and name is not None:
            return FakeControl(self, name)
        raise AssertionError(f"unexpected role: {role} {name}")

    def locator(self, selector: str):
        if selector == ".arco-modal-wrapper":
            return FakeCollection([])
        if selector == "tr":
            return FakeRows(self)
        if selector == "body":
            return FakeBody(self)
        if selector == "#basic-sales":
            return FakeSales(self)
        raise AssertionError(f"unexpected page selector: {selector}")

    def close(self) -> None:
        self.closed = True


class FakeEchoTikContext:
    def __init__(self, page: FakeEchoTikPage) -> None:
        self.page = page
        self.created_pages = 0

    def new_page(self) -> FakeEchoTikPage:
        self.created_pages += 1
        return self.page


def echotik_row(index: int, gmv_7d: float) -> dict:
    return {
        "title": f"Kitchen product {index}",
        "translated": f"厨房商品 {index}",
        "href": f"/product/{index}",
        "cells": [
            f"Kitchen product {index}\n$12.50\n4.8\n120",
            "Example Shop",
            "10",
            str(gmv_7d),
            "-",
            "-",
            str(gmv_7d * 2),
            "3",
            "4",
        ],
    }


class SourceAndTrendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_config(
        self,
        echotik_categories: tuple[EchoTikCategory, ...],
        amazon_categories: tuple[AmazonCategory, ...] = (
            AmazonCategory("Books", "https://www.amazon.com/books"),
        ),
    ) -> RuntimeConfig:
        temporary_root = Path(self.temp_dir.name)
        return RuntimeConfig(
            output_dir=temporary_root / "reports",
            profile_dir=temporary_root / "profile",
            template_path=temporary_root / "template.xlsx",
            pages_per_category=1,
            echotik_categories=echotik_categories,
            amazon_categories=amazon_categories,
        )

    def test_amazon_scrape_iterates_only_supplied_non_pet_categories(self) -> None:
        categories = (
            AmazonCategory("Books", "https://www.amazon.com/books"),
            AmazonCategory("Kitchen", "https://www.amazon.com/kitchen"),
        )
        context = FakeAmazonContext()

        frame = scrape_amazon(context, categories)

        self.assertEqual(context.page.navigations, [category.url for category in categories])
        self.assertEqual(frame["category"].tolist(), ["Books", "Kitchen"])
        self.assertEqual(frame["name"].tolist(), ["A complete product title"] * 2)
        self.assertTrue(context.page.closed)

    def test_default_amazon_search_pages_use_search_result_selectors(self) -> None:
        """Keeping only bestseller selectors would make every bundled /s URL empty."""
        context = FakeAmazonContext()
        context.page = FakeAmazonSearchPage()

        frame = scrape_amazon(context, (DEFAULT_AMAZON_CATEGORIES[0],))

        self.assertFalse(frame.empty)
        self.assertEqual(frame["name"].tolist(), ["A search result complete title"])
        self.assertEqual(frame["price"].tolist(), [17.25])
        self.assertEqual(frame["reviews"].tolist(), [987])

    def test_amazon_navigation_failure_is_not_silently_returned_as_empty(self) -> None:
        """Continuing after every category navigation fails would publish a false success."""
        context = FakeAmazonContext()
        context.page = FailingAmazonNavigationPage()

        with self.assertRaisesRegex(RuntimeError, "Amazon 类目导航失败: Books"):
            scrape_amazon(
                context,
                (AmazonCategory("Books", "https://www.amazon.com/s?k=books"),),
            )

    def test_amazon_human_challenge_stops_collection(self) -> None:
        """Treating a CAPTCHA page as an empty category would conceal required user action."""
        context = FakeAmazonContext()
        context.page = ChallengedAmazonPage()

        with self.assertRaisesRegex(RuntimeError, "Amazon 出现人工验证"):
            scrape_amazon(
                context,
                (AmazonCategory("Books", "https://www.amazon.com/s?k=books"),),
            )

    def test_amazon_translation_sends_the_complete_normalized_title(self) -> None:
        requests = []

        def fake_urlopen(request, timeout: int):
            requests.append((request, timeout))
            return FakeResponse()

        with patch("scripts.ecommerce_report.amazon.urlopen", side_effect=fake_urlopen):
            translated = translate_amazon_title_to_chinese("  Complete   product title  ")

        self.assertEqual(translated, "完整商品标题")
        self.assertEqual(parse_qs(urlparse(requests[0][0].full_url).query)["q"], ["Complete product title"])
        self.assertEqual(requests[0][1], 20)

    def test_echotik_row_parser_converts_wan_and_yi_units(self) -> None:
        cells = [
            "Kitchen scale\n$12.50\n4.8\n1.2万",
            "Kitchen Shop",
            "2万",
            "$3.5万",
            "-",
            "-",
            "$1.2亿",
            "3万",
            "4万",
        ]

        record = parse_echotik_row(cells)

        self.assertEqual(record["price"], 12.5)
        self.assertEqual(record["reviews"], 12_000)
        self.assertEqual(record["sold_7d"], 20_000)
        self.assertEqual(record["gmv_7d"], 35_000)
        self.assertEqual(record["gmv"], 120_000_000)
        self.assertEqual(record["creators"], 30_000)
        self.assertEqual(record["videos"], 40_000)
        self.assertEqual(record["source"], "EchoTik")

    def test_read_7d_gmv_trend_selects_exact_controls_and_returns_exact_values(self) -> None:
        page = FakeEchoTikPage([], {}, trend_values=[10, 20.125, 30, 40, 50, 60, 70])

        values = read_7d_gmv_trend(page)

        self.assertEqual(values, [10.0, 20.12, 30.0, 40.0, 50.0, 60.0, 70.0])
        self.assertEqual(page.checked_controls, ["7 天", "销售额"])

    def test_read_7d_gmv_trend_rejects_any_series_other_than_seven_nonnegative_values(self) -> None:
        for values in (
            [1, 2, 3, 4, 5, 6],
            [1, 2, 3, 4, 5, 6, 7, 8],
            [1, 2, 3, 4, 5, 6, None],
            [1, 2, 3, 4, 5, 6, -1],
            [1, 2, 3, 4, 5, 6, "not-a-number"],
        ):
            with self.subTest(values=values):
                page = FakeEchoTikPage([], {}, trend_values=values)
                try:
                    read_7d_gmv_trend(page)
                except Exception as error:
                    self.assertIs(type(error), TrendDataEmpty)
                    self.assertEqual(str(error), "EchoTik 七天日销售额数据为空")
                else:
                    self.fail("invalid seven-day trend was accepted")

    def test_read_7d_gmv_trend_reports_a_missing_chart_as_an_operational_failure(self) -> None:
        page = FakeEchoTikPage([], {}, missing_chart=True)

        try:
            read_7d_gmv_trend(page)
        except Exception as error:
            self.assertIs(type(error), RuntimeError)
            self.assertEqual(str(error), "EchoTik 趋势图未能加载")
        else:
            self.fail("missing trend DOM was not reported")

    def test_read_7d_gmv_trend_keeps_control_failures_operational(self) -> None:
        for control_name in ("7 天", "销售额"):
            with self.subTest(control_name=control_name):
                page = FakeEchoTikPage([], {}, failing_control=control_name)

                try:
                    read_7d_gmv_trend(page)
                except Exception as error:
                    self.assertIs(type(error), RuntimeError)
                    self.assertEqual(str(error), "EchoTik 趋势控件操作失败")
                else:
                    self.fail("trend control failure was not reported")

    def test_top_selection_uses_the_selected_source(self) -> None:
        records = [
            {"source": "MarketPulse", "gmv_7d": 200},
            {"source": "EchoTik", "gmv_7d": 300},
            {"source": "MarketPulse", "gmv_7d": 100},
        ]

        selected = select_top_detail_rows(records, "MarketPulse", 20)

        self.assertEqual([row["gmv_7d"] for row in selected], [200, 100])

    def test_selects_only_twenty_echotik_details_by_7d_gmv(self) -> None:
        records = [
            {"source": "EchoTik", "gmv_7d": value, "detail_url": f"/product/{value}"}
            for value in range(25)
        ] + [
            {"source": "Amazon", "gmv_7d": 10_000 + value, "detail_url": f"/amazon/{value}"}
            for value in range(5)
        ]

        selected = select_top_detail_rows(records, "EchoTik")

        self.assertEqual(20, len(selected))
        self.assertTrue(all(row["source"] == "EchoTik" for row in selected))
        self.assertEqual(list(range(24, 4, -1)), [row["gmv_7d"] for row in selected])

    def test_select_top_details_never_exceeds_twenty_even_for_a_larger_limit(self) -> None:
        records = [
            {"source": "EchoTik", "gmv_7d": value, "detail_url": f"/product/{value}"}
            for value in range(30)
        ]

        self.assertEqual(20, len(select_top_detail_rows(records, "EchoTik", limit=100)))

    def test_top_twenty_is_fixed_before_missing_detail_urls_are_examined(self) -> None:
        """Filtering missing URLs first would incorrectly substitute the twenty-first item."""
        records = [
            {
                "source": "EchoTik",
                "gmv_7d": value,
                "detail_url": None if value == 25 else f"/product/{value}",
            }
            for value in range(25, 4, -1)
        ]

        selected = select_top_detail_rows(records, "EchoTik")

        self.assertEqual([row["gmv_7d"] for row in selected], list(range(25, 5, -1)))
        self.assertIsNone(selected[0]["detail_url"])
        self.assertNotIn(5, [row["gmv_7d"] for row in selected])

    def test_echotik_scrape_traverses_non_pet_path_and_opens_at_most_twenty_details(self) -> None:
        category = EchoTikCategory(("Home & Garden", "Kitchen", "Bakeware"), "123456")
        page = FakeEchoTikPage(
            [echotik_row(index, float(index)) for index in range(25)],
            {"Bakeware": category.category_id},
        )
        context = FakeEchoTikContext(page)

        frame = scrape_echotik(context, self.make_config((category,)))

        self.assertEqual(
            page.category_actions,
            [("hover", "Home & Garden"), ("hover", "Kitchen"), ("click", "Bakeware")],
        )
        self.assertEqual(frame["category"].unique().tolist(), ["Bakeware"])
        detail_navigations = [url for url in page.navigations if "/product/" in url]
        self.assertEqual(20, len(detail_navigations))
        self.assertEqual(detail_navigations[0], "https://echotik.live/product/24")
        self.assertEqual(context.created_pages, 1)
        self.assertTrue(page.closed)

    def test_echotik_adapter_collects_from_platform_config(self) -> None:
        page = FakeEchoTikPage(
            [echotik_row(1, 10.0)],
            {"Kitchen": "123456"},
        )
        config = PrimaryPlatformConfig(
            adapter="echotik",
            categories=({"path": ["Home", "Kitchen"], "id": "123456"},),
        )

        frame = ECHOTIK_ADAPTER.collect(
            FakeEchoTikContext(page),
            config,
            detail_limit=20,
            trend_days=7,
            pages_per_category=1,
        )

        self.assertEqual(frame["source"].tolist(), ["EchoTik"])
        self.assertEqual(frame["gmv_trend_7d"].tolist(), [[1, 2, 3, 4, 5, 6, 7]])

    def test_missing_url_in_frozen_top_twenty_is_data_empty_without_substitution(self) -> None:
        """Opening the next-ranked URL would make collection and workbook Top identities diverge."""
        category = EchoTikCategory(("Home", "Kitchen"), "123456")
        rows = [echotik_row(value, float(value)) for value in range(25, 4, -1)]
        rows[0]["href"] = None
        page = FakeEchoTikPage(rows, {"Kitchen": category.category_id})

        frame = scrape_echotik(
            FakeEchoTikContext(page), self.make_config((category,))
        )

        top_missing = frame.loc[frame["gmv_7d"] == 25].iloc[0]
        self.assertIn("diagnostic", top_missing.index)
        self.assertEqual(top_missing["diagnostic"], "数据为空")
        detail_navigations = [url for url in page.navigations if "/product/" in url]
        self.assertEqual(len(detail_navigations), 19)
        self.assertNotIn("https://echotik.live/product/5", detail_navigations)

    def test_echotik_scrape_requires_an_exact_selected_category_id(self) -> None:
        category = EchoTikCategory(("Home", "Kitchen"), "123456")
        page = FakeEchoTikPage([], {"Kitchen": "1234567"})

        with self.assertRaisesRegex(RuntimeError, "Home > Kitchen"):
            scrape_echotik(FakeEchoTikContext(page), self.make_config((category,)))

    def test_echotik_scrape_stops_all_details_when_human_verification_appears(self) -> None:
        category = EchoTikCategory(("Home", "Kitchen"), "123456")
        page = FakeEchoTikPage(
            [echotik_row(index, float(index)) for index in range(3)],
            {"Kitchen": category.category_id},
            verification_on_detail=True,
        )

        with self.assertRaisesRegex(RuntimeError, "EchoTik 出现人工验证"):
            scrape_echotik(FakeEchoTikContext(page), self.make_config((category,)))

        self.assertEqual(1, len([url for url in page.navigations if "/product/" in url]))
        self.assertTrue(page.closed)

    def test_echotik_only_converts_the_dedicated_empty_trend_exception(self) -> None:
        """Catching every ValueError would disguise selector and parser defects as empty data."""
        category = EchoTikCategory(("Home", "Kitchen"), "123456")
        page = FakeEchoTikPage(
            [echotik_row(1, 10.0)],
            {"Kitchen": category.category_id},
        )

        with patch(
            "scripts.ecommerce_report.echotik.read_7d_gmv_trend",
            side_effect=ValueError("unexpected parser defect"),
        ):
            with self.assertRaisesRegex(ValueError, "unexpected parser defect"):
                scrape_echotik(
                    FakeEchoTikContext(page), self.make_config((category,))
                )

    def test_echotik_listing_challenge_stops_before_category_actions(self) -> None:
        """Treating a challenged listing as an empty category would hide user action."""
        category = EchoTikCategory(("Home", "Kitchen"), "123456")
        page = FakeEchoTikPage(
            [],
            {"Kitchen": category.category_id},
            verification_on_listing=True,
        )

        with self.assertRaisesRegex(RuntimeError, "EchoTik 出现人工验证"):
            scrape_echotik(FakeEchoTikContext(page), self.make_config((category,)))

        self.assertEqual(page.category_actions, [])


if __name__ == "__main__":
    unittest.main()
