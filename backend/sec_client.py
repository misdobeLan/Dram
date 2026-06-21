"""SEC EDGAR 官方 filings 动态获取客户端。

为 US 持仓（Micron、SanDisk、Western Digital、Seagate）拉取最新 8-K、10-K、10-Q、DEF 14A 等
公开披露文件。SEC 数据免费、权威，无需 API key，但必须在请求头中设置合理的 User-Agent。
"""
import json
import logging
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SEC_DATA_URL = "https://data.sec.gov"
SEC_SUBMISSIONS_URL = f"{SEC_DATA_URL}/submissions"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# 美国持仓 ticker -> 用于展示的名称
US_HOLDINGS: dict[str, str] = {
    "MU": "Micron Technology Inc",
    "SNDK": "SanDisk Corp",
    "WDC": "Western Digital Corp",
    "STX": "Seagate Technology Holdings PLC",
}

# 关注的文件类型
INTERESTING_FORMS = {"8-K", "10-K", "10-Q", "DEF 14A", "SC 13D", "SC 13G", "424B2", "S-3", "S-4"}

# 缓存
class _SECCache:
    def __init__(self, ttl_seconds: int = 600):
        self.ttl_seconds = ttl_seconds
        self._cik_map: tuple[float, dict[str, str]] | None = None
        self._filings: dict[str, tuple[float, list[dict]]] = {}

    def get_cik_map(self) -> dict[str, str] | None:
        if self._cik_map is None:
            return None
        cached_at, data = self._cik_map
        if time.time() - cached_at > self.ttl_seconds:
            return None
        return data

    def set_cik_map(self, data: dict[str, str]) -> None:
        self._cik_map = (time.time(), data)

    def get_filings(self, ticker: str) -> list[dict] | None:
        if ticker not in self._filings:
            return None
        cached_at, data = self._filings[ticker]
        if time.time() - cached_at > self.ttl_seconds:
            self._filings.pop(ticker, None)
            return None
        return data

    def set_filings(self, ticker: str, data: list[dict]) -> None:
        self._filings[ticker] = (time.time(), data)


_cache = _SECCache(ttl_seconds=600)


def _request_json(url: str) -> dict | None:
    """带 SEC 合规 User-Agent 的 JSON 请求。"""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "DRAM Tracker research@dramtracker.local",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.warning(f"SEC HTTP error: {e.code} for {url}: {e.read().decode('utf-8', errors='ignore')[:200]}")
        return None
    except Exception as e:
        logger.warning(f"SEC request failed for {url}: {e}")
        return None


def _cik_to_str(cik: int) -> str:
    """CIK 需要补零到 10 位。"""
    return str(cik).zfill(10)


def fetch_cik_mapping() -> dict[str, str]:
    """获取 SEC ticker -> CIK 映射，带缓存。"""
    cached = _cache.get_cik_map()
    if cached is not None:
        return cached

    data = _request_json(SEC_TICKERS_URL)
    if not data:
        return {}

    mapping = {}
    for item in data.values():
        ticker = item.get("ticker", "").upper().strip()
        cik = item.get("cik_str")
        if ticker and cik is not None:
            mapping[ticker] = _cik_to_str(cik)

    _cache.set_cik_map(mapping)
    return mapping


def _format_filing_url(cik: str, accession: str, primary_doc: str) -> str:
    """构造 SEC filing 详情页 URL。"""
    cik_no_leading = str(int(cik))
    accession_clean = accession.replace("-", "")
    if primary_doc:
        return f"https://www.sec.gov/ix?doc=/Archives/edgar/data/{cik_no_leading}/{accession_clean}/{primary_doc}"
    return f"https://www.sec.gov/Archives/edgar/data/{cik_no_leading}/{accession_clean}/"


def _form_description(form: str) -> str:
    descriptions = {
        "8-K": "当前报告（重大事件或公司公告）",
        "10-K": "年度报告",
        "10-Q": "季度报告",
        "DEF 14A": "股东委托说明书",
        "SC 13D": "实益拥有权变动报告（13D）",
        "SC 13G": "实益拥有权报告（13G）",
        "424B2": "招股说明书补充文件",
        "S-3": "证券注册声明",
        "S-4": "并购/换股注册声明",
    }
    return descriptions.get(form, f"SEC 披露文件（{form}）")


def fetch_recent_filings(ticker: str, display: int = 5) -> list[dict]:
    """获取某只 US 股票最近的 SEC filings，返回 NewsItem 列表。"""
    cached = _cache.get_filings(ticker)
    if cached is not None:
        return cached

    mapping = fetch_cik_mapping()
    cik = mapping.get(ticker.upper())
    if not cik:
        logger.warning(f"No CIK found for ticker {ticker}")
        return []

    data = _request_json(f"{SEC_SUBMISSIONS_URL}/CIK{cik}.json")
    if not data:
        return []

    recent = data.get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])

    results = []
    for i in range(min(len(forms), display * 3)):
        form = forms[i]
        if form not in INTERESTING_FORMS:
            continue
        accession = accession_numbers[i]
        filing_date = dates[i]
        primary_doc = primary_docs[i] if i < len(primary_docs) else ""
        desc = descriptions[i] if i < len(descriptions) else ""

        company = US_HOLDINGS.get(ticker.upper(), ticker)
        title = f"{company} 提交 {form}"
        summary = _form_description(form)
        if desc:
            summary += f"：{desc}"

        results.append({
            "source": "SEC EDGAR",
            "date": filing_date,
            "title": title,
            "summary": summary,
            "url": _format_filing_url(cik, accession, primary_doc),
            "tickers": [ticker.upper()],
        })

        if len(results) >= display:
            break

    _cache.set_filings(ticker, results)
    return results


def fetch_all_sec_filings(display_per_ticker: int = 3) -> list[dict]:
    """获取所有 US 持仓的 SEC filings，按日期倒序返回。"""
    all_filings: list[dict] = []
    for ticker in US_HOLDINGS:
        try:
            all_filings.extend(fetch_recent_filings(ticker, display=display_per_ticker))
        except Exception as e:
            logger.warning(f"Failed to fetch SEC filings for {ticker}: {e}")

    all_filings.sort(key=lambda x: x.get("date", ""), reverse=True)
    return all_filings
