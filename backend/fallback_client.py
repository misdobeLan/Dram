"""行情回退数据源（K-skill Korean Stock + Yahoo Finance），用于补充富途不支持的市场。"""
import json
import logging
import urllib.request
from dataclasses import dataclass
from datetime import datetime

from futu_client import Quote
from k_skill_client import fetch_korean_quote

logger = logging.getLogger(__name__)


YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"


@dataclass
class FallbackQuote(Quote):
    source: str = ""  # 'k-skill' 或 'yahoo'
    yahoo_ticker: str = ""


def fetch_yahoo_quote(ticker: str) -> FallbackQuote | None:
    """从 Yahoo Finance 获取单只股票快照。"""
    url = f"{YAHOO_BASE}/{ticker}?interval=1d&range=2d"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        result = data.get("chart", {}).get("result", [None])[0]
        if not result:
            return None

        meta = result.get("meta", {})
        timestamps = result.get("timestamp", [])
        closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
        prev_closes = result.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose", []) or closes

        if not closes:
            return None

        # 取最新有效收盘价
        price = None
        for c in reversed(closes):
            if c is not None:
                price = float(c)
                break

        prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
        if prev_close is None and len(prev_closes) >= 2:
            for c in reversed(prev_closes[:-1]):
                if c is not None:
                    prev_close = float(c)
                    break

        change = None
        change_pct = None
        if price is not None and prev_close:
            change = price - prev_close
            change_pct = (change / prev_close) * 100

        update_time = None
        if timestamps:
            update_time = datetime.fromtimestamp(timestamps[-1]).strftime("%Y-%m-%d %H:%M:%S")

        return FallbackQuote(
            code=ticker,
            name=meta.get("shortName", meta.get("longName", ticker)),
            price=price,
            open=None,
            prev_close=float(prev_close) if prev_close else None,
            change=change,
            change_pct=change_pct,
            volume=None,
            update_time=update_time,
            valid=price is not None,
            source="yahoo",
            yahoo_ticker=ticker,
        )
    except Exception as e:
        logger.warning(f"Yahoo Finance fetch failed for {ticker}: {e}")
        return None


def fetch_quote(ticker: str, yahoo_ticker: str) -> FallbackQuote | None:
    """优先使用 k-skill 获取韩国股票，失败则回退 Yahoo Finance。"""
    # 韩国股票优先走 k-skill
    if ticker.endswith(".KS") or ticker.endswith(".KQ"):
        q = fetch_korean_quote(ticker)
        if q:
            fq = FallbackQuote(**q.__dict__)
            fq.source = "k-skill"
            fq.yahoo_ticker = ""
            return fq
        logger.info(f"k-skill unavailable for {ticker}, falling back to Yahoo")

    # 其他市场或 k-skill 失败时走 Yahoo
    return fetch_yahoo_quote(yahoo_ticker)


def fetch_yahoo_kline(ticker: str, num: int = 100) -> list[dict]:
    """从 Yahoo Finance 获取历史 K 线。"""
    url = f"{YAHOO_BASE}/{ticker}?interval=1d&range=1y"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        result = data.get("chart", {}).get("result", [None])[0]
        if not result:
            return []

        timestamps = result.get("timestamp", [])
        quote = result.get("indicators", {}).get("quote", [{}])[0]
        opens = quote.get("open", [])
        highs = quote.get("high", [])
        lows = quote.get("low", [])
        closes = quote.get("close", [])
        volumes = result.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose", [])

        records = []
        for i, ts in enumerate(timestamps):
            if closes[i] is None:
                continue
            records.append({
                "time_key": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                "open": float(opens[i]) if opens[i] is not None else None,
                "high": float(highs[i]) if highs[i] is not None else None,
                "low": float(lows[i]) if lows[i] is not None else None,
                "close": float(closes[i]),
                "volume": int(volumes[i]) if volumes and volumes[i] is not None else None,
            })

        return records[-num:]
    except Exception as e:
        logger.warning(f"Yahoo Finance kline failed for {ticker}: {e}")
        return []
