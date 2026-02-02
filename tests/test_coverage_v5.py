import pytest
from unittest.mock import patch, MagicMock 
from app.services.tsetmc import TSETMCClient
from app.services.tgju import TGJUClient
from app.services.technical_analysis import TechnicalAnalyzer
import pandas as pd
import io
import json

@pytest.fixture
def tsetmc_client():
    return TSETMCClient("test_key")

def test_tsetmc_classification_robust(tsetmc_client):
    test_cases = [
        ({"isin": "IRO5"}, "etf"),
        ({"cs_id": "68"}, "etf"),
        ({"isin": "IRO2"}, "fixed_income"),
        ({"isin": "IROL"}, "tashilat"),
        ({"isin": "IRO7"}, "base"),
        ({"isin": "IRO3"}, "farabourse"),
        ({"isin": "IRO1"}, "bourse"),
    ]
    for inp, expected in test_cases:
        res = tsetmc_client._classify_equity_market(inp)
        if expected == "base" and res.lower() == "base": continue
        assert res.lower() == expected.lower()

def test_tsetmc_retries_and_bridge(tsetmc_client):
    with patch("requests.get") as mock_get:
        # Test Bridge success
        mock_bridge = MagicMock(status_code=200)
        mock_bridge.text = '[{"isin": "TEST"}]'
        mock_bridge.json.return_value = [{"isin": "TEST"}]
        
        with patch("app.services.tsetmc.BRIDGE_URL", "http://bridge"):
            mock_get.return_value = mock_bridge
            res = tsetmc_client._make_request("test")
            assert res == [{"isin": "TEST"}]

        # Test retry logic
        mock_get.reset_mock()
        mock_resp_fail = MagicMock(status_code=429)
        mock_resp_ok = MagicMock(status_code=200)
        mock_resp_ok.text = '{"data": "ok"}'
        mock_resp_ok.json.return_value = {"data": "ok"}
        mock_get.side_effect = [mock_resp_fail, mock_resp_ok, mock_resp_ok, mock_resp_ok, mock_resp_ok]
        
        with patch("app.services.tsetmc.BRIDGE_URL", None), patch("time.sleep"):
            res = tsetmc_client._make_request("test")
            assert res == {"data": "ok"}

def test_routes_indices_and_history(client):
    with patch("app.services.tsetmc.client.get_indices") as mock_indices, \
         patch("app.services.tsetmc.client.get_price_history") as mock_hist:
        
        mock_indices.return_value = [{"value": 2000000}]
        resp = client.post("/api/fetch_data", json={
            "asset_type": "indices_market",
            "service_type": "realtime",
            "symbol": "شاخص کل",
            "refresh": True
        })
        assert resp.status_code == 200
        
        mock_hist.return_value = [{"date": "2023-01-01", "pc": 2000000}]
        resp = client.post("/api/fetch_data", json={
            "asset_type": "indices_market",
            "service_type": "history",
            "symbol": "شاخص کل",
            "refresh": True
        })
        assert resp.status_code == 200

def test_comprehensive_zip_full(client):
    test_data = [{"date": "2023-01-01", "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000}]
    resp = client.post("/api/download_comprehensive", json={
        "symbol": "TEST",
        "daily_data": test_data,
        "weekly_data": test_data,
        "markdown": "# Report"
    })
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/zip"

def test_strategy_matrix_direct():
    supports = [{"value": 100, "strength": 1}, {"value": 90, "strength": 0.5}]
    resistances = [{"value": 110, "strength": 1}, {"value": 120, "strength": 0.5}, {"value": 130, "strength": 0.3}]
    strategies = TechnicalAnalyzer.generate_strategy_matrix(105, supports, resistances)
    assert len(strategies) > 0

def test_technical_analysis_edge_cases():
    res = TechnicalAnalyzer.calculate_technical_analysis([])
    assert res == []
    
    # Use 60 items to satisfy all minimum requirements (RSI needs 14, SMA needs 50, etc.)
    data = [{"date": f"2023-01-{i+1:02d}", "open": 100+i, "high": 110+i, "low": 90+i, "close": 105+i, "volume": 1000} for i in range(60)]
    res = TechnicalAnalyzer.calculate_technical_analysis(data)
    assert len(res) == 60
    assert "Signal" in res[0]
    assert "Pattern" in res[0]

def test_core_utils_stats():
    from app.utils.core_utils import update_stats, stats
    update_stats("test", "success")
    assert stats["services"]["test"]["success"] >= 1
def test_tsetmc_complex_methods(tsetmc_client):
    with patch.object(TSETMCClient, "get_all_symbols") as mock_all, \
         patch.object(TSETMCClient, "get_price_history") as mock_hist:
        mock_all.return_value = [{"l18": "S1", "cs": "C1", "mv": 1000}]
        mock_hist.return_value = [{"date": "2023-01-01", "pc": 100}]
        res = tsetmc_client.get_sector_history("C1")
        assert len(res) > 0

def test_app_404(client):
    resp = client.get("/non_existent_page")
    assert resp.status_code == 404
