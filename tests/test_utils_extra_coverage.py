import pytest
from app.utils.encoding_utils import EncodingHandler
from app.utils.core_utils import CoreUtils

def test_encoding_utils_extra_coverage():
    # Test safe_decode with different encodings and errors
    assert EncodingHandler.safe_decode(b'\x80\xae', 'latin-1') is not None
    assert EncodingHandler.safe_decode(b'\x80\xae', 'invalid-encoding') is None

    # Test normalize_unicode with different forms
    assert EncodingHandler.normalize_unicode("ی", form='NFKC') is not None

    # Test remove_control_characters with more edge cases
    assert EncodingHandler.remove_control_characters("a\nb\rc") == "a\nb\rc"

    # Test safe_json_dumps with different types
    assert EncodingHandler.safe_json_dumps({"a", "b"}) is not None
    assert EncodingHandler.safe_json_dumps(set()) == '[]'

    # Test urlencode_safely with None
    assert EncodingHandler.urlencode_safely(None) == ""

    # Test urldecode_safely with different inputs
    assert EncodingHandler.urldecode_safely("a%20b") == "a b"
    assert EncodingHandler.urldecode_safely(None) == ""
    assert EncodingHandler.urldecode_safely("%") == "%"

    # Additional tests for better coverage
    # Test safe_encode with different inputs
    assert EncodingHandler.safe_encode("تست") == "تست"
    assert EncodingHandler.safe_encode(None) is None
    assert EncodingHandler.safe_encode(b'\xc7\x84\xc7\x81\xc7\x84\xc7\x85') is not None

    # Test detect_encoding
    assert EncodingHandler.detect_encoding("تست") == 'utf-8'
    assert EncodingHandler.detect_encoding(b'\xc7\x84\xc7\x81\xc7\x84\xc7\x85') == 'utf-8'

    # Test safe_json_loads
    result = EncodingHandler.safe_json_loads('{"a":1}')
    assert result is not None and result["a"] == 1  # type: ignore[index]
    assert EncodingHandler.safe_json_loads(None) is None
    assert EncodingHandler.safe_json_loads('invalid json') is None

    # Test sanitize_string with various inputs
    assert EncodingHandler.sanitize_string("  test  ", 4) == "test"
    assert EncodingHandler.sanitize_string(123, 5) == "123"
    assert EncodingHandler.sanitize_string("very long string that should be truncated", 10) == "very long ..."

    # Test clean_symbol_string
    assert EncodingHandler.clean_symbol_string("فولاد(مبارکه)") == "فولادمبارکه"
    assert EncodingHandler.clean_symbol_string("test-123") == "test-123"
    assert EncodingHandler.clean_symbol_string(None) is None
    assert EncodingHandler.clean_symbol_string("") is None

    # Test convert_to_string
    assert EncodingHandler.convert_to_string("test") == "test"
    assert EncodingHandler.convert_to_string(123) == "123"
    assert EncodingHandler.convert_to_string(b'test') == "test"
    assert EncodingHandler.convert_to_string(None) is None

    # Test Persian digit conversion
    assert CoreUtils.to_persian_digits("12345") == "۱۲۳۴۵"
    assert CoreUtils.to_persian_digits("1,234.56") == "۱,۲۳۴.۵۶"
    assert CoreUtils.to_english_digits("۱۲۳۴۵") == "12345"
    assert CoreUtils.to_english_digits("۱,۲۳۴.۵۶") == "1,234.56"

    # Test clean_symbol_string with more edge cases
    assert EncodingHandler.clean_symbol_string("  test  ") == "test"
    assert EncodingHandler.clean_symbol_string("test-123") == "test-123"
