import pytest
import pandas as pd
import numpy as np
import os
import io
import base64
import json
import time
import logging
from datetime import datetime, timedelta
from PIL import Image
from unittest.mock import patch

# Import all utility classes
from app.utils.core_utils import CoreUtils, DateFormatter, update_stats, _get_api_key
from app.utils.validators import DataValidator
from app.utils.nan_handler import NaNHandler
from app.utils.encoding_utils import EncodingHandler
from app.utils.duplicate_handler import DuplicateHandler
from app.utils.chart_optimizer import ChartOptimizer
from app.utils.enhanced_logger import EnhancedLogger, get_app_logger, get_api_logger, get_db_logger, get_service_logger
from app.services.rate_limiter import SmartRateLimiter

# --- Comprehensive Test Suite for app/utils ---

# 1. CoreUtils Tests
def test_core_utils_full_coverage():
    """Covers all branches in core_utils.py"""
    # safe_round
    assert CoreUtils.safe_round(1.2345, 2) == 1.23
    assert CoreUtils.safe_round(None) == 0.0
    assert CoreUtils.safe_round("not-a-number") == 0.0

    # get_nested_value
    nested_dict = {"a": {"b": {"c": 1}}, "x": [10, 20]}
    assert CoreUtils.get_nested_value(nested_dict, "a.b.c") == 1
    assert CoreUtils.get_nested_value(nested_dict, "a.b.d", "default") == "default"
    assert CoreUtils.get_nested_value(nested_dict, "x.0") is None # Not supported
    assert CoreUtils.get_nested_value(None, "a.b") is None
    assert CoreUtils.get_nested_value(nested_dict, "") is None

    # is_numeric
    assert CoreUtils.is_numeric(123) == True
    assert CoreUtils.is_numeric("123.45") == True
    assert CoreUtils.is_numeric("abc") == False
    assert CoreUtils.is_numeric(None) == False
    assert CoreUtils.is_numeric([1]) == False

    # format_number
    assert CoreUtils.format_number(12345, "تومان") == "12,345 تومان"
    assert CoreUtils.format_number(None) == "0"
    assert CoreUtils.format_number("N/A") == "N/A"
    assert CoreUtils.format_number(12345, "تومان", persian_digits=True) == "۱۲,۳۴۵ تومان"

    # update_stats & _get_api_key
    for status in ["success", "fail", "timeout", "blocked", "unknown_status"]:
        update_stats("test_stat", status)
        
        with patch('app.utils.core_utils.os.getenv', return_value='test_api_key'):
            assert _get_api_key() == 'test_api_key'
    """Covers all branches in DateFormatter"""
    assert DateFormatter.to_gregorian("1401-05-10") == "2022-08-01"
    assert DateFormatter.to_gregorian(None) is None
    assert DateFormatter.to_gregorian("invalid-date") is None

    assert DateFormatter.to_jalali("2022-08-01") == "1401-05-10"
    assert DateFormatter.to_jalali(None) is None
    assert DateFormatter.to_jalali("invalid-date") is None

    assert isinstance(DateFormatter.get_gregorian_today(), str)
    assert isinstance(DateFormatter.get_jalali_today(), str)

    assert DateFormatter.add_days("2023-01-01", 10) == "2023-01-11"
    assert DateFormatter.add_days("1401-01-01", 10, 'jalali') is not None
    assert DateFormatter.add_days("invalid", 1) is None

    assert len(DateFormatter.date_range("2023-01-01", "2023-01-05")) == 5
    assert DateFormatter.date_range("invalid", "2023-01-01") == []
    assert DateFormatter.date_range("2023-01-01", "invalid") == []

