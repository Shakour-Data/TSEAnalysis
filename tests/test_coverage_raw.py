import pytest
from app.services.tsetmc import TSETMCClient
from app.services.technical_analysis import TechnicalAnalyzer
from app.core_utils import API_KEY
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

@pytest.fixture
def tsetmc_client():
    return TSETMCClient(api_key=API_KEY)

def test_tsetmc_get_symbols_indices(tsetmc_client):
    # Test indices_market
    with patch.object(TSETMCClient, "get_indices") as mock_idx:
        mock_idx.return_value = [{"l18": "Index1", "l30": "Full Index 1"}]
        res = tsetmc_client.get_all_symbols("indices_market")
        assert len(res) > 0
        assert any("Index1" in s["l18"] for s in res)

    # Test indices_industry
    with patch.object(TSETMCClient, "_get_equity_universe") as mock_univ:
        mock_univ.return_value = [{"l18": "S1", "cs": "Sector1"}]
        res = tsetmc_client.get_all_symbols("indices_industry")
        assert len(res) > 0
        assert res[0]["l18"] == "Sector1"

def test_tsetmc_mock_history(tsetmc_client):
    res = tsetmc_client._generate_mock_history("TEST", days=10)
    assert len(res) == 10
    assert "close" in res[0]
    assert "date" in res[0]

def test_technical_analysis_resample_weekly():
    data = []
    import datetime
    base = datetime.datetime(2023, 1, 1)
    for i in range(20):
        data.append({
            "date": (base + datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
            "open": 100 + i, "high": 110 + i, "low": 90 + i, "close": 105 + i, "volume": 1000
        })
    
    # Needs at least 5 items for resampling to kick in
    res = TechnicalAnalyzer.resample_to_weekly(data)
    # Weekly should be fewer records than daily
    assert len(res) < len(data)
    assert "close" in res[0]

def test_technical_analysis_prepare_ohlcv():
    data = [{"pc": 100, "pf": 90, "pmax": 110, "pmin": 85, "tvol": 1000}]
    res = TechnicalAnalyzer.prepare_ohlcv_data(data)
    assert res[0]["close"] == 100
    assert res[0]["open"] == 90
    assert res[0]["high"] == 110
    assert res[0]["low"] == 85
    assert res[0]["volume"] == 1000

def test_routes_fetch_data_weekly(client):
    # Mocking the client instance in routes
    with patch("app.api.routes.client.get_price_history") as mock_hist:
        mock_hist.return_value = [{"date": f"2023-01-{i+1:02d}", "pc": 100+i, "pf": 95+i} for i in range(30)]
        
        resp = client.post('/api/fetch_data', json={
            "symbol": "TEST",
            "asset_type": "1",
            "service_type": "technical",
            "timeframe": "weekly",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) > 0

def test_tsetmc_get_symbols_errors(tsetmc_client):
    # Test invalid market type
    res = tsetmc_client.get_all_symbols("invalid_market")
    assert res == []

def test_tsetmc_get_price_history_mock_fallback(tsetmc_client):
    with patch("app.services.tsetmc.db.get_history") as mock_get, \
         patch("app.services.tsetmc.db.save_history") as mock_save, \
         patch("app.services.tsetmc.TSETMCClient._make_request") as mock_req:
        
        mock_get.return_value = []
        mock_req.return_value = {"error": "Too many requests"}
        mock_save.return_value = True
        
        # This should trigger mock fallback
        res = tsetmc_client.get_price_history("TEST", force_refresh=True)
        assert isinstance(res, list)
        assert len(res) > 0

def test_tsetmc_techniques_coverage(tsetmc_client):
    # Cover the different fetch techniques in _make_request
    with patch("app.services.tsetmc.requests.get") as mock_get, \
         patch("app.services.tsetmc.update_stats") as mock_stats:
        
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"data": "ok"})
        
        # Force the loop to reach the requests.get technique (technique 2)
        # We can mock _locked_make_request to return None for first few attempts
        # Or just mock the libraries being unavailable
        with patch("app.services.tsetmc.TLS_CLIENT_AVAILABLE", False), \
             patch("app.services.tsetmc.CURL_CFFI_AVAILABLE", False):
            res = tsetmc_client._make_request("test_endpoint")
            assert res == {"data": "ok"}

def test_tsetmc_get_market_proxy(tsetmc_client):
    with patch.object(TSETMCClient, "get_all_symbols") as mock_all, \
         patch.object(TSETMCClient, "get_price_history") as mock_hist:
        
        mock_all.return_value = [{"isin": "I1", "l18": "S1", "mv": 1000}]
        mock_hist.return_value = [
            {"date": "2023-01-01", "pc": 100, "pf": 100, "pmax": 100, "pmin": 100, "tvol": 1000}
        ]
        
        res = tsetmc_client.get_market_proxy_history("1")
        assert isinstance(res, list)
        if len(res) > 0:
            assert "pc" in res[0]

def test_tsetmc_get_sector_history(tsetmc_client):
    with patch.object(TSETMCClient, "get_all_symbols") as mock_all, \
         patch.object(TSETMCClient, "get_price_history") as mock_hist:
        
        mock_all.return_value = [{"isin": "I1", "l18": "S1", "cs": "Sector1", "mv": 1000}]
        mock_hist.return_value = [
            {"date": "2023-01-01", "pc": 100, "pf": 100, "pmax": 100, "pmin": 100, "tvol": 1000}
        ]
        
        res = tsetmc_client.get_sector_history("Sector1")
        assert len(res) > 0


def test_tsetmc_classify_equity_market_edge_cases(tsetmc_client):
    # Case with missing ISIN but valid CS
    res = tsetmc_client._classify_equity_market({"isin": "", "cs": "Sector", "l18": "Symbol"})
    assert isinstance(res, str)

def test_core_utils_stats_endpoint():
    from app.core_utils import update_stats, stats
    update_stats("test_svc", "success", endpoint="api/test")
    found = False
    for h in stats["history"]:
        if h["endpoint"] == "api/test":
            found = True
            break
    assert found

def test_tgju_history_error():
    from app.services.tgju import TGJUClient
    client = TGJUClient()
    with patch("app.services.tgju.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"s": "no_data"})
        res = client.get_history("USD")
        assert "error" in res

def test_routes_ai_package(client):
    resp = client.post("/api/ai_package", json={
        "symbol": "TEST",
        "data": [{"close": 100, "Signal": "Buy", "RSI": 25}],
        "weekly_data": []
    })
    assert resp.status_code == 200
    assert "markdown" in resp.get_json()

def test_core_utils_stats_errors():
    from app.core_utils import update_stats, stats
    update_stats('tsetmc', 'blocked')
    update_stats('tgju', 'success')
    assert stats['services']['tsetmc']['blocked'] > 0

def test_tgju_get_symbols_exception():
    from app.services.tgju import TGJUClient
    client = TGJUClient()
    # Mocking inside the service module's reference to requests
    with patch("app.services.tgju.requests.get") as mock_get:
        mock_get.side_effect = Exception("error")
        res = client.get_all_symbols()
        assert isinstance(res, list) # Fallback returns predefined list
