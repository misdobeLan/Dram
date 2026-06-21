"""FastAPI 行情代理后端入口。"""
import asyncio
import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import (
    HOLDINGS, DRAM_ETF_CODES, DRAM_YAHOO_TICKER,
    OPEND_HOST, OPEND_PORT, PUSH_INTERVAL_SECONDS,
)
from fallback_client import fetch_quote, fetch_yahoo_kline
from futu_client import FutuClient
from k_skill_client import search_stock
from models import QuoteBatchResponse, QuoteResponse, KlineResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent

# 全局状态
class AppState:
    def __init__(self):
        self.connected = False
        self.connection_error: str | None = None
        self.resolved_codes: dict[str, str] = {}  # {ticker: futu_code}
        self.yahoo_tickers: dict[str, str] = {}   # {ticker: yahoo_ticker}
        self.latest_quotes: dict[str, QuoteResponse] = {}
        self.yahoo_quotes: dict[str, QuoteResponse] = {}
        self.last_update = 0.0
        self.subscribers: set[asyncio.Queue] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._push_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def get_all_target_codes(self) -> list[str]:
        return list(self.resolved_codes.values())

    def get_merged_quotes(self) -> list[QuoteResponse]:
        merged = dict(self.yahoo_quotes)
        merged.update(self.latest_quotes)  # Futu 数据优先覆盖 Yahoo
        return list(merged.values())


state = AppState()


def _port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _resolve_yahoo_tickers(resolved_futu: dict[str, str] | None = None) -> dict[str, str]:
    """解析需要 Yahoo Finance 回退的持仓代码。
    若某个 ticker 已被富途解析，则优先使用富途，不再请求 Yahoo。
    """
    mapping = {}
    for h in HOLDINGS:
        if h.get("yahoo_ticker") and h["ticker"] not in (resolved_futu or {}):
            mapping[h["ticker"]] = h["yahoo_ticker"]
    # DRAM ETF 只要富途已解析，就不走 Yahoo
    if DRAM_YAHOO_TICKER and (resolved_futu is None or "DRAM" not in resolved_futu):
        mapping["DRAM"] = DRAM_YAHOO_TICKER
    return mapping


