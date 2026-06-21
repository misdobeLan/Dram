"""验证 config.py 中韩国持仓已使用富途 SDK 支持的市场前缀。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from futu import Market
from config import HOLDINGS


def _market_prefix(code: str) -> str:
    if "." not in code:
        return ""
    return code.split(".", 1)[0]


def _find_holding(name_substring: str):
    for h in HOLDINGS:
        if name_substring.lower() in h["name"].lower():
            return h
    raise AssertionError(f"未找到持仓: {name_substring}")


def test_korean_holdings_use_supported_futu_markets():
    """SK hynix 与 Samsung Electronics 必须使用富途支持的市场前缀。"""
    sk = _find_holding("SK hynix")
    samsung = _find_holding("Samsung Electronics")

    for h in (sk, samsung):
        assert h["futu_codes"], f"{h['name']} 没有配置 futu_codes"
        for code in h["futu_codes"]:
            prefix = _market_prefix(code)
            assert Market.if_has_key(prefix), (
                f"{h['name']} 使用了富途不支持的市场前缀: '{prefix}' in '{code}'"
            )


def test_no_kr_market_prefix_in_korean_holdings():
    """韩国股票不再使用富途不支持的 KR 前缀。"""
    sk = _find_holding("SK hynix")
    samsung = _find_holding("Samsung Electronics")

    for h in (sk, samsung):
        for code in h["futu_codes"]:
            assert not code.startswith("KR."), (
                f"{h['name']} 仍包含无效的 KR 前缀: {code}"
            )


def test_korean_holdings_use_correct_us_otc_tickers():
    """验证已切换为富途可识别的美股场外代码。"""
    sk = _find_holding("SK hynix")
    samsung = _find_holding("Samsung Electronics")

    assert "US.HXSCF" in sk["futu_codes"], "SK hynix 应使用 US.HXSCF"
    assert "US.SSNLF" in samsung["futu_codes"], "Samsung Electronics 应使用 US.SSNLF"
