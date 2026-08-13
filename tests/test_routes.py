import pytest
import json
from unittest.mock import patch

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data

def test_market_status_route(client):
    response = client.get('/api/market_status')
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data
    assert "time" in data
    assert "stats" in data

@patch('app.services.tsetmc.client.get_all_symbols')
def test_get_symbols_route(mock_get, client):
    mock_get.return_value = [{"l18": "TEST", "isin": "ISIN1"}]
    
    response = client.get('/api/symbols/1')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["l18"] == "TEST"

@patch('app.services.tsetmc.client.get_symbol_info')
def test_fetch_data_realtime(mock_info, client):
    mock_info.return_value = {"l18": "FOOLAD", "pc": 1000}
    
    payload = {
        "symbol": "FOOLAD",
        "asset_type": "tse",
        "service_type": "realtime"
    }
    
    response = client.post('/api/fetch_data', 
                           data=json.dumps(payload),
                           content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["l18"] == "FOOLAD"

def test_health_check_route(client):
    with patch('app.services.tsetmc.client._make_request') as mock_req:
        mock_req.return_value = {"status": "success"}
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.json['status'] == "OK"

def test_clear_cache_route(client):
    response = client.post('/api/clear_cache')
    assert response.status_code == 200
    assert response.json['status'] == "success"

def test_sync_registry_route(client):
    with patch('threading.Thread'):
        response = client.post('/api/sync_registry')
        assert response.status_code == 200
        assert response.json['status'] == "Started"

def test_management_route(client):
    response = client.get('/management')
    assert response.status_code == 200

def test_ai_package_route(client):
    payload = {
        "symbol": "فولاد",
        "data": [{"date": "2023-01-01", "close": 1000, "Signal": "Bullish", "Pattern": "Doji", "supports": [900], "resistances": [1100]}],
        "weekly_data": []
    }
    response = client.post('/api/ai_package', json=payload)
    assert response.status_code == 200
    assert "markdown" in response.json

def test_download_comprehensive_route(client):
    payload = {
        "symbol": "فولاد",
        "daily_data": [{"date": "2023-01-01", "close": 1000}],
        "markdown": "Test Report"
    }
    response = client.post('/api/download_comprehensive', json=payload)
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/zip'
