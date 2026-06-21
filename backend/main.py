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

from config import HOLDINGS, DRAM_ETF_CODES, OPEND_HOST, OPEND_PORT, PUSH_INTERVAL_SECONDS
from futu_client import FutuClient
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
        self.latest_quotes: dict[str, QuoteResponse] = {}
        self.last_update = 0.0
        self.subscribers: set[asyncio.Queue] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._push_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def get_all_target_codes(self) -> list[str]:
        return list(self.resolved_codes.values())


state = AppState()


def _run_futu_loop():
    """在后台线程中运行富途行情循环：解析代码、订阅、轮询快照、推送。"""
    try:
        with FutuClient(OPEND_HOST, OPEND_PORT) as client:
            logger.info("Connected to OpenD, resolving codes...")
            resolved = client.resolve_all_codes()
            if not resolved:
                state.connection_error = "无法解析任何富途代码，请检查 OpenD 登录状态与行情权限。"
                state.connected = False
                return

            state.resolved_codes = resolved
            state.connected = True
            state.connection_error = None
            logger.info(f"Resolved codes: {resolved}")

            codes = list(resolved.values())
            if codes:
                client.subscribe(codes)

            while not state._stop_event.is_set():
                try:
                    quotes = client.get_snapshot(codes)
                    state.latest_quotes = {q.code: q for q in quotes.values()}
                    state.last_update = time.time()
                    # 推送到所有 WebSocket 订阅者
                    if state._loop and state.subscribers:
                        payload = {
                            "type": "quotes",
                            "timestamp": state.last_update,
                            "quotes": [QuoteResponse(**q.__dict__).model_dump() for q in quotes.values()],
                        }
                        for queue in list(state.subscribers):
                            state._loop.call_soon_threadsafe(queue.put_nowait, payload)
                except Exception as e:
                    logger.error(f"Error fetching snapshot: {e}")

                time.sleep(PUSH_INTERVAL_SECONDS)
    except Exception as e:
        logger.error(f"Futu background thread error: {e}")
        state.connection_error = str(e)
        state.connected = False


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
        "last_update": state.last_update,
    }


@app.get("/api/quote", response_model=QuoteBatchResponse)
async def get_quote():
    if not state.connected:
        raise HTTPException(status_code=503, detail=state.connection_error or "行情连接未就绪")
    quotes = list(state.latest_quotes.values())
    if not quotes and state.last_update == 0:
        # 尚未拉取到数据，等待一小段时间
        await asyncio.sleep(2)
        quotes = list(state.latest_quotes.values())
    return QuoteBatchResponse(
        timestamp=state.last_update,
        quotes=[QuoteResponse(**q.__dict__) for q in quotes],
    )


@app.get("/api/kline", response_model=KlineResponse)
async def get_kline(
    code: str = Query(..., description="富途代码，如 US.MU"),
    ktype: str = Query("1d", description="K线类型: 1m,5m,15m,30m,60m,1d,1w,1M"),
    num: int = Query(100, ge=1, le=1000),
):
    if not state.connected:
        raise HTTPException(status_code=503, detail="行情连接未就绪")
    try:
        with FutuClient(OPEND_HOST, OPEND_PORT) as client:
            records = client.get_kline(code, ktype, num)
            return KlineResponse(code=code, ktype=ktype, records=records)
    except Exception as e:
        logger.error(f"Kline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
            "quotes": [QuoteResponse(**q.__dict__).model_dump() for q in state.latest_quotes.values()],
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
