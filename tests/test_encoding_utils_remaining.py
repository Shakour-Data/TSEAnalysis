import pytest
from app.utils.encoding_utils import EncodingHandler

def test_encoding_utils_remaining_coverage():
    """Test remaining uncovered parts of EncodingHandler"""

    # Test safe_encode with various inputs
    # Test bytes input
    result = EncodingHandler.safe_encode(b'hello')
    assert result == 'hello'

    # Test None input
    assert EncodingHandler.safe_encode(None) is None

    # Test string with special characters
    result = EncodingHandler.safe_encode("مرحبا")
    assert result == "مرحبا"

    # Test safe_decode with various encodings
    # Test with utf-8
    result = EncodingHandler.safe_decode("مرحبا".encode('utf-8'), 'utf-8')
    assert result == "مرحبا"

    # Test with None encoding (should use utf-8)
    result = EncodingHandler.safe_decode("hello".encode('utf-8'))
    assert result == "hello"

    # Test normalize_unicode with None input
    assert EncodingHandler.normalize_unicode(None) is None

    # Test normalize_unicode with empty string
    assert EncodingHandler.normalize_unicode("") == ""

    # Test remove_control_characters with various inputs
    assert EncodingHandler.remove_control_characters("hello\nworld") == "hello\nworld"
    assert EncodingHandler.remove_control_characters("hello\x00world") == "helloworld"
    assert EncodingHandler.remove_control_characters(None) is None

    # Test safe_json_dumps with various inputs
    result = EncodingHandler.safe_json_dumps(None)
    assert result is not None  # Should return error message

    # Test safe_json_dumps with datetime
    from datetime import datetime
    result = EncodingHandler.safe_json_dumps({"date": datetime(2023, 1, 1)})
    assert '"2023-01-01T00:00:00"' in result

    # Test safe_json_loads with various inputs
    assert EncodingHandler.safe_json_loads(None) is None
    assert EncodingHandler.safe_json_loads("") is None
    assert EncodingHandler.safe_json_loads("invalid json") is None

    # Test safe_json_loads with bytes
    result = EncodingHandler.safe_json_loads(b'{"test": 123}')
    assert result == {"test": 123}

    # Test sanitize_string with various inputs
    assert EncodingHandler.sanitize_string(None) == "None"
    assert EncodingHandler.sanitize_string(123.45) == "123.45"
    assert EncodingHandler.sanitize_string("  test  ") == "test"
    assert EncodingHandler.sanitize_string("verylongstringthatshouldbetruncated", 10) == "verylongst..."

    # Test urlencode_safely with various inputs
    assert EncodingHandler.urlencode_safely("hello world") == "hello%20world"
    assert EncodingHandler.urlencode_safely("") == ""
    assert EncodingHandler.urlencode_safely("normal_string") == "normal_string"

    # Test urldecode_safely with various inputs
    assert EncodingHandler.urldecode_safely("hello%20world") == "hello world"
    assert EncodingHandler.urldecode_safely("") == ""
    assert EncodingHandler.urldecode_safely("normal_string") == "normal_string"

    # Test clean_symbol_string with various inputs
    assert EncodingHandler.clean_symbol_string("TEST(123)") == "TEST123"
    assert EncodingHandler.clean_symbol_string("test_123") == "test_123"
    assert EncodingHandler.clean_symbol_string("test@#$%") == "test"
    assert EncodingHandler.clean_symbol_string("  ") is None

    # Test convert_to_string with various inputs
    assert EncodingHandler.convert_to_string(b"bytes") == "bytes"
    assert EncodingHandler.convert_to_string(42) == "42"
    assert EncodingHandler.convert_to_string(42.5) == "42.5"