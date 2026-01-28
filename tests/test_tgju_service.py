import pytest
from unittest.mock import patch, MagicMock
from app.services.tgju import tgju_client

def test_tgju_get_all_symbols():
    # This method doesn't call requests.get, it returns hardcoded SYMBOLS
    symbols = tgju_client.get_all_symbols()
    assert len(symbols) > 0
    # The first one is typically Dollar
    assert "دلار آمریکا (آزاد)" in [s["l18"] for s in symbols]

def test_tgju_get_history():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        # Correct TGJU API format
        mock_get.return_value.json.return_value = {
            "s": "ok",
            "t": [1672531200], # 2023-01-01
            "o": [1000],
            "h": [1050],
            "l": [950],
            "c": [1020],
            "v": [5000]
        }
        
        history = tgju_client.get_history("price_dollar_rl")
        assert len(history) == 1
        assert history[0]["close"] == 1020
