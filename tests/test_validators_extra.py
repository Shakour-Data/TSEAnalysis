import pytest
from app.utils.validators import DataValidator

def test_validators_extra_coverage():
    # Test is_valid_price
    assert DataValidator.is_valid_price(100.5) == True
    assert DataValidator.is_valid_price(-1) == False
    assert DataValidator.is_valid_price(0) == False
    assert DataValidator.is_valid_price(None) == False
    assert DataValidator.is_valid_price("100") == True

    # Test is_valid_volume
    assert DataValidator.is_valid_volume(1000) == True
    assert DataValidator.is_valid_volume(0) == False
    assert DataValidator.is_valid_volume(-1) == False
    assert DataValidator.is_valid_volume(None) == False

    # Test is_valid_symbol
    assert DataValidator.is_valid_symbol("فولاد") == True
    assert DataValidator.is_valid_symbol("ABC") == True
    assert DataValidator.is_valid_symbol("a") == True
    assert DataValidator.is_valid_symbol("") == False
    assert DataValidator.is_valid_symbol(None) == False
    assert DataValidator.is_valid_symbol("a" * 100) == False  # Too long

    # Test is_valid_date
    assert DataValidator.is_valid_date("2023-01-01") == True
    assert DataValidator.is_valid_date("2023/01/01") == False
    assert DataValidator.is_valid_date("invalid") == False
    assert DataValidator.is_valid_date(None) == False

    # Test is_valid_number
    assert DataValidator.is_valid_number(5, 0, 10) == True
    assert DataValidator.is_valid_number(15, 0, 10) == False
    assert DataValidator.is_valid_number(-1, 0, 10) == False
    assert DataValidator.is_valid_number(5.5, 0, 10) == True
    assert DataValidator.is_valid_number(None, 0, 10) == False

    # Test ensure_non_empty_list
    assert DataValidator.ensure_non_empty_list([1, 2, 3], [4, 5]) == [1, 2, 3]
    assert DataValidator.ensure_non_empty_list([], [4, 5]) == [4, 5]
    assert DataValidator.ensure_non_empty_list(None, [4, 5]) == [4, 5]

    # Test ensure_non_empty_dict
    assert DataValidator.ensure_non_empty_dict({'a': 1}, {'b': 2}) == {'a': 1}
    assert DataValidator.ensure_non_empty_dict({}, {'b': 2}) == {'b': 2}
    assert DataValidator.ensure_non_empty_dict(None, {'b': 2}) == {'b': 2}

    # Test ensure_non_empty_string
    assert DataValidator.ensure_non_empty_string("test", "default") == "test"
    assert DataValidator.ensure_non_empty_string("", "default") == "default"
    assert DataValidator.ensure_non_empty_string("   ", "default") == "default"
    assert DataValidator.ensure_non_empty_string(None, "default") == "default"

    # Test validate_ohlcv_candle
    valid_candle = {
        "date": "2023-01-01",
        "open": 100,
        "high": 110,
        "low": 90,
        "close": 105,
        "volume": 1000
    }
    assert DataValidator.validate_ohlcv_candle(valid_candle) == True

    # Invalid cases
    assert DataValidator.validate_ohlcv_candle({}) == False
    assert DataValidator.validate_ohlcv_candle({"open": -1}) == False
    assert DataValidator.validate_ohlcv_candle({"open": 100, "high": 90}) == False  # high < low
    assert DataValidator.validate_ohlcv_candle({"open": 100, "volume": -1}) == False
    assert DataValidator.validate_ohlcv_candle(None) == False

    # Test filter_valid_candles
    candles = [valid_candle, {}, {"open": -1}, None]
    filtered = DataValidator.filter_valid_candles(candles)
    assert len(filtered) == 1
    assert filtered[0] == valid_candle