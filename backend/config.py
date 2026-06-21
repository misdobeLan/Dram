"""后端配置：OpenD 连接、持仓代码映射。"""
import os

OPEND_HOST = os.getenv("FUTU_OPEND_HOST", "127.0.0.1")
OPEND_PORT = int(os.getenv("FUTU_OPEND_PORT", "11111"))

# 页面持仓映射到富途代码（市场前缀 + 代码）
# 权重来源：Roundhill Investments 官网 Top Holdings（As of 06/21/2026）
# 注意：富途 OpenAPI 目前不支持韩国（KR）与台湾（TW）市场，因此韩国成分股使用 Yahoo Finance 代码作为回退。
HOLDINGS = [
    {"name": "Micron Technology Inc", "ticker": "MU", "market": "US", "weight": 27.57, "futu_codes": ["US.MU"], "yahoo_ticker": "MU", "segment": "DRAM / NAND / HBM", "color": "#2d7dff"},
    {"name": "SK hynix", "ticker": "000660.KS", "market": "Korea", "weight": 26.87, "futu_codes": ["US.HXSCF"], "yahoo_ticker": "000660.KS", "segment": "HBM / DRAM", "color": "#00f0ff"},
    {"name": "Samsung Electronics Co", "ticker": "005930.KS", "market": "Korea", "weight": 17.64, "futu_codes": ["US.SSNLF"], "yahoo_ticker": "005930.KS", "segment": "DRAM / NAND / HBM", "color": "#00ff9d"},
    {"name": "Kioxia Holdings", "ticker": "285A / KI5.SG", "market": "Japan / Singapore", "weight": 8.00, "futu_codes": ["SG.KI5", "US.285A"], "yahoo_ticker": "KI5.SI", "segment": "NAND Flash", "color": "#f59e0b"},
    {"name": "Sandisk", "ticker": "SNDK", "market": "US", "weight": 5.52, "futu_codes": ["US.SNDK"], "yahoo_ticker": "SNDK", "segment": "NAND / SSD", "color": "#ff4d6d"},
    {"name": "Western Digital", "ticker": "WDC", "market": "US", "weight": 4.36, "futu_codes": ["US.WDC"], "yahoo_ticker": "WDC", "segment": "HDD / NAND", "color": "#ec4899"},
    {"name": "Seagate Technology Holdings", "ticker": "STX", "market": "US / Ireland", "weight": 4.27, "futu_codes": ["US.STX"], "yahoo_ticker": "STX", "segment": "HDD", "color": "#a855f7"},
    {"name": "Nanya Technology", "ticker": "2408.TW", "market": "Taiwan", "weight": 3.27, "futu_codes": ["TW.2408", "US.2408"], "yahoo_ticker": "2408.TW", "segment": "DRAM", "color": "#14b8a6"},
    {"name": "Winbond Electronics", "ticker": "2344.TW", "market": "Taiwan", "weight": 2.08, "futu_codes": ["TW.2344", "US.2344"], "yahoo_ticker": "2344.TW", "segment": "Specialty Memory", "color": "#6366f1"},
]

# DRAM ETF 可能代码（按优先级尝试）
DRAM_ETF_CODES = ["US.DRAM", "HK.DRAM"]
DRAM_YAHOO_TICKER = "DRAM"

# 缓存与订阅配置
CACHE_TTL_SECONDS = 3
PUSH_INTERVAL_SECONDS = 2
