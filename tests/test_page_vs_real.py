"""页面展示数据与真实行情一致性测试。"""
import json
import re
import time
import urllib.request

import pytest


def _get_json(url: str):
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _is_connected(base_url: str) -> bool:
    try:
        data = _get_json(f"{base_url}/api/health")
        return data.get("connected", False)
    except Exception:
        return False


def _parse_price(text: str) -> float | None:
    if not text or text == "—":
        return None
    m = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


def _parse_change_pct(text: str) -> float | None:
    if not text or text == "—":
        return None
    m = re.search(r"[+-]?[\d,]+\.?\d*", text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


def test_page_etf_price_matches_real(backend_server, page):
    if not _is_connected(backend_server):
        pytest.skip("OpenD 未连接，无法获取真实行情数据")

    page.goto(backend_server)
    page.wait_for_selector("#etf-price", timeout=10000)
    # 等待至少一次行情更新
    time.sleep(4)

    page_price = _parse_price(page.locator("#etf-price").text_content())
    page_change = _parse_change_pct(page.locator("#etf-change").text_content())

    data = _get_json(f"{backend_server}/api/quote")
    etf_quote = next((q for q in data["quotes"] if "DRAM" in q["code"]), None)
    assert etf_quote is not None, "后端未返回 DRAM ETF 行情"

    real_price = etf_quote.get("price")
    real_change = etf_quote.get("change_pct")

    assert page_price is not None, "页面 ETF 价格未显示"
    assert real_price is not None, "后端 ETF 价格缺失"
    assert abs(page_price - real_price) < 0.02, (
        f"DRAM 价格不一致：页面={page_price}，真实={real_price}"
    )

    if real_change is not None:
        assert page_change is not None, "页面 ETF 涨跌幅未显示"
        assert abs(page_change - real_change) < 0.06, (
            f"DRAM 涨跌幅不一致：页面={page_change}%，真实={real_change}%"
        )


def test_page_holdings_match_real(backend_server, page):
    if not _is_connected(backend_server):
        pytest.skip("OpenD 未连接，无法获取真实行情数据")

    page.goto(backend_server)
    page.wait_for_selector("[data-ticker]", timeout=10000)
    time.sleep(4)

    data = _get_json(f"{backend_server}/api/quote")
    real_quotes = {q["code"]: q for q in data["quotes"]}

    errors = []
    rows = page.locator("[data-ticker]").all()
    for row in rows:
        ticker = row.get_attribute("data-ticker")
        quote = None
        for q in real_quotes.values():
            if any(part in q["code"] for part in ticker.replace(" ", "/").split("/") if part):
                quote = q
                break
        if not quote:
            continue

        page_price = _parse_price(row.locator(".rt-price").text_content())
        page_change = _parse_change_pct(row.locator(".rt-change").text_content())
        real_price = quote.get("price")
        real_change = quote.get("change_pct")

        if real_price is not None and page_price is not None:
            if abs(page_price - real_price) >= 0.02:
                errors.append(f"{ticker} 价格不一致：页面={page_price}，真实={real_price}")
        if real_change is not None and page_change is not None:
            if abs(page_change - real_change) >= 0.06:
                errors.append(f"{ticker} 涨跌幅不一致：页面={page_change}%，真实={real_change}%")

    assert not errors, "持仓数据不一致：\n" + "\n".join(errors)