def _fetch_fallback_batch(tickers: dict[str, str]) -> dict[str, QuoteResponse]:
    """批量获取回退行情：韩国股票优先 k-skill，其余 Yahoo Finance（并发）。"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    quotes = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {
            executor.submit(fetch_quote, ticker, yahoo_ticker): ticker
            for ticker, yahoo_ticker in tickers.items()
        }
        for future in as_completed(future_to_ticker, timeout=20):
            ticker = future_to_ticker[future]
            try:
                q = future.result()
                if q and q.valid:
                    q.code = ticker
                    quotes[ticker] = q
            except Exception as e:
                logger.warning(f"Fallback fetch error for {ticker}: {e}")
    return quotes


def _run_futu_loop():
    """在后台线程中运行富途行情循环：解析代码、订阅、轮询快照、推送。"""
    # 无论 OpenD 是否在线，先初始化 Yahoo 代码映射（先假设全部走 Yahoo）
    state.yahoo_tickers = _resolve_yahoo_tickers()

    if not _port_open(OPEND_HOST, OPEND_PORT):
        state.connection_error = f"OpenD 未在 {OPEND_HOST}:{OPEND_DEFAULT_PORT} 运行，请先启动 OpenD。"
        state.connected = False
        logger.error(state.connection_error)
        # 仅使用 Yahoo 数据
        while not state._stop_event.is_set():
            try:
                state.yahoo_quotes = _fetch_fallback_batch(state.yahoo_tickers)
                state.last_update = time.time()
                _push_quotes(state.get_merged_quotes())
            except Exception as e:
                logger.error(f"Error fetching Yahoo quotes: {e}")
            time.sleep(PUSH_INTERVAL_SECONDS)
        return

    try:
        with FutuClient(OPEND_HOST, OPEND_PORT) as client:
            logger.info("Connected to OpenD, resolving codes...")
            resolved = client.resolve_all_codes()
            # 将 resolved 保存到状态
            state.resolved_codes = resolved

            if not resolved:
                state.connection_error = "OpenD 已连接，但无法解析任何代码。可能未登录或行情权限不足。"
                state.connected = False
                logger.error(state.connection_error)
                return

            state.connected = True
            state.connection_error = None
            logger.info(f"Resolved Futu codes: {resolved}")

            # 富途解析成功后，Yahoo 仅作为未解析持仓的回退
            state.yahoo_tickers = _resolve_yahoo_tickers(resolved)

            codes = list(resolved.values())
            if codes:
                client.subscribe(codes)

            while not state._stop_event.is_set():
                try:
                    # 1. 拉取富途快照
                    quotes = client.get_snapshot(codes)
                    state.latest_quotes = {q.code: q for q in quotes.values()}
                    # 2. 拉取 k-skill / Yahoo 回退行情（补充富途不支持的市场）
                    state.yahoo_quotes = _fetch_fallback_batch(state.yahoo_tickers)
                    state.last_update = time.time()
                    # 3. 推送合并后的行情
                    _push_quotes(state.get_merged_quotes())
                except Exception as e:
                    logger.error(f"Error fetching snapshot: {e}")

                time.sleep(PUSH_INTERVAL_SECONDS)
    except Exception as e:
        logger.error(f"Futu background thread error: {e}")
        state.connection_error = str(e)
        state.connected = False
        # 富途异常时回退到 Yahoo
        while not state._stop_event.is_set():
            try:
                state.yahoo_quotes = _fetch_fallback_batch(state.yahoo_tickers)
                state.last_update = time.time()
                _push_quotes(state.get_merged_quotes())
            except Exception as e2:
                logger.error(f"Error fetching Yahoo quotes: {e2}")
            time.sleep(PUSH_INTERVAL_SECONDS)


def _push_quotes(quotes: list):
    """推送行情到所有 WebSocket 订阅者。"""
    if state._loop and state.subscribers:
        payload = {
            "type": "quotes",
            "timestamp": state.last_update,
            "quotes": [QuoteResponse(**q.__dict__).model_dump() for q in quotes],
        }
        for queue in list(state.subscribers):
            state._loop.call_soon_threadsafe(queue.put_nowait, payload)


@asynccontextmanager
async def lifespan(app: FastAPI):
    state._loop = asyncio.get_running_loop()
    state._stop_event.clear()
    state._push_thread = threading.Thread(target=_run_futu_loop, daemon=True)
    state._push_thread.start()
    yield
    state._stop_event.set()
    if state._push_thread:
        state._push_thread.join(timeout=5)


app = FastAPI(title="DRAM Tracker Quote Proxy", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {
        "connected": state.connected,
        "error": state.connection_error,
        "resolved_codes": state.resolved_codes,
        "yahoo_tickers": state.yahoo_tickers,
        "last_update": state.last_update,
    }


@app.get("/api/holdings")
async def get_holdings():
    """返回持仓列表，包含解析后的富途代码与 Yahoo 回退代码。"""
    result = []
    for h in HOLDINGS:
        item = dict(h)
        item["futu_code"] = state.resolved_codes.get(h["ticker"])
        item["yahoo_code"] = h.get("yahoo_ticker")
        result.append(item)
    return {
        "connected": state.connected,
        "etf_code": state.resolved_codes.get("DRAM"),
        "etf_yahoo": DRAM_YAHOO_TICKER,
        "holdings": result,
    }


@app.get("/api/quote", response_model=QuoteBatchResponse)
async def get_quote():
    quotes = state.get_merged_quotes()
    if not quotes and not state.connected and not state.yahoo_quotes:
        raise HTTPException(status_code=503, detail=state.connection_error or "行情连接未就绪")
    if not quotes and state.last_update == 0:
        await asyncio.sleep(2)
        quotes = state.get_merged_quotes()
    return QuoteBatchResponse(
        timestamp=state.last_update,
        quotes=[QuoteResponse(**q.__dict__) for q in quotes],
    )


@app.get("/api/kline", response_model=KlineResponse)
async def get_kline(
    code: str = Query(..., description="代码，如 US.MU 或 Yahoo 代码 MU"),
    ktype: str = Query("1d", description="K线类型: 1m,5m,15m,30m,60m,1d,1w,1M"),
    num: int = Query(100, ge=1, le=1000),
):
    # 1. 尝试富途 K 线（如果 code 是富途代码且 OpenD 在线）
    if state.connected:
        try:
            with FutuClient(OPEND_HOST, OPEND_PORT) as client:
                records = client.get_kline(code, ktype, num)
                if records:
                    return KlineResponse(code=code, ktype=ktype, records=records)
        except Exception as e:
            logger.warning(f"Futu kline failed for {code}: {e}")

    # 2. 回退到 Yahoo Finance K 线
    try:
        records = fetch_yahoo_kline(code, num)
        if records:
            return KlineResponse(code=code, ktype=ktype, records=records)
    except Exception as e:
        logger.warning(f"Yahoo kline failed for {code}: {e}")

    raise HTTPException(status_code=500, detail=f"无法获取 {code} 的 K 线数据")


@app.get("/api/korean/search")
async def korean_search(q: str = Query(..., min_length=1), bas_dd: str | None = None):
    """通过 k-skill 代理搜索韩国上市股票（KOSPI/KOSDAQ）。

    该接口仅作辅助验证/数据源；由于代理当前行情接口不稳定，
    实际价格仍通过 Yahoo Finance 回退获取。
    """
    items = search_stock(q, bas_dd=bas_dd)
    return {"query": q, "bas_dd": bas_dd, "count": len(items), "items": items}


@app.get("/api/market-state")
async def get_market_state():
    if not state.connected:
        raise HTTPException(status_code=503, detail="行情连接未就绪")
    try:
        from futu import OpenQuoteContext
        with OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT) as ctx:
            ret, data = ctx.get_market_state(list(state.resolved_codes.values()))
            if ret != 0:
                raise HTTPException(status_code=500, detail="market state query failed")
            return [
                {"code": row.get("code"), "state": row.get("market_state")}
                for _, row in data.iterrows()
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/quotes")
async def websocket_quotes(websocket: WebSocket):
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()
    state.subscribers.add(queue)
    try:
        # 先发送一次当前全量数据
        initial = {
            "type": "quotes",
            "timestamp": state.last_update,
            "quotes": [QuoteResponse(**q.__dict__).model_dump() for q in state.get_merged_quotes()],
        }
        await websocket.send_json(initial)

        while True:
            payload = await queue.get()
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        state.subscribers.discard(queue)


# 静态文件与 SPA 回退
app.mount("/css", StaticFiles(directory=ROOT_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=ROOT_DIR / "js"), name="js")
app.mount("/data", StaticFiles(directory=ROOT_DIR / "data"), name="data")


@app.get("/")
async def serve_index():
    return FileResponse(ROOT_DIR / "index.html")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = ROOT_DIR / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(ROOT_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