# 3. DataValidator Tests
def test_data_validator_full_coverage():
    """Covers all branches in validators.py"""
    assert DataValidator.is_valid_price(100) and not DataValidator.is_valid_price(-1)
    assert not DataValidator.is_valid_price(None)
    assert DataValidator.is_valid_volume(1000) and not DataValidator.is_valid_volume(-1)
    assert not DataValidator.is_valid_volume(None)
    assert DataValidator.is_valid_symbol("فولاد") and not DataValidator.is_valid_symbol("a"*100)
    assert not DataValidator.is_valid_symbol(None) and not DataValidator.is_valid_symbol("")
    assert DataValidator.is_valid_date("2024-01-01") and not DataValidator.is_valid_date("2024/01/01")
    assert not DataValidator.is_valid_date(None)
    assert DataValidator.is_valid_number(5, 0, 10) and not DataValidator.is_valid_number(15, 0, 10)
    assert not DataValidator.is_valid_number(None, 0, 10)
    assert DataValidator.ensure_non_empty_list(None, [1]) == [1]
    assert DataValidator.ensure_non_empty_dict(None, {"a":1}) == {"a":1}
    assert DataValidator.ensure_non_empty_string(" ", "def") == "def"
    candle = {"date": "2023-01-01", "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000}
    assert DataValidator.validate_ohlcv_candle(candle)
    assert not DataValidator.validate_ohlcv_candle({"open": -1})
    assert not DataValidator.validate_ohlcv_candle(None)
    assert len(DataValidator.filter_valid_candles([candle, None, {"open":0}])) == 1

# 4. NaNHandler Tests
def test_nan_handler_full_coverage():
    """Covers all branches in nan_handler.py"""
    assert NaNHandler.has_nan(np.nan) and not NaNHandler.has_nan(1)
    assert NaNHandler.has_nan(pd.Series([1, np.nan]))
    df = pd.DataFrame({'a': [1, np.nan, np.inf], 'b': [np.nan, 5, 6]})
    NaNHandler.replace_inf_nan(df)
    assert not df.isin([np.inf, -np.inf]).any().any()
    for strategy in ['zero', 'drop', 'mean', 'forward_fill', 'backward_fill', 'unknown']:
        NaNHandler.clean_dataframe_nan(df.copy(), strategy)
    NaNHandler.clean_dataframe_nan(None)
    NaNHandler.clean_dict_nan({'a': np.nan, 'b': [1, np.nan]})
    assert NaNHandler.get_nan_statistics(df)['total_nan'] >= 0
    assert NaNHandler.get_nan_statistics(None)['total_nan'] == 0
    ohlcv_df = pd.DataFrame({'open': [100, np.nan], 'close': [101, 102]})
    NaNHandler.handle_ohlcv_nan(ohlcv_df)
    assert not ohlcv_df.isna().any().any()
    NaNHandler.validate_numeric_column(df.copy(), 'a', 'interpolate')

# 5. EncodingHandler Tests
def test_encoding_handler_full_coverage():
    """Covers all branches in encoding_utils.py"""
    assert EncodingHandler.safe_encode("تست") == "تست"
    assert EncodingHandler.safe_decode(b'\xff\xfe', 'utf-16') is not None
    assert EncodingHandler.safe_decode(123) == "123"
    assert EncodingHandler.normalize_unicode("ی") is not None
    assert EncodingHandler.normalize_unicode(123) == 123
    assert EncodingHandler.remove_control_characters("a\x00b") == "ab"
    assert EncodingHandler.remove_control_characters(123) == 123
    assert EncodingHandler.detect_encoding(b'\xc7\x84\xc7\x81\xc7\x84\xc7\x85') == 'utf-8'
    assert EncodingHandler.safe_json_dumps(datetime.now()) is not None
    result = EncodingHandler.safe_json_loads('{"a":1}')
    assert result is not None and result["a"] == 1  # type: ignore[index]
    assert EncodingHandler.sanitize_string(" test ", 3, ellipsis="") == "tes"
    assert EncodingHandler.sanitize_string(123) == "123"
    assert EncodingHandler.urlencode_safely("a/b") == "a%2Fb"
    assert EncodingHandler.urldecode_safely("a%2Fb") == "a/b"
    assert EncodingHandler.clean_symbol_string("فولاد(مبارکه)") == "فولادمبارکه"
    assert EncodingHandler.clean_symbol_string(123) == "123"

# 6. DuplicateHandler Tests
def test_duplicate_handler_full_coverage():
    """Covers all branches in duplicate_handler.py"""
    data = [{"id": 1, "v": 10}, {"id": 1, "v": 20}, {"id": 2, "v": 30}]
    DuplicateHandler.find_duplicates(data, "id")
    DuplicateHandler.merge_duplicates(data, "id", 'keep_latest')
    DuplicateHandler.merge_duplicates(data, "id", 'merge_data')
    DuplicateHandler.detect_similar_entries(data, "id")
    d1, d2 = {"a": 1, "b": [1]}, {"b": [2], "c": 3}
    merged = DuplicateHandler._merge_dicts(d1, d2)
    assert merged["c"] == 3 and len(merged["b"]) == 2
    coll = []
    DuplicateHandler.update_or_insert(coll, "id", {"id": 1, "val": 10})
    DuplicateHandler.update_or_insert(coll, "id", {"id": 1, "val": 20})
    assert len(coll) == 1 and coll[0]["val"] == 20
    DuplicateHandler.batch_upsert(coll, "id", [{"id": 2}, {"id": 3}])
    assert len(coll) == 3

# 7. ChartOptimizer Tests
def test_chart_optimizer_full_coverage():
    """Covers all branches in chart_optimizer.py"""
    # Create a dummy image for testing
    img = Image.new('RGB', (2500, 2500), color = 'red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    # Test optimization - this will trigger resizing and quality reduction
    optimized_buf = ChartOptimizer.optimize_image_size(buf, max_size_kb=50)
    assert len(optimized_buf.getvalue()) < len(buf.getvalue())
    
    # Test other functions
    b64_str = ChartOptimizer.encode_chart_to_base64(optimized_buf)
    assert isinstance(b64_str, str)
    assert ChartOptimizer.encode_chart_to_base64(None) is None
    
    key = ChartOptimizer.get_chart_cache_key("sym", "type", "1Y", "1d")
    ChartOptimizer.cache_chart(key, b64_str)
    assert ChartOptimizer.get_cached_chart(key) is not None
    
    ChartOptimizer.set_chart_cache_ttl(0.01)
    time.sleep(0.02)
    ChartOptimizer.cleanup_expired_charts()
    assert ChartOptimizer.get_cached_chart(key) is None
    
    assert ChartOptimizer.estimate_data_points("1Y", "1d") > 300

    ChartOptimizer.get_chart_stats()
    ChartOptimizer.clear_chart_cache()

# 8. EnhancedLogger Tests
def test_enhanced_logger_full_coverage():
    """Covers all branches in enhanced_logger.py"""
    logger = EnhancedLogger.setup_logging("master_test")
    assert logger is not None
    
    EnhancedLogger.log_event(logger, "TEST_EVENT", data={"key": "value"})
    EnhancedLogger.log_event(None, "NULL_LOGGER") # Should not crash
    
    EnhancedLogger.log_api_call(logger, "/master", "POST", 201, 120.5)
    EnhancedLogger.log_database_operation(logger, "INSERT", "users", 15.2, affected_rows=1)
    EnhancedLogger.log_performance(logger, "complex_calc", 500.7)
    EnhancedLogger.log_error_with_context(logger, ValueError("Test Error"), {"user_id": 123})
    
    assert isinstance(EnhancedLogger.get_log_files(), list)
    assert isinstance(EnhancedLogger.get_log_summary(), dict)
    EnhancedLogger.clear_old_logs(days_to_keep=0)
    
    # Test getters
    assert get_app_logger() is not None
    assert get_api_logger() is not None
    assert get_db_logger() is not None
    assert get_service_logger("my_service") is not None

# 9. SmartRateLimiter Tests
# def test_rate_limiter_full_coverage():
#     """Covers all branches in rate_limiter.py"""
#     limiter = SmartRateLimiter(base_delay=0.01, max_delay=0.1, backoff_factor=2)
#
#     # Initial state
#     assert limiter.current_delay == 0.01
#
#     # Success should reset delay
#     limiter.on_failure(429) # Increase delay
#     assert limiter.current_delay > 0.01
#     limiter.on_success()
#     assert limiter.current_delay == 0.01
#
#     # Failure should increase delay
#     limiter.on_failure(429)
#     delay1 = limiter.current_delay
#     limiter.on_failure(503)
#     delay2 = limiter.current_delay
#     assert delay2 > delay1
#
#     # Max delay should be respected
#     for _ in range(10):
#         limiter.on_failure(429)
#     assert limiter.current_delay <= limiter.max_delay
#
#     # Wait function
#     with patch('time.sleep') as mock_sleep:
#         limiter.current_delay = 0.02
#         limiter.last_request_time = time.time() - 1
#         limiter.wait_before_request()
#         mock_sleep.assert_called_once()
