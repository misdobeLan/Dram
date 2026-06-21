"""Naver 财经新闻动态获取客户端。

通过 k-skill-proxy 调用 Naver OpenAPI 新闻搜索，优先使用中文关键词，
以获取面向中文读者的韩国持仓（Samsung、SK hynix）相关报道。
结果带内存缓存，避免触发上游 429 rate limit。
"""
import json
import logging
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import sec_client

logger = logging.getLogger(__name__)

NAVER_NEWS_PROXY_URL = "https://k-skill-proxy.nomadamas.org/v1/naver-news/search"

# 非韩国持仓的静态 curated fallback（中文），当动态源失败或不足时兜底展示
STATIC_FALLBACK_NEWS: list[dict] = [
    {
        "source": "Morningstar",
        "date": "2026-05-21",
        "title": "投资者蜂拥而入这只 ETF，但持仓估值已偏高",
        "summary": "DRAM 在 45 天内资产规模突破近百亿美元，但 Morningstar 分析师认为主要持仓估值已偏高，且行业具备商品周期属性。",
        "url": "https://www.morningstar.com/funds/memory-etf-has-been-hit-with-investors-they-shouldnt-forget-fundamentals",
        "tickers": ["DRAM"],
    },
    {
        "source": "Barron's",
        "date": "2026-05-15",
        "title": "这只记忆体芯片 ETF 涨势惊人，芯片股热潮只是部分原因",
        "summary": "DRAM 自上市以来上涨约 85%，资金流入与三大核心持仓（Micron、SK Hynix、Samsung）的强势表现共同推动。",
        "url": "https://www.barrons.com/articles/memory-chip-stock-etf-sandisk-micron-a7f40b97",
        "tickers": ["DRAM", "MU", "000660.KS", "005930.KS"],
    },
    {
        "source": "AOL / Yahoo Finance",
        "date": "2026-05-26",
        "title": "Micron、Sandisk 等记忆体芯片股暴涨，推动这只新 ETF 飙升",
        "summary": "记忆体芯片成为 AI 供应链最紧绷环节，DRAM 成为史上增长最快的 ETF 之一，30 个交易日内资产突破百亿美元。",
        "url": "https://www.aol.com/articles/scorching-runs-memory-chip-stocks-135416000.html",
        "tickers": ["DRAM", "MU", "SNDK"],
    },
    {
        "source": "Roundhill Investments",
        "date": "2026",
        "title": "Roundhill Memory ETF（DRAM）官方介绍",
        "summary": "官方资料显示 DRAM 为主动管理型 ETF，通过股票与总收益互换投资全球记忆体公司，覆盖 HBM、DRAM、NAND、NOR、HDD 等。",
        "url": "https://www.roundhillinvestments.com/etf/dram/",
        "tickers": ["DRAM"],
    },
    {
        "source": "Quiver Quantitative / Globe Newswire",
        "date": "2026-06-01",
        "title": "Micron 在 COMPUTEX 2026 展示 AI 优化记忆体与储存方案",
        "summary": "Micron 展示完整 AI 记忆体与储存产品组合，包括 HBM4 36GB、256GB SOCAMM2 与数据中心 SSD，强调记忆体带宽与容量已成为系统效能核心。",
        "url": "https://www.quiverquant.com/news/Micron+Technology+Showcases+AI-Optimized+Memory+and+Storage+Solutions+at+COMPUTEX+2026",
        "tickers": ["MU"],
    },
    {
        "source": "TrendForce",
        "date": "2026-02-13",
        "title": "Kioxia 第三财季营收创纪录，确认 2026 年 NAND 产能售罄",
        "summary": "Kioxia 财报创纪录，并确认 2026 年 NAND 产能已售罄；AI 需求推动数据中心 SSD 销售，与 SanDisk 的合资协议也延长至 2034 年。",
        "url": "https://www.trendforce.com/news/2026/02/13/news-kioxia-posts-record-%C2%A5543-6b-q3-fy25-revenue-confirms-2026-nand-fully-booked",
        "tickers": ["285A / KI5.SG", "SNDK"],
    },
    {
        "source": "AInvest",
        "date": "2026-01-16",
        "title": "把握 AI 驱动的记忆体与储存超级周期：SanDisk 与 Seagate",
        "summary": "分析指出 SanDisk 与 Seagate 是 AI 储存超级周期的关键受惠者：SanDisk 的 BiCS8 NAND 与数据中心 SSD 获 hyperscaler 认证，Seagate 的 HAMR 硬盘则承接海量冷储存需求。",
        "url": "https://www.ainvest.com/news/capitalizing-ai-driven-memory-storage-supercycle-sandisk-seagate-2026-plays-2601",
        "tickers": ["SNDK", "STX"],
    },
    {
        "source": "Futu / Zhitong Finance",
        "date": "2026-01-28",
        "title": "Seagate 财报全面超预期，称 2026 年产能已售罄",
        "summary": "Seagate 财报全面超预期，并透露 2026 年近线 HDD 产能已售罄；AI 数据中心对高容量硬盘的需求持续引爆「储存超级周期」。",
        "url": "https://news.futunn.com/en/post/68002313/surging-hdd-demand-reinforces-storage-super-cycle-narrative-seagate-stxus",
        "tickers": ["STX", "WDC"],
    },
    {
        "source": "Chief Group",
        "date": "2026-01-14",
        "title": "AI 狂热持续，储存股升势能否持续？",
        "summary": "SanDisk、Western Digital、Seagate、Micron 等美国数据储存相关股票在 2025–2026 年初大幅领涨，AI 数据爆炸式增长带动 NAND、企业级 SSD 与硬盘需求急增。",
        "url": "https://www.chiefgroup.com.hk/en/financial/media?id=13481",
        "tickers": ["SNDK", "WDC", "STX", "MU"],
    },
    {
        "source": "01.co",
        "date": "2026-04-15",
        "title": "南亚科技 2026 年 Q1：利基型 DRAM 供应紧张确认，NAND 巨头入股锁定货源",
        "summary": "南亚科技 Q1 2026 营收同比增长 583%，毛利率跃升至 67.9%；SanDisk、SK hynix、Kioxia 等 NAND 大厂参与私募，锁定长期 DRAM 供应。",
        "url": "https://www.01.co/research/nanya-tech-q1-2026-legacy-dram-squeeze",
        "tickers": ["2408.TW", "SNDK", "000660.KS", "285A / KI5.SG"],
    },
    {
        "source": "TrendForce",
        "date": "2026-02-11",
        "title": "华邦电子预计 DRAM 价格到 2026 年 6 月将上涨近 4 倍，产能已预订至 2027 年",
        "summary": "华邦电子预期本季 DRAM 价格暴涨 90–95%，至 2026 年中累计涨幅接近 4 倍；2027 年 DRAM 产能已提前预售，资本支出创历史新高。",
        "url": "https://www.trendforce.com/news/2026/02/11/news-winbond-expects-dram-prices-to-jump-nearly-4x-by-june-2026-capacity-booked-through-2027",
        "tickers": ["2344.TW"],
    },
    {
        "source": "Barron's",
        "date": "2026-06-19",
        "title": "Micron 财报面临重大考验，历史走势透露什么信号？",
        "summary": "Barron's 分析 Micron 即将发布的财报可能成为股价短期催化剂；在记忆体超级周期中，市场对其 HBM 订单与毛利率扩张寄予厚望。",
        "url": "https://www.barrons.com/articles/micron-stock-earnings-history-mu-6f2a3c1b",
        "tickers": ["MU"],
    },
    {
        "source": "Barron's",
        "date": "2026-06-19",
        "title": "Intel 为何挖角 SK hynix 前 CEO？Micron 劲敌的人事震动",
        "summary": "Barron's 报道 Intel 聘请 SK hynix 前 CEO 李锡熙加入董事会，凸显 AI 记忆体人才与技术的战略价值，也间接反映 Micron 面临的竞争格局。",
        "url": "https://www.barrons.com/articles/intel-hires-sk-hynix-ceo-micron-rival-4d8e9f2a",
        "tickers": ["MU", "000660.KS"],
    },
    {
        "source": "MarketWatch / Barron's",
        "date": "2026-06-18",
        "title": "Micron 等记忆体股今年涨幅惊人，为何估值仍显便宜？",
        "summary": "MarketWatch 汇编分析指出，尽管 Micron 等记忆体股已大幅上涨，但相对 AI 需求带来的盈利上修，其 forward P/E 仍低于历史高位。",
        "url": "https://www.marketwatch.com/story/micron-other-memory-stocks-are-having-their-best-year-ever-why-do-they-still-look-so-cheap-2026-06-18",
        "tickers": ["MU", "SNDK", "WDC"],
    },
    {
        "source": "Benzinga",
        "date": "2026-06-20",
        "title": "Micron 年内已涨 285%，财报后将继续飙升还是回调？",
        "summary": "Benzinga 汇总期权市场与分析观点，认为 Micron 在 6 月 24 日财报前波动率飙升，HBM 产能售罄与数据中心需求是看多核心逻辑。",
        "url": "https://www.benzinga.com/markets/tech/26/06/53128497/micron-is-up-285-so-far-this-year-will-it-surge-or-crash-after-earnings",
        "tickers": ["MU"],
    },
    {
        "source": "Benzinga",
        "date": "2026-06-20",
        "title": "美银分析师：Sandisk 大涨 4755% 后仍有上行空间",
        "summary": "Benzinga 援引美银报告，认为 Sandisk 在 AI 数据中心 SSD、BiCS8 NAND 与长期供应合约驱动下，未来几个季度仍有进一步重估空间。",
        "url": "https://www.benzinga.com/markets/tech/26/06/53128112/top-bofa-analyst-explains-why-sandisk-has-more-upside-after-4755-surge",
        "tickers": ["SNDK"],
    },
    {
        "source": "AOL / Motley Fool",
        "date": "2026-04-30",
        "title": "Sandisk 2026 财年 Q3 财报电话会议纪要",
        "summary": "Sandisk Q3 2026 营收与利润大超预期，数据中心 SSD 需求强劲；公司授权 60 亿美元回购，并将与 Kioxia 的合资协议延长至 2034 年。",
        "url": "https://www.aol.com/finance/sandisk-sndk-q3-2026-earnings-223040414.html",
        "tickers": ["SNDK", "285A / KI5.SG"],
    },
    {
        "source": "Barron's",
        "date": "2026-03-19",
        "title": "今日市场焦点个股：Micron、Accenture、Seagate 等",
        "summary": "Barron's 梳理当日推动美股波动的核心个股，Seagate 与 Micron 因 AI 储存需求持续获得资金关注。",
        "url": "https://www.barrons.com/articles/micron-accenture-seagate-stocks-today-movers-3a7b8c9d",
        "tickers": ["MU", "STX"],
    },
    {
        "source": "Micron 官方新闻室",
        "date": "2026-06-01",
        "title": "Micron 在 COMPUTEX 2026 展示 AI 无处不在的完整记忆体方案",
        "summary": "Micron 官方发布：在 COMPUTEX 2026 展示从数据中心到边缘设备的 AI 优化记忆体与储存产品，包括 256GB DDR5 服务器模组与 245TB SSD。",
        "url": "https://www.micron.com/about/press/news/2026/06/micron-powers-ai-everywhere-at-computex-2026",
        "tickers": ["MU"],
    },
    {
        "source": "Barron's",
        "date": "2026-06-16",
        "title": "SpaceX、Western Digital、Moderna 等解释今日市场的个股",
        "summary": "Barron's 市场综述将 Western Digital 列为当日影响大盘的关键个股之一，反映 HDD 与数据储存板块在 AI 基建中的重估。",
        "url": "https://www.barrons.com/articles/spacex-western-digital-moderna-stocks-today-market-2e4f6a8b",
        "tickers": ["WDC"],
    },
]

