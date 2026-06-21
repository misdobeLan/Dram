"""后端 API 测试。"""
import json
import urllib.request


def _get_json(url_or_req):
    with urllib.request.urlopen(url_or_req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_health(backend_server):
    data = _get_json(f"{backend_server}/api/health")
    assert "connected" in data
    assert "resolved_codes" in data


def test_holdings(backend_server):
    data = _get_json(f"{backend_server}/api/holdings")
    assert "holdings" in data
    assert len(data["holdings"]) > 0
    for h in data["holdings"]:
        assert "ticker" in h
        assert "weight" in h
        assert "futu_code" in h


def test_quote_requires_connection(backend_server):
    try:
        data = _get_json(f"{backend_server}/api/quote")
    except urllib.error.HTTPError as e:
        if e.code == 503:
            return
        raise
    assert "timestamp" in data
    assert "quotes" in data
    for q in data["quotes"]:
        assert "code" in q
        assert "price" in q


def test_kline_requires_connection(backend_server):
    url = f"{backend_server}/api/kline?code=US.MU&ktype=1d&num=10"
    try:
        data = _get_json(url)
    except urllib.error.HTTPError as e:
        if e.code == 503:
            return
        raise
    assert data["code"] == "US.MU"
    assert data["ktype"] == "1d"
    assert isinstance(data["records"], list)


def test_korean_search_endpoint(backend_server):
    """/api/korean/search 应返回韩国股票搜索结果。"""
    url = f"{backend_server}/api/korean/search?q=005930&bas_dd=20250619"
    data = _get_json(url)
    assert data["query"] == "005930"
    assert data["count"] > 0
    codes = {item.get("code") for item in data["items"]}
    assert "005930" in codes


def test_news_endpoint(backend_server):
    """/api/news 应返回动态或静态 fallback 新闻列表，并附带情感分析。"""
    data = _get_json(f"{backend_server}/api/news")
    assert "dynamic" in data
    assert "items" in data
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert "source" in item
        assert "title" in item
        assert "url" in item
        assert "tickers" in item
        assert "sentiment" in item
        assert item["sentiment"]["sentiment"] in {"bullish", "bearish", "neutral"}
        assert isinstance(item["sentiment"]["score"], (int, float))
        assert -1.0 <= item["sentiment"]["score"] <= 1.0


def test_analyze_sentiment_endpoint(backend_server):
    """/api/analyze-sentiment 应返回情感分析结果。"""
    url = f"{backend_server}/api/analyze-sentiment"
    payload = json.dumps({
        "title": "Micron 财报大涨，HBM 需求强劲",
        "summary": "Micron 本季营收超预期，股价飙升 10%。",
        "tickers": ["MU"],
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    data = _get_json(req)
    assert data["sentiment"] == "bullish"
    assert data["score"] > 0
    assert len(data["reasons"]) > 0
