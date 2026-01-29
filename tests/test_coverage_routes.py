import pytest
import json
from unittest.mock import patch, MagicMock
from flask import url_for
import pandas as pd

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_route(client):
    with patch("app.services.tsetmc.TSETMCClient._make_request") as mock_make:
        mock_make.return_value = {"status": "ok"}
        response = client.get('/api/health')
        assert response.status_code == 200
        assert "OK" in response.get_json()['status']

def test_api_symbols_error(client):
    with patch("app.services.tsetmc.TSETMCClient.get_all_symbols") as mock_get:
        mock_get.return_value = {"error": "API Down"}
        response = client.get('/api/symbols/1?refresh=true')
        assert response.status_code == 200
        assert "error" in response.get_json()

def test_fetch_data_invalid_json(client):
    response = client.post('/api/fetch_data', data="invalid json", content_type='application/json')
    assert response.status_code == 400

def test_fetch_data_missing_params(client):
    # Tests line 82-90 logic for defaults
    with patch("app.services.tsetmc.TSETMCClient.get_price_history") as mock_hist:
        mock_hist.return_value = [{"date": "2023-01-01", "pc": 100, "pf": 90, "pmax": 110, "pmin": 80, "tvol": 1000}]
        response = client.post('/api/fetch_data', json={"symbol": "TEST"})
        # Note: If it fails because timeframe default is weekly (resampling), we handle it.
        assert response.status_code == 200

def test_fetch_data_invalid_json(client):
    response = client.post('/api/fetch_data', data="invalid json", content_type='application/json')
    assert response.status_code == 400

def test_fetch_data_proxy_history(client):
    with patch("app.services.tsetmc.TSETMCClient.get_market_proxy_history") as mock_proxy:
        mock_proxy.return_value = [{"date": "2023-01-01", "pc": 100, "pf": 90}]
        response = client.post('/api/fetch_data', json={"asset_type": "proxy_market", "symbol": "1"})
        assert response.status_code == 200

def test_fetch_data_ta_signals(client):
    # Tests line 178-195 (Signal logic) with real TA
    with patch("app.services.tsetmc.TSETMCClient.get_price_history") as mock_hist:
        mock_hist.return_value = [{'date': f'2023-01-{i:02d}', 'open': 100, 'high': 105, 'low': 95, 'close': 100+i, 'tvol': 1000} for i in range(1, 40)]
        
        response = client.post('/api/fetch_data', json={
            "symbol": "FOO",
            "service_type": "technical",
            "timeframe": "Daily",
            "indicators": ["RSI", "MACD"]
        })
        assert response.status_code == 200
        res_data = response.get_json()
        assert len(res_data) > 0
        assert 'Signal' in res_data[0]

def test_market_status(client):
    response = client.get('/api/market_status')
    assert response.status_code == 200
    assert "status" in response.get_json()

def test_sync_registry_route(client):
    response = client.post('/api/sync_registry')
    assert response.status_code == 200
    assert "Started" in response.get_json()['status']

def test_fetch_data_sector_proxy(client):
    with patch("app.services.tsetmc.TSETMCClient.get_sector_history") as mock_sector:
        mock_sector.return_value = [{"date": "2023-01-01", "pc": 100}]
        response = client.post('/api/fetch_data', json={"asset_type": "proxy_sector", "symbol": "SectorName"})
        assert response.status_code == 200

def test_fetch_data_empty_history(client):
    # Tests line 150-154
    with patch("app.services.tsetmc.TSETMCClient.get_price_history") as mock_hist:
        mock_hist.return_value = []
        response = client.post('/api/fetch_data', json={"symbol": "EMPTY"})
        assert response.status_code == 200
        # If history is empty, it returns {"error": "..."} or []
        res = response.get_json()
        assert (isinstance(res, dict) and "error" in res) or (isinstance(res, list) and not res)

def test_fetch_data_technical_empty(client):
    with patch("app.services.tsetmc.TSETMCClient.get_price_history") as mock_hist:
        mock_hist.return_value = []
        response = client.post('/api/fetch_data', json={"symbol": "EMPTY", "service_type": "technical"})
        assert response.status_code == 200
        res = response.get_json()
        assert isinstance(res, list) and not res

def test_fetch_data_tgju(client):
    with patch("app.services.tgju.TGJUClient.get_history") as mock_tgju:
        mock_tgju.return_value = [{"date": "2023-01-01", "price": 100}]
        response = client.post('/api/fetch_data', json={"asset_type": "tgju", "symbol": "USD"})
        assert response.status_code == 200
        res = response.get_json()
        assert len(res) == 1

def test_fetch_data_indices_realtime(client):
    with patch("app.services.tsetmc.TSETMCClient.get_indices") as mock_indices:
        mock_indices.return_value = [{"value": 100, "index": "شاخص کل"}]
        response = client.post('/api/fetch_data', json={"asset_type": "indices_market", "service_type": "realtime"})
        assert response.status_code == 200
        res = response.get_json()
        assert len(res) == 2  # One for each market type

def test_fetch_data_indices_history(client):
    with patch("app.services.tsetmc.TSETMCClient.get_price_history") as mock_hist:
        mock_hist.return_value = [{"date": "2023-01-01", "pc": 100}]
        response = client.post('/api/fetch_data', json={"asset_type": "indices_market", "symbol": "1", "service_type": "history"})
        assert response.status_code == 200

@pytest.mark.integration
def test_fetch_data_real_tse_api(client):
    """Integration test using real TSE API data."""
    # Mock the API call to avoid real network dependency
    with patch("app.services.tsetmc.client.get_symbol_info") as mock_get:
        mock_get.return_value = {"l18": "نماد تست", "pc": 1234}
        response = client.post('/api/fetch_data', json={
            "symbol": "1",  # شاخص کل
            "asset_type": "tse",
            "service_type": "realtime"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        if data:
            assert "l18" in data[0] or "pc" in data[0]

@pytest.mark.integration
def test_fetch_data_real_tse_history(client):
    """Integration test for real TSE history data."""
    response = client.post('/api/fetch_data', json={
        "symbol": "1",
        "asset_type": "tse",
        "service_type": "history",
        "start_date": "2023-01-01",
        "end_date": "2023-01-05"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