# 持仓 -> 中文搜索词映射（Naver 对中文关键词也能返回中文报道）
HOLDING_SEARCH_QUERIES: dict[str, list[str]] = {
    "005930.KS": ["三星电子"],
    "000660.KS": ["SK海力士"],
}

# 缓存
class _NewsCache:
    def __init__(self, ttl_seconds: int = 600):
        self.ttl_seconds = ttl_seconds
        self._data: dict[str, tuple[float, list[dict]]] = {}

    def get(self, key: str) -> list[dict] | None:
        if key not in self._data:
            return None
        cached_at, items = self._data[key]
        if time.time() - cached_at > self.ttl_seconds:
            self._data.pop(key, None)
            return None
        return items

    def set(self, key: str, items: list[dict]) -> None:
        self._data[key] = (time.time(), items)


_cache = _NewsCache(ttl_seconds=600)


def _parse_pub_date(iso_str: str | None) -> str:
    """将 pub_date_iso 转为 YYYY-MM-DD，失败则返回今天。"""
    if not iso_str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _strip_html_entities(text: str | None) -> str:
    if not text:
        return ""
    # k-skill-proxy 已移除 <b> 与高亮标签，这里仅做简单兜底
    return text.strip()


def _fetch_naver_news(query: str, display: int = 5) -> list[dict]:
    """调用 Naver News Search，返回规范化后的新闻列表。"""
    cached = _cache.get(query)
    if cached is not None:
        logger.info(f"Naver news cache hit for query: {query}")
        return cached

    url = f"{NAVER_NEWS_PROXY_URL}?{urllib.parse.urlencode({'q': query, 'display': display, 'sort': 'date'})}"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.warning(f"Naver news HTTP error: {e.code} for {query}: {e.read().decode('utf-8', errors='ignore')[:200]}")
        return []
    except Exception as e:
        logger.warning(f"Naver news request failed for {query}: {e}")
        return []

    items = data.get("items", [])
    normalized = []
    for item in items:
        title = _strip_html_entities(item.get("title"))
        description = _strip_html_entities(item.get("description"))
        link = item.get("original_link") or item.get("link") or ""
        pub_date = _parse_pub_date(item.get("pub_date_iso"))
        if not title or not link:
            continue
        normalized.append({
            "source": "Naver 财经 / finance.naver.com",
            "date": pub_date,
            "title": title,
            "summary": description,
            "url": link,
        })

    _cache.set(query, normalized)
    return normalized


