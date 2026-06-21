"""K-skill (Korean Stock Search) 集成测试。

当前代理的 KRX 实时行情接口因上游 401 无法使用，因此测试重点验证：
1. 搜索接口可用；
2. k-skill 失败时系统能优雅回退到 Yahoo Finance；
3. 韩国持仓仍能通过回退拿到有效行情。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest

from config import HOLDINGS
from fallback_client import fetch_quote, fetch_yahoo_quote
from k_skill_client import search_stock, fetch_korean_quote


KOREAN_HOLDINGS = [h for h in HOLDINGS if h.get("market") == "Korea"]


# k-skill 当前数据最新日期约为 2025-06-19，使用一个已知有数据的日期做搜索测试。
_KNOWN_GOOD_BAS_DD = "20250619"


def test_search_stock_finds_samsung():
    """k-skill 搜索应能找到 Samsung Electronics。"""
    items = search_stock("삼성전자", bas_dd=_KNOWN_GOOD_BAS_DD)
    codes = {item.get("code") for item in items}
    assert "005930" in codes, f"expected 005930 in search results, got {codes}"


def test_search_stock_finds_sk_hynix():
    """k-skill 搜索应能找到 SK hynix。"""
    items = search_stock("SK하이닉스", bas_dd=_KNOWN_GOOD_BAS_DD)
    codes = {item.get("code") for item in items}
    assert "000660" in codes, f"expected 000660 in search results, got {codes}"


def test_search_stock_returns_empty_for_future_date():
    """对代理没有数据的未来日期，搜索应返回空列表且不抛异常。"""
    items = search_stock("005930", bas_dd="20991231")
    assert items == []


def test_fetch_korean_quote_gracefully_fails_on_upstream_error():
    """当 k-skill 行情接口异常时，fetch_korean_quote 应返回 None 而不抛异常。"""
    result = fetch_korean_quote("005930.KS")
    # 代理目前返回 401/502，因此返回 None 是可接受的；若接口恢复，则应为有效行情
    assert result is None or result.valid


def test_fetch_quote_falls_back_to_yahoo_when_k_skill_fails():
    """k-skill 不可用时，fetch_quote 应回退到 Yahoo Finance 并返回有效行情。"""
    samsung = next(h for h in KOREAN_HOLDINGS if h["ticker"] == "005930.KS")
    quote = fetch_quote(samsung["ticker"], samsung["yahoo_ticker"])
    assert quote is not None
    assert quote.valid
    assert quote.price is not None
    assert quote.price > 0
    # 数据源可以是 k-skill 或 yahoo，只要有效即可
    assert quote.source in ("k-skill", "yahoo")


@pytest.mark.parametrize("holding", KOREAN_HOLDINGS)
def test_korean_holding_has_fallback_quote(holding):
    """每只韩国持仓都能通过回退机制拿到行情。"""
    quote = fetch_quote(holding["ticker"], holding["yahoo_ticker"])
    assert quote is not None, f"no quote for {holding['ticker']}"
    assert quote.valid, f"invalid quote for {holding['ticker']}"
    assert quote.price is not None and quote.price > 0
    assert quote.change_pct is not None


def test_yahoo_quote_alone_works_for_korean_tickers():
    """即使完全不使用 k-skill，Yahoo Finance 也能提供韩国股票行情。"""
    sk = next(h for h in KOREAN_HOLDINGS if h["ticker"] == "000660.KS")
    quote = fetch_yahoo_quote(sk["yahoo_ticker"])
    assert quote is not None
    assert quote.valid
    assert quote.price is not None and quote.price > 0
