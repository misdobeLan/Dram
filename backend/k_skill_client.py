"""Korean Stock Search (k-skill-proxy) 客户端。

API 文档: https://github.com/NomaDamas/k-skill/blob/main/docs/features/korean-stock-search.md
Proxy: https://k-skill-proxy.nomadamas.org/v1/korean-stock
"""
import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta

from futu_client import Quote

logger = logging.getLogger(__name__)

BASE_URL = "https://k-skill-proxy.nomadamas.org/v1/korean-stock"


@dataclass
class KSkillQuote(Quote):
    market: str = ""
    krx_code: str = ""


def _last_krx_trading_day(date: datetime) -> datetime:
    """返回不超过给定日期的最近一个 KRX 交易日（仅处理周末，不处理节假日）。"""
    while date.weekday() >= 5:  # 周六=5, 周日=6
        date -= timedelta(days=1)
    return date


def _today_kr() -> str:
    # KRX bas_dd 格式 YYYYMMDD，使用亚洲/首尔时区；周末回退到最近交易日
    tz = __import__("zoneinfo", fromlist=["ZoneInfo"]).ZoneInfo("Asia/Seoul") if hasattr(__import__("zoneinfo", fromlist=["ZoneInfo"]), "ZoneInfo") else None
    if tz:
        now = datetime.now(tz)
    else:
        now = datetime.utcnow() + timedelta(hours=9)
    return _last_krx_trading_day(now).strftime("%Y%m%d")


def _get_json(path: str, params: dict) -> dict | None:
    url = f"{BASE_URL}/{path}?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 404 通常是市场/日期不存在，属于预期内的探测结果，降级为 info 避免日志噪音
        level = logging.INFO if e.code == 404 else logging.WARNING
        logger.log(level, f"k-skill HTTP error: {e.code} for {path}: {e.read().decode('utf-8', errors='ignore')[:200]}")
        return None
    except Exception as e:
        logger.warning(f"k-skill request failed for {path}: {e}")
        return None


def search_stock(query: str, bas_dd: str | None = None) -> list[dict]:
    """按名称搜索 KRX 上市股票。"""
    data = _get_json("search", {"q": query, "bas_dd": bas_dd or _today_kr(), "limit": 10})
    if not data:
        return []
    return data.get("items", [])


def get_base_info(market: str, code: str, bas_dd: str | None = None) -> dict | None:
    """获取股票基本信息。"""
    data = _get_json("base-info", {"market": market, "code": code, "bas_dd": bas_dd or _today_kr()})
    if not data:
        return None
    return data.get("item") or (data.get("items")[0] if data.get("items") else None)


def get_trade_info(market: str, code: str, bas_dd: str | None = None) -> KSkillQuote | None:
    """获取股票日终行情（收盘/涨跌等）。若 proxy 返回 401 或其他错误则返回 None。"""
    data = _get_json("trade-info", {"market": market, "code": code, "bas_dd": bas_dd or _today_kr()})
    if not data:
        return None

    item = data.get("item") or (data.get("items")[0] if data.get("items") else None)
    if not item:
        return None

    # 尝试多种可能的字段名（proxy 可能做不同标准化）
    def _get(*keys):
        for k in keys:
            v = item.get(k)
            if v is not None and v != "":
                try:
                    return float(str(v).replace(",", ""))
                except (ValueError, TypeError):
                    continue
        return None

    price = _get("close", "TDD_CLSPRC", "clpr", "close_price", "종가")
    open_ = _get("open", "TDD_OPNPRC", "oppr", "open_price", "시가")
    high = _get("high", "TDD_HGPRC", "hgpr", "high_price", "고가")
    low = _get("low", "TDD_LWPRC", "lwpr", "low_price", "저가")
    prev_close = _get("previous_close", "prev_close", "prev_clpr", "전일종가")
    change_pct = _get("change_rate", "fluc_rt", "FLUC_RT", "등락률")
    volume = _get("volume", "ACC_TRDVOL", "acc_trdvol", "거래량")

    if price is None:
        return None

    if change_pct is None and prev_close:
        change_pct = (price - prev_close) / prev_close * 100

    name = item.get("name") or item.get("name_ko") or item.get("short_name") or item.get("ISU_NM") or ""

    return KSkillQuote(
        code=code,
        name=name,
        price=price,
        open=open_,
        prev_close=prev_close,
        change=price - prev_close if prev_close else None,
        change_pct=change_pct,
        volume=int(volume) if volume is not None else None,
        update_time=item.get("bas_dd") or _today_kr(),
        valid=True,
        market=market,
        krx_code=code,
    )


def fetch_korean_quote(ticker: str) -> Quote | None:
    """根据原始 ticker（如 000660.KS）获取韩国股票行情。
    先尝试 k-skill trade-info，失败则返回 None（由上层再回退 Yahoo）。
    """
    # 去掉 .KS/.KQ 后缀，并根据后缀推断市场，避免对错误市场发起 404 探测
    code = ticker.replace(".KS", "").replace(".KQ", "").strip()
    bas_dd = _today_kr()

    if ticker.endswith(".KS"):
        markets = ["KOSPI"]
    elif ticker.endswith(".KQ"):
        markets = ["KOSDAQ"]
    else:
        markets = ["KOSPI", "KOSDAQ"]

    for market in markets:
        base = get_base_info(market, code, bas_dd=bas_dd)
        if base:
            q = get_trade_info(market, code, bas_dd=bas_dd)
            if q:
                return q
    return None
