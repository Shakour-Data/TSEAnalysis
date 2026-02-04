import pytest
import os
import json
from app.database import SymbolDatabase

def test_db_initialization(tmp_path):
    db_file = tmp_path / "test.db"
    db = SymbolDatabase(db_path=str(db_file))
    assert os.path.exists(str(db_file))
    
    # Check if tables exist
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='symbols'")
        assert cursor.fetchone() is not None
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='price_history'")
        assert cursor.fetchone() is not None

def test_save_and_get_symbols(tmp_path):
    db_file = tmp_path / "test_symbols.db"
    db = SymbolDatabase(db_path=str(db_file))
    
    symbols = [
        {"isin": "ISIN1", "l18": "SYM1", "l30": "NAME1", "id": 1},
        {"isin": "ISIN2", "l18": "SYM2", "l30": "NAME2", "id": 2}
    ]
    
    db.save_symbols(symbols, "market1")
    
    stored = db.get_symbols_by_market("market1")
    assert len(stored) == 2
    assert stored[0]["isin"] == "ISIN1"
    assert stored[1]["l18"] == "SYM2"

def test_save_and_get_history(tmp_path):
    db_file = tmp_path / "test_history.db"
    db = SymbolDatabase(db_path=str(db_file))
    
    # Ensure tables are initialized (SymbolDatabase._init_db should do this)
    with db._get_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS price_history (symbol TEXT, date TEXT, close REAL, vol REAL)")
        conn.commit()

    history = [
        {"date": "2023-01-01", "close": 100, "vol": 10},
        {"date": "2023-01-02", "close": 110, "vol": 20}
    ]
    
    db.save_history("TEST_SYM", history)
    
    stored = db.get_history("TEST_SYM")
    assert len(stored) == 2
    assert stored[0]["date"] == "2023-01-01"
    assert stored[1]["close"] == 110

def test_save_symbols_without_isin(tmp_path):
    db_file = tmp_path / "test_no_isin.db"
    db = SymbolDatabase(db_path=str(db_file))
    
    symbols = [
        {"l30": "NAME1"},  # no isin, l18, id
        {"isin": "ISIN2", "l18": "SYM2", "l30": "NAME2"}
    ]
    
    db.save_symbols(symbols, "market1")
    
    stored = db.get_symbols_by_market("market1")
    assert len(stored) == 1  # only the one with isin
    assert stored[0]["isin"] == "ISIN2"
    
    # Note: No history data saved in this test, so get_latest_date returns None
    # This assertion was incorrect as no data was inserted for "TEST_SYM"

def test_clear_and_empty_check(tmp_path):
    db_file = tmp_path / "test_ops.db"
    db = SymbolDatabase(db_path=str(db_file))
    
    assert db.is_market_empty("market1") is True
    
    db.save_symbols([{"isin": "I1"}], "market1")
    assert db.is_market_empty("market1") is False
    
    db.clear_symbols("market1")
    assert db.is_market_empty("market1") is True
