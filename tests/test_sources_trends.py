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
from scripts.ecommerce_report.platforms import (
    PrimaryPlatformConfig,
    validate_normalized_records,
)
from scripts.ecommerce_report.trends import (
    TrendDataEmpty,
    TrendDataInvalid,
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
        if self.page.translation_enabled and self.page.verification_on_translation:
            self.page.body_text = self.page.verification_on_translation


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
            if self.page.verification_after_category:
                self.page.body_text = self.page.verification_after_category


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
        if self.page.translation_enabled and self.page.pre_detail_challenge:
            self.page.pre_detail_challenge_ready = True
            if self.page.pre_detail_challenge == "login_url":
                self.page.url = "https://echotik.live/sign-in"
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
        if self.page.pre_detail_challenge_ready:
            if self.page.pre_detail_challenge == "login":
                return "Sign in to continue"
            if self.page.pre_detail_challenge == "captcha":
                return "Please complete the CAPTCHA"
        return self.page.body_text


class FakeFrame:
    def __init__(self, url: str) -> None:
        self.url = url


class FakeBars:
    def __init__(self, page: "FakeEchoTikPage") -> None:
        self.page = page

    @property
    def first(self) -> "FakeBars":
        return self

    def wait_for(self, **_: object) -> None:
        if self.page.failing_bar_wait:
            raise TimeoutError("daily bars did not become visible")
        if self.page.delayed_trend_values is not None:
            self.page.trend_values = self.page.delayed_trend_values
            self.page.delayed_trend_values = None
        return None

    def count(self) -> int:
        return len(self.page.trend_values)

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
        delayed_trend_values: list[float | None] | None = None,
        verification_on_detail: bool | str = False,
        verification_on_listing: bool | str = False,
        verification_after_category: str | None = None,
        verification_on_translation: str | None = None,
        pre_detail_challenge: str | None = None,
        missing_chart: bool = False,
        failing_control: str | None = None,
        failing_bar_wait: bool = False,
    ) -> None:
        self.rows = rows
        self.category_ids_by_final_label = category_ids_by_final_label
        self.trend_values = (
            [1, 2, 3, 4, 5, 6, 7]
            if trend_values is None
            else trend_values
        )
        self.verification_on_detail = verification_on_detail
        self.verification_on_listing = verification_on_listing
        self.verification_after_category = verification_after_category
        self.verification_on_translation = verification_on_translation
        self.pre_detail_challenge = pre_detail_challenge
        self.pre_detail_challenge_ready = False
        self.missing_chart = missing_chart
        self.failing_control = failing_control
        self.failing_bar_wait = failing_bar_wait
        self.delayed_trend_values = delayed_trend_values
        self.url = ""
        self.body_text = ""
        self.translation_enabled = False
        self.category_actions: list[tuple[str, str]] = []
        self.checked_controls: list[str] = []
        self.navigations: list[str] = []
        self.waits: list[int] = []
        self.closed = False

    @property
    def frames(self) -> list[FakeFrame]:
        if (
            self.pre_detail_challenge_ready
            and self.pre_detail_challenge == "frame"
        ):
            return [FakeFrame("https://www.google.com/recaptcha/api2/anchor")]
        return []

    def goto(self, url: str, **_: object) -> None:
        self.url = url
        self.navigations.append(url)
        if "/product/" in url and self.verification_on_detail:
            self.body_text = (
                "请完成验证"
                if self.verification_on_detail is True
                else str(self.verification_on_detail)
            )
        elif "/products" in url and self.verification_on_listing:
            self.body_text = (
                "真人验证"
                if self.verification_on_listing is True
                else str(self.verification_on_listing)
            )
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

    def test_read_7d_gmv_trend_treats_no_daily_bars_as_data_empty(self) -> None:
        page = FakeEchoTikPage([], {}, trend_values=[])

        with self.assertRaisesRegex(TrendDataEmpty, "数据为空"):
            read_7d_gmv_trend(page)

    def test_read_7d_gmv_trend_waits_for_slowly_rendered_bars(self) -> None:
        page = FakeEchoTikPage(
            [],
            {},
            trend_values=[],
            delayed_trend_values=[10, 20, 30, 40, 50, 60, 70],
        )

        self.assertEqual(
            read_7d_gmv_trend(page),
            [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0],
        )

    def test_read_7d_gmv_trend_keeps_bar_wait_failures_operational(self) -> None:
        page = FakeEchoTikPage([], {}, failing_bar_wait=True)

        with self.assertRaisesRegex(RuntimeError, "趋势数据 DOM 读取失败"):
            read_7d_gmv_trend(page)

    def test_read_7d_gmv_trend_rejects_malformed_series_as_operational(self) -> None:
        for values in (
            [1, 2, 3, 4, 5, 6],
            [1, 2, 3, 4, 5, 6, 7, 8],
            [1, 2, 3, 4, 5, 6, None],
            [1, 2, 3, 4, 5, 6, -1],
            [1, 2, 3, 4, 5, 6, "not-a-number"],
            [1, 2, 3, 4, 5, 6, float("nan")],
            [1, 2, 3, 4, 5, 6, float("inf")],
        ):
            with self.subTest(values=values):
                page = FakeEchoTikPage([], {}, trend_values=values)
                try:
                    read_7d_gmv_trend(page)
                except Exception as error:
                    self.assertIs(type(error), TrendDataInvalid)
                    self.assertEqual(str(error), "EchoTik 七天日销售额数据无效")
                else:
                    self.fail("malformed seven-day trend was accepted")

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
        self.assertEqual(
            frame["detail_url"].tolist(),
            ["https://echotik.live/product/1"],
        )
        self.assertEqual(frame["gmv_trend_7d"].tolist(), [[1, 2, 3, 4, 5, 6, 7]])
        validate_normalized_records(frame, "EchoTik")

    def test_echotik_adapter_rejects_unsafe_detail_urls(self) -> None:
        config = PrimaryPlatformConfig(
            adapter="echotik",
            categories=({"path": ["Home", "Kitchen"], "id": "123456"},),
        )
        for unsafe_url in (
            "javascript:alert(1)",
            "https:///product/1",
            "//attacker.example/product/1",
            "https://user:password@echotik.live/product/1",
            r"\attacker.example\product\1",
            r"\\attacker.example\product\1",
            r"/\attacker.example/product/1",
            r"https:\attacker.example\product\1",
            "/%5c%5cattacker.example/product/1",
        ):
            with self.subTest(unsafe_url=unsafe_url):
                row = echotik_row(1, 10.0)
                row["href"] = unsafe_url
                page = FakeEchoTikPage([row], {"Kitchen": "123456"})

                with self.assertRaisesRegex(RuntimeError, "商品详情链接不安全"):
                    ECHOTIK_ADAPTER.collect(
                        FakeEchoTikContext(page),
                        config,
                        detail_limit=20,
                        trend_days=7,
                        pages_per_category=1,
                    )

                self.assertEqual(
                    [url for url in page.navigations if "/product/" in url],
                    [],
                )

    def test_echotik_adapter_does_not_convert_malformed_trends_to_data_empty(self) -> None:
        page = FakeEchoTikPage(
            [echotik_row(1, 10.0)],
            {"Kitchen": "123456"},
            trend_values=[1, 2, 3, 4, 5, 6, float("nan")],
        )
        config = PrimaryPlatformConfig(
            adapter="echotik",
            categories=({"path": ["Home", "Kitchen"], "id": "123456"},),
        )

        with self.assertRaisesRegex(TrendDataInvalid, "数据无效"):
            ECHOTIK_ADAPTER.collect(
                FakeEchoTikContext(page),
                config,
                detail_limit=20,
                trend_days=7,
                pages_per_category=1,
            )

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

    def test_echotik_stops_before_detail_navigation_for_preexisting_challenges(self) -> None:
        category = EchoTikCategory(("Home", "Kitchen"), "123456")
        for challenge in ("login_url", "captcha", "frame"):
            with self.subTest(challenge=challenge):
                page = FakeEchoTikPage(
                    [echotik_row(1, 10.0)],
                    {"Kitchen": category.category_id},
                    pre_detail_challenge=challenge,
                )

                with self.assertRaisesRegex(RuntimeError, "EchoTik 出现人工验证"):
                    scrape_echotik(
                        FakeEchoTikContext(page), self.make_config((category,))
                    )

                self.assertEqual(
                    [url for url in page.navigations if "/product/" in url],
                    [],
                )

    def test_echotik_stops_after_english_challenge_on_detail_navigation(self) -> None:
        category = EchoTikCategory(("Home", "Kitchen"), "123456")
        page = FakeEchoTikPage(
            [echotik_row(1, 10.0)],
            {"Kitchen": category.category_id},
            verification_on_detail="Verify you are human",
        )

        with self.assertRaisesRegex(RuntimeError, "EchoTik 出现人工验证"):
            scrape_echotik(FakeEchoTikContext(page), self.make_config((category,)))

        self.assertEqual(
            [url for url in page.navigations if "/product/" in url],
            ["https://echotik.live/product/1"],
        )

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

    def test_echotik_category_challenge_stops_before_reading_products(self) -> None:
        category = EchoTikCategory(("Home", "Kitchen"), "123456")
        page = FakeEchoTikPage(
            [echotik_row(1, 10.0)],
            {"Kitchen": category.category_id},
            verification_after_category="Security check: verify you are human",
        )

        with self.assertRaisesRegex(RuntimeError, "EchoTik 出现人工验证"):
            scrape_echotik(FakeEchoTikContext(page), self.make_config((category,)))

        self.assertEqual(
            page.category_actions,
            [("hover", "Home"), ("click", "Kitchen")],
        )
        self.assertEqual(
            [url for url in page.navigations if "/product/" in url],
            [],
        )

    def test_echotik_translation_challenge_stops_even_when_no_rows_are_added(self) -> None:
        category = EchoTikCategory(("Home", "Kitchen"), "123456")
        row = echotik_row(1, 10.0)
        row["translated"] = ""
        page = FakeEchoTikPage(
            [row],
            {"Kitchen": category.category_id},
            verification_on_translation="Please complete the CAPTCHA",
        )

        with self.assertRaisesRegex(RuntimeError, "EchoTik 出现人工验证"):
            scrape_echotik(FakeEchoTikContext(page), self.make_config((category,)))

        self.assertEqual(
            [url for url in page.navigations if "/product/" in url],
            [],
        )


if __name__ == "__main__":
    unittest.main()
