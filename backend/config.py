"""后端配置：OpenD 连接、持仓代码映射。"""
import os

OPEND_HOST = os.getenv("FUTU_OPEND_HOST", "127.0.0.1")
OPEND_PORT = int(os.getenv("FUTU_OPEND_PORT", "11111"))

# 页面持仓映射到富途代码（市场前缀 + 代码）
HOLDINGS = [
    {"name": "SK Hynix", "ticker": "000660.KS", "market": "Korea", "weight": 28.2, "futu_codes": ["KR.000660", "US.000660"], "segment": "HBM / DRAM", "color": "#00f0ff"},
    {"name": "Micron Technology", "ticker": "MU", "market": "US", "weight": 24.9, "futu_codes": ["US.MU"], "segment": "DRAM / NAND / HBM", "color": "#2d7dff"},
    {"name": "Samsung Electronics", "ticker": "005930.KS", "market": "Korea", "weight": 20.9, "futu_codes": ["KR.005930", "US.005930"], "segment": "DRAM / NAND / HBM", "color": "#00ff9d"},
    {"name": "Kioxia Holdings", "ticker": "285A / KI5.SG", "market": "Japan / Singapore", "weight": 6.5, "futu_codes": ["SG.KI5", "US.285A"], "segment": "NAND Flash", "color": "#f59e0b"},
    {"name": "SanDisk", "ticker": "SNDK", "market": "US", "weight": 5.1, "futu_codes": ["US.SNDK"], "segment": "NAND / SSD", "color": "#ff4d6d"},
    {"name": "Seagate Technology", "ticker": "STX", "market": "US / Ireland", "weight": 4.4, "futu_codes": ["US.STX"], "segment": "HDD", "color": "#a855f7"},
    {"name": "Western Digital", "ticker": "WDC", "market": "US", "weight": 4.0, "futu_codes": ["US.WDC"], "segment": "HDD / NAND", "color": "#ec4899"},
    {"name": "Nanya Technology", "ticker": "2408.TW", "market": "Taiwan", "weight": 3.3, "futu_codes": ["TW.2408", "US.2408"], "segment": "DRAM", "color": "#14b8a6"},
    {"name": "Winbond Electronics", "ticker": "2344.TW", "market": "Taiwan", "weight": 2.1, "futu_codes": ["TW.2344", "US.2344"], "segment": "Specialty Memory", "color": "#6366f1"},
]

# DRAM ETF 可能代码（按优先级尝试）
DRAM_ETF_CODES = ["US.DRAM", "HK.DRAM"]

# 缓存与订阅配置
CACHE_TTL_SECONDS = 3
PUSH_INTERVAL_SECONDS = 2
