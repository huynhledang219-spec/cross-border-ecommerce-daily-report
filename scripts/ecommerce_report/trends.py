from __future__ import annotations


_EMPTY_TREND_MESSAGE = "EchoTik 七天日销售额数据为空"


class TrendDataEmpty(ValueError):
    """The requested chart loaded, but did not contain one valid seven-day series."""


def read_7d_gmv_trend(page) -> list[float]:
    """Select EchoTik's seven-day sales-amount chart and read its daily values."""
    try:
        sales = page.locator("#basic-sales")
        sales.wait_for(state="visible", timeout=15_000)
    except Exception as error:
        raise RuntimeError("EchoTik 趋势图未能加载") from error
    try:
        page.get_by_role("radio", name="7 天", exact=True).first.check(timeout=15_000)
        page.wait_for_timeout(3_000)
        page.get_by_role("radio", name="销售额", exact=True).first.check(timeout=15_000)
        page.wait_for_timeout(3_000)
    except Exception as error:
        raise RuntimeError("EchoTik 趋势控件操作失败") from error
    try:
        daily_bars = sales.locator("path[name='日销售额']")
        daily_bars.first.wait_for(state="visible", timeout=15_000)
        values = daily_bars.evaluate_all(
            """bars => bars.map(node => {
                const fiberKey = Object.keys(node).find(key => key.startsWith('__reactFiber'));
                let fiber = fiberKey ? node[fiberKey] : null;
                for (let depth = 0; fiber && depth < 12; depth++, fiber = fiber.return) {
                    const props = fiber.memoizedProps || {};
                    if (props.dataKey === '日销售额' && Number.isFinite(Number(props.value))) {
                        return Number(props.value);
                    }
                }
                return null;
            })"""
        )
    except Exception as error:
        raise RuntimeError("EchoTik 趋势数据 DOM 读取失败") from error
    try:
        if len(values) != 7 or any(
            value is None or float(value) < 0 for value in values
        ):
            raise ValueError
        return [round(float(value), 2) for value in values]
    except (TypeError, ValueError) as error:
        raise TrendDataEmpty(_EMPTY_TREND_MESSAGE) from error


def select_top_detail_rows(records, limit: int = 20) -> list[dict]:
    """Freeze the top twenty EchoTik identities before checking detail URLs."""
    safe_limit = min(max(int(limit), 0), 20)
    candidates = [
        record
        for record in records
        if record.get("source") == "echotik"
    ]
    return sorted(
        candidates,
        key=lambda record: float(record.get("gmv_7d") or 0),
        reverse=True,
    )[:safe_limit]
