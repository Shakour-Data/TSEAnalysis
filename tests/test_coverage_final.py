import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from app.services.tsetmc import TSETMCClient
from app.services.technical_analysis import TechnicalAnalyzer
from app.services.tgju import TGJUClient

@pytest.fixture
def tsetmc():
    return TSETMCClient(api_key="TEST")

def test_tsetmc_all_techniques_fail(tsetmc):
    with patch("tls_client.Session.get", side_effect=Exception("TLS")), \
         patch("subprocess.run", side_effect=Exception("Curl")), \
         patch("requests.get", side_effect=Exception("Req")):
        res = tsetmc._make_request("test")
        assert res is None

def test_tsetmc_get_price_history_adjusted(tsetmc):
    # Coverage for adjusted history branches
    with patch.object(TSETMCClient, "_make_request") as mock_m:
        mock_m.return_value = [{"date": "20230101", "pc": "100"}]
        res = tsetmc.get_price_history("SYMBOL", adjusted=True)
        assert len(res) > 0

def test_tsetmc_index_history_fallback(tsetmc):
    # Coverage for index history logic
    with patch.object(TSETMCClient, "_make_request") as mock_m:
        mock_m.return_value = {"error": "NotFound"}
        res = tsetmc.get_price_history("SYMBOL", service="index")
        assert isinstance(res, list)

def test_ta_full_cycle():
    # Enough data for all indicators
    data = []
    for i in range(100):
        data.append({
            'date': f'2023-01-{i//30+1:02d}-{i%30+1:02d}',
            'open': 100 + np.random.randn(),
            'high': 110 + np.random.randn(),
            'low': 90 + np.random.randn(),
            'close': 105 + np.random.randn(),
            'volume': 1000 + i
        })
    res = TechnicalAnalyzer.calculate_technical_analysis(data)
    assert 'Signal' in res[0]
    assert 'Pattern' in res[0]
    assert 'chart_image' in res[0]

def test_ta_weekly_resample():
    data = [{'date': f'2023-01-{i+1:02d}', 'open': 100, 'high': 105, 'low': 95, 'close': 101, 'volume': 1000} for i in range(20)]
    res = TechnicalAnalyzer.resample_to_weekly(data)
    assert len(res) < 20

def test_tgju_history_success():
    client = TGJUClient()
    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = {
            "s": "ok",
            "t": [1600000000],
            "o": [100], "h": [110], "l": [90], "c": [105], "v": [1000]
        }
        res = client.get_history("USD")
        assert len(res) > 0

def test_routes_error_handlers(client):
    # Trigger 404
    resp = client.get('/nonexistent_route_123')
    assert resp.status_code == 404
    
def test_routes_fetch_data_params(client):
    # Detailed fetch_data test
    with patch("app.api.routes.client.get_price_history") as mock_h:
        mock_h.return_value = [{'date': '2023-01-01', 'pc': 100, 'pf': 100, 'pmax': 100, 'pmin': 100, 'tvol': 100}] * 20
        resp = client.post('/api/fetch_data', json={
            "symbol": "TEST",
            "start_date": "2022/01/01",
            "timeframe": "weekly"
        })
        assert resp.status_code == 200
