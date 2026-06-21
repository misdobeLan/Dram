"""Pydantic 数据模型。"""
from pydantic import BaseModel
from typing import Literal


class QuoteResponse(BaseModel):
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


class QuoteBatchResponse(BaseModel):
    timestamp: float
    quotes: list[QuoteResponse]


class KlineResponse(BaseModel):
    code: str
    ktype: str
    records: list[dict]


class MarketStateResponse(BaseModel):
    code: str
    state: str | None = None


class ErrorResponse(BaseModel):
    detail: str
