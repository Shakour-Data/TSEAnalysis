import pytest
from app.utils.validators import DataValidator

def test_validators_remaining_coverage():
    """Test remaining uncovered parts of DataValidator"""

    # Test is_valid_price with edge cases
    assert DataValidator.is_valid_price("0") == False  # String zero should be invalid
    assert DataValidator.is_valid_price(0.0) == False  # Float zero should be invalid
    assert DataValidator.is_valid_price(-0.01) == False  # Negative should be invalid
    assert DataValidator.is_valid_price(1e11) == False  # Too large should be invalid
    assert DataValidator.is_valid_price("abc") == False  # Non-numeric string
    assert DataValidator.is_valid_price("") == False  # Empty string
    assert DataValidator.is_valid_price([]) == False  # List
    assert DataValidator.is_valid_price({}) == False  # Dict

    # Test is_valid_volume with edge cases
    assert DataValidator.is_valid_volume("0") == False  # String zero should be invalid
    assert DataValidator.is_valid_volume(0.0) == False  # Float zero should be invalid
    assert DataValidator.is_valid_volume(-1) == False  # Negative should be invalid
    assert DataValidator.is_valid_volume("abc") == False  # Non-numeric string
    assert DataValidator.is_valid_volume("") == False  # Empty string
    assert DataValidator.is_valid_volume(100.5) == True  # Float volume is converted to int and valid
    assert DataValidator.is_valid_volume([]) == False  # List
    assert DataValidator.is_valid_volume({}) == False  # Dict

    # Test is_valid_symbol
    assert DataValidator.is_valid_symbol("") == False
    assert DataValidator.is_valid_symbol(None) == False
    assert DataValidator.is_valid_symbol("   ") == False
    assert DataValidator.is_valid_symbol("A") == True
    assert DataValidator.is_valid_symbol("ABC123") == True
    assert DataValidator.is_valid_symbol("TEST_SYMBOL") == True
    assert DataValidator.is_valid_symbol("test@#$%") == True  # Special chars allowed?

    # Test is_valid_date
    assert DataValidator.is_valid_date("2023-01-01") == True
    assert DataValidator.is_valid_date("2023/01/01") == False  # Only YYYY-MM-DD format accepted
    assert DataValidator.is_valid_date("01-01-2023") == False  # Wrong format
    assert DataValidator.is_valid_date("invalid") == False
    assert DataValidator.is_valid_date("") == False
    assert DataValidator.is_valid_date(None) == False
    assert DataValidator.is_valid_date(123) == False

    # Additional edge case tests for existing methods
    # Test that we've covered the remaining uncovered code paths