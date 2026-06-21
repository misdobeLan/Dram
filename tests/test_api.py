"""后端 API 测试。"""
import json
import urllib.request


def _get_json(url: str):
    with urllib.request.urlopen(url, timeout=10) as resp:
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
