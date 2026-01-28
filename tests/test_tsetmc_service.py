import pytest
from unittest.mock import patch, MagicMock
from app.services.tsetmc import TSETMCClient

@pytest.fixture
def tsetmc_client():
    return TSETMCClient(api_key="test_key")

def test_normalize_text(tsetmc_client):
    assert tsetmc_client._normalize_text(" ي ك ") == "ی ک"
    assert tsetmc_client._normalize_text(None) == ""

def test_classify_equity_market(tsetmc_client):
    # Test Bourse
    assert tsetmc_client._classify_equity_market({"isin": "IRO1BMLT0001"}) == "bourse"
    # Test Farabourse
    assert tsetmc_client._classify_equity_market({"isin": "IRO3..."}) == "farabourse"
    # Test Base
    assert tsetmc_client._classify_equity_market({"isin": "IRO7..."}) == "base"
    # Test ETF
    assert tsetmc_client._classify_equity_market({"isin": "IRO5...", "cs_id": "68"}) == "etf"
    # Test Fixed Income
    assert tsetmc_client._classify_equity_market({"isin": "IRO2...", "cs_id": "69"}) == "fixed_income"

def test_get_all_symbols_filtering(tsetmc_client):
    with patch.object(tsetmc_client, '_get_equity_universe') as mock_universe:
        mock_universe.return_value = [
            {"isin": "IRO1_B", "l18": "Bourse1"},
            {"isin": "IRO3_F", "l18": "Fara1"},
            {"isin": "IRO7_P", "l18": "Payeh1"},
        ]
        
        # Test Bourse filter
        bourse = tsetmc_client.get_all_symbols("1")
        assert len(bourse) == 1
        assert bourse[0]["l18"] == "Bourse1"
        
        # Test Farabourse filter
        fara = tsetmc_client.get_all_symbols("2")
        assert len(fara) == 1
        assert fara[0]["l18"] == "Fara1"

@patch('app.services.tsetmc.crequests')
def test_make_request_success(mock_crequests, tsetmc_client):
    mock_crequests.get.return_value.status_code = 200
    mock_crequests.get.return_value.json.return_value = [{"isin": "TEST"}]
    
    # We need to mock _apply_fair_use_control to speed up tests
    with patch.object(tsetmc_client, '_apply_fair_use_control'):
        res = tsetmc_client._make_request("test_endpoint")
        assert res == [{"isin": "TEST"}]

def test_get_price_history(tsetmc_client):
    with patch.object(tsetmc_client, '_make_request') as mock_req:
        # Return list directly to avoid dict-flattening logic issues in test
        mock_req.return_value = [
            {"date": "2023-01-01", "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000},
            {"date": "2023-01-02", "open": 105, "high": 115, "low": 100, "close": 112, "volume": 1200}
        ]
        
        with patch('app.database.db.save_history'):
            with patch('app.database.db.get_history') as mock_db_get:
                # First call returns empty, second call returns our data (simulating save/load)
                mock_db_get.side_effect = [[], mock_req.return_value]
                history = tsetmc_client.get_price_history("123", adjusted=False)
                assert len(history) == 2
                assert history[0]["close"] == 105

def test_get_indices(tsetmc_client):
    with patch.object(tsetmc_client, '_make_request') as mock_req:
        mock_req.return_value = {"index": " شاخص کل ", "value": "2,100,000"}
        
        with patch('app.database.db.get_symbols_by_market') as mock_db_get:
            mock_db_get.side_effect = [[], [mock_req.return_value]]
            with patch('app.database.db.save_symbols'):
                indices = tsetmc_client.get_indices(1)
                assert len(indices) == 1
                assert indices[0]["index"] == " شاخص کل "

def test_fetch_symbols_by_type(tsetmc_client):
    with patch.object(tsetmc_client, '_make_request') as mock_req:
        mock_req.return_value = [
            {"i": "1", "l18": "Symbol1", "isin": "IRO1...", "cs": "1"},
            {"i": "2", "l18": "Symbol2", "isin": "IRO3...", "cs": "2"}
        ]
        
        with patch('app.database.db.save_symbols'):
            with patch('app.database.db.clear_symbols'):
                # Force refresh to bypass DB check
                symbols = tsetmc_client._fetch_symbols_by_type("1", force_refresh=True)
                assert len(symbols) == 2
                assert symbols[0]["i"] == "1"