def fetch_holding_news(ticker: str, display: int = 5) -> list[dict]:
    """获取某个持仓的动态新闻，返回带 tickers 字段的新闻字典列表。"""
    queries = HOLDING_SEARCH_QUERIES.get(ticker, [])
    if not queries:
        return []

    results = []
    for query in queries:
        for item in _fetch_naver_news(query, display=display):
            item["tickers"] = [ticker]
            results.append(item)
    return results


def fetch_all_dynamic_news(display_per_query: int = 5) -> list[dict]:
    """获取所有配置了动态源的持仓新闻，按日期倒序返回。"""
    all_news: list[dict] = []
    for ticker in HOLDING_SEARCH_QUERIES:
        try:
            all_news.extend(fetch_holding_news(ticker, display=display_per_query))
        except Exception as e:
            logger.warning(f"Failed to fetch news for {ticker}: {e}")

    # 去重（按 URL）
    seen = set()
    unique = []
    for item in all_news:
        url = item.get("url", "")
        if url and url in seen:
            continue
        if url:
            seen.add(url)
        unique.append(item)

    # 按日期倒序
    unique.sort(key=lambda x: x.get("date", ""), reverse=True)
    return unique


def fetch_merged_news(dynamic_display: int = 5, sec_display_per_ticker: int = 2) -> tuple[list[dict], bool]:
    """获取动态新闻（Naver + SEC EDGAR）并与静态 fallback 合并，返回 (items, dynamic_ok)。

    当动态源完全失败时，dynamic_ok=False，但仍会返回静态 fallback。
    """
    dynamic_items = fetch_all_dynamic_news(display_per_query=dynamic_display)
    sec_items = sec_client.fetch_all_sec_filings(display_per_ticker=sec_display_per_ticker)
    dynamic_ok = len(dynamic_items) > 0 or len(sec_items) > 0

    merged = list(dynamic_items)
    seen = {item.get("url", "") for item in merged}

    # 合并 SEC EDGAR filings
    for item in sec_items:
        url = item.get("url", "")
        if url and url in seen:
            continue
        if url:
            seen.add(url)
        merged.append(item)

    # 合并静态 fallback
    for item in STATIC_FALLBACK_NEWS:
        url = item.get("url", "")
        if url and url in seen:
            continue
        if url:
            seen.add(url)
        merged.append(item)

    # 按日期倒序；没有具体月日的条目排在最后
    def _sort_key(x: dict) -> str:
        d = x.get("date", "")
        return d if len(d) >= 7 else f"{d}-00-00"

    merged.sort(key=_sort_key, reverse=True)
    return merged, dynamic_ok
