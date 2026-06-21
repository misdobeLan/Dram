"""富途 SDK 封装：连接、快照、K线、订阅、实时推送。"""
import asyncio
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterable

from futu import KLType, OpenQuoteContext, SubType

from config import HOLDINGS, DRAM_ETF_CODES, OPEND_HOST, OPEND_PORT

logger = logging.getLogger(__name__)


@dataclass
class Quote:
    code: str
    name: str
    price: float | None = None
    open: float | None = None
    prev_close: float | None = None
    change: float | None = None
    change_pct: float | None = None
    volume: int | None = None
    update_time: str | None = None
    valid: bool = True
    error: str | None = None


class FutuClient:
    def __init__(self, host: str = OPEND_HOST, port: int = OPEND_PORT):
        self.host = host
        self.port = port
        self._ctx: OpenQuoteContext | None = None
        self._resolved_codes: dict[str, str] = {}

    @contextmanager
    def context(self):
        ctx = OpenQuoteContext(host=self.host, port=self.port)
        try:
            self._ctx = ctx
            yield self
        finally:
            ctx.close()
            self._ctx = None

    def resolve_code(self, candidate_codes: list[str]) -> str | None:
        """从候选代码中返回第一个可用的富途代码。"""
        if not self._ctx:
            raise RuntimeError("Quote context not initialized")
        for code in candidate_codes:
            if code in self._resolved_codes:
                return self._resolved_codes[code]
            ret, data = self._ctx.get_market_snapshot([code])
            if ret == 0 and not data.empty:
                self._resolved_codes[code] = code
                return code
        return None

    def resolve_all_codes(self) -> dict[str, str]:
        """解析所有持仓和 ETF 的可用富途代码。返回 {原始标识: 富途代码}。"""
        mapping = {}
        # ETF
        etf_code = self.resolve_code(DRAM_ETF_CODES)
        if etf_code:
            mapping["DRAM"] = etf_code
        # 持仓
        for h in HOLDINGS:
            resolved = self.resolve_code(h["futu_codes"])
            if resolved:
                mapping[h["ticker"]] = resolved
            else:
                logger.warning(f"无法解析持仓代码: {h['name']} {h['futu_codes']}")
        return mapping

    def get_snapshot(self, codes: Iterable[str]) -> dict[str, Quote]:
        """批量获取市场快照。"""
        if not self._ctx:
            raise RuntimeError("Quote context not initialized")
        codes = list(codes)
        ret, data = self._ctx.get_market_snapshot(codes)
        if ret != 0:
            raise RuntimeError(f"get_market_snapshot failed: {ret}")

        quotes = {}
        for _, row in data.iterrows():
            code = row.get("code")
            prev_close = self._to_float(row.get("last_close"))
            price = self._to_float(row.get("last_price"))
            open_ = self._to_float(row.get("open_price"))
            change_pct = self._to_float(row.get("change_rate"))
            volume = self._to_int(row.get("volume"))
            update_time = row.get("update_time")

            # 兼容：部分字段可能为空，用 last_price / last_close 计算
            if change_pct is None and price is not None and prev_close and prev_close != 0:
                change_pct = (price - prev_close) / prev_close * 100

            quotes[code] = Quote(
                code=code,
                name=str(row.get("stock_name", "")),
                price=price,
                open=open_,
                prev_close=prev_close,
                change=price - prev_close if (price is not None and prev_close is not None) else None,
                change_pct=change_pct,
                volume=volume,
                update_time=str(update_time) if update_time is not None else None,
            )

        # 对未返回的代码标记为无效
        for code in codes:
            if code not in quotes:
                quotes[code] = Quote(code=code, name="", valid=False, error="snapshot not returned")
        return quotes

    def get_kline(self, code: str, ktype: str = "K_DAY", num: int = 100) -> list[dict]:
        """获取 K 线数据。"""
        if not self._ctx:
            raise RuntimeError("Quote context not initialized")
        kl_mapping = {
            "1m": KLType.K_1M,
            "5m": KLType.K_5M,
            "15m": KLType.K_15M,
            "30m": KLType.K_30M,
            "60m": KLType.K_60M,
            "1d": KLType.K_DAY,
            "1w": KLType.K_WEEK,
            "1M": KLType.K_MON,
        }
        kl = kl_mapping.get(ktype, KLType.K_DAY)
        ret, data = self._ctx.get_cur_kl(code, kl, num)
        if ret != 0:
            raise RuntimeError(f"get_cur_kl failed: {ret}")
        records = []
        for _, row in data.iterrows():
            records.append({
                "time_key": str(row.get("time_key")),
                "open": self._to_float(row.get("open")),
                "high": self._to_float(row.get("high")),
                "low": self._to_float(row.get("low")),
                "close": self._to_float(row.get("close")),
                "volume": self._to_int(row.get("volume")),
            })
        return records

    def subscribe(self, codes: Iterable[str], sub_types: list[str] | None = None) -> list[str]:
        """订阅实时行情，返回实际订阅成功的代码。"""
        if not self._ctx:
            raise RuntimeError("Quote context not initialized")
        codes = list(codes)
        sub_types = sub_types or [SubType.QUOTE]
        ret, data = self._ctx.subscribe(codes, sub_types)
        if ret != 0:
            logger.warning(f"subscribe partial failure: {ret}, data={data}")
        # 查询实际订阅状态
        ret2, data2 = self._ctx.query_subscription()
        if ret2 == 0:
            return data2.get("sub_list", {}).get("QUOTE", [])
        return codes

    def set_handler(self, handler: Callable):
        """设置实时推送回调。"""
        if not self._ctx:
            raise RuntimeError("Quote context not initialized")
        self._ctx.set_handler(handler)

    @staticmethod
    def _to_float(val):
        if val is None:
            return None
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(val):
        if val is None:
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            return None
