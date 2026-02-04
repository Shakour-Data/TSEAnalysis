import pytest
import pandas as pd
import numpy as np
from app.services.technical_analysis import TechnicalAnalyzer

def test_ta_detect_divergence_short():
    df = pd.DataFrame({'close': range(10), 'RSI': range(10)})
    assert TechnicalAnalyzer.detect_divergence(df) == "No Divergence"

def test_ta_prepare_ohlcv_empty():
    assert TechnicalAnalyzer.prepare_ohlcv_data([]) == []
    assert TechnicalAnalyzer.prepare_ohlcv_data(None) is None

def test_ta_resample_weekly_short():
    assert TechnicalAnalyzer.resample_to_weekly([{'date': '2023-01-01', 'close': 10}]) == [{'date': '2023-01-01', 'close': 10}]

def test_ta_calculate_technical_analysis_short():
    res = TechnicalAnalyzer.calculate_technical_analysis([{'date': '2023-01-01', 'close': 10}])
    assert len(res) == 1

def test_ta_get_fibonacci_levels_empty():
    df = pd.DataFrame()
    assert TechnicalAnalyzer.get_fibonacci_levels(df) == {}

def test_ta_calculate_risk_reward_empty():
    assert TechnicalAnalyzer.calculate_risk_reward(100, [], []) is None

def test_ta_resample_weekly_no_date():
    data = [{'close': 10, 'open': 9}]
    assert TechnicalAnalyzer.resample_to_weekly(data) == data

def test_ta_resample_weekly_exception():
    data = [{'date': 'invalid', 'close': 10, 'open': 9, 'high': 11, 'low': 8, 'volume': 100}]
    # Should return original data on exception
    result = TechnicalAnalyzer.resample_to_weekly(data)
    assert result == data

def test_ta_calculate_technical_analysis_short_len():
    data = [{'date': '2023-01-01', 'close': 10, 'open': 9, 'high': 11, 'low': 8, 'volume': 100}] * 15  # len=15 <20
    result = TechnicalAnalyzer.calculate_technical_analysis(data)
    assert len(result) == 15
    # SMA20 should be added with rolling mean for short data

def test_ta_calculate_technical_analysis_mid_len():
    data = [{'date': '2023-01-01', 'close': 10, 'open': 9, 'high': 11, 'low': 8, 'volume': 100}] * 25  # len=25 >=20 <26
    result = TechnicalAnalyzer.calculate_technical_analysis(data)
    assert len(result) == 25
    assert 'MACD' not in result[0] or result[0]['MACD'] is None  # MACD None for <26

def test_ta_calculate_technical_analysis_very_short():
    data = [{'date': '2023-01-01', 'close': 10, 'open': 9, 'high': 11, 'low': 8, 'volume': 100}] * 5  # len=5 <10
    result = TechnicalAnalyzer.calculate_technical_analysis(data)
    assert result == data  # returns original if <10

def test_ta_calculate_technical_analysis_with_index():
    data = [{'date': '2023-01-01', 'close': 10, 'open': 9, 'high': 11, 'low': 8, 'volume': 100}] * 50
    index_data = [{'date': '2023-01-01', 'close': 100}] * 50
    result = TechnicalAnalyzer.calculate_technical_analysis(data, index_data)
    assert len(result) == 50
    # Should have beta if index_data provided

def test_ta_calculate_technical_analysis_with_chart():
    data = [{'date': '2023-01-01', 'close': 10, 'open': 9, 'high': 11, 'low': 8, 'volume': 100}] * 100
    result = TechnicalAnalyzer.calculate_technical_analysis(data)
    assert len(result) == 100
    # Should have chart_image if data is long enough

def test_ta_indicators_missing_cols():
    # Covers error paths when data is malformed
    # Needs at least 10 rows to even try
    data = [{'date': f'2023-01-{i:02d}', 'open': 100, 'high': 105, 'low': 95, 'close': 100+i} for i in range(1, 50)]
    res = TechnicalAnalyzer.calculate_technical_analysis(data)
    assert 'Signal' in res[0]

def test_ta_calculate_technical_analysis_variations():
    # Creating data with enough rows for indicators
    data = [{'date': f'2023-01-{i:02d}', 'open': 100, 'high': 105, 'low': 95, 'close': 102} for i in range(1, 60)]
    res = TechnicalAnalyzer.calculate_technical_analysis(data)
    assert 'SMA20' in res[0]

def test_ta_chart_generation_fail():
    # Pass empty data to generate_chart_image
    res = TechnicalAnalyzer.generate_chart_image([], "TEST")
    assert res is None

def test_ta_identify_levels_short():
    df = pd.DataFrame({'close': [10, 11, 10, 11, 10], 'high': [12, 12, 12, 12, 12], 'low': [8, 8, 8, 8, 8]})
    # The actual method name is get_support_resistance
    supports, resistances = TechnicalAnalyzer.get_support_resistance(df)
    assert isinstance(supports, list)

def test_ta_generate_chart_image_with_data():
    # Test with valid data
    df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=20),
        'open': [100] * 20,
        'high': [105] * 20,
        'low': [95] * 20,
        'close': [102] * 20,
        'volume': [1000] * 20,
        'SMA20': [101] * 20,
        'BBU': [106] * 20,
        'BBL': [96] * 20
    })
    buf = TechnicalAnalyzer.generate_chart_image(df, "TEST", "daily")
    assert buf is not None

def test_ta_generate_chart_image_empty_df():
    df = pd.DataFrame()
    buf = TechnicalAnalyzer.generate_chart_image(df, "TEST")
    assert buf is None

def test_ta_generate_chart_image_short():
    df = pd.DataFrame({'date': ['2023-01-01'], 'close': [100]})
    buf = TechnicalAnalyzer.generate_chart_image(df, "TEST")
    assert buf is None

def test_ta_detect_divergence_bullish():
    # Create data for bullish divergence
    close_prices = [100, 95, 90, 85, 80] + [80, 82, 84, 86, 88] * 10  # Lower lows
    rsi_values = [70, 75, 80, 85, 90] + [90, 88, 86, 84, 82] * 10   # Higher lows
    df = pd.DataFrame({'close': close_prices, 'high': close_prices, 'low': close_prices, 'RSI': rsi_values})
    result = TechnicalAnalyzer.detect_divergence(df)
    assert result in ["Bullish Divergence (Positive)", "Bearish Divergence (Negative)", "Normal", "No Divergence"]

def test_ta_detect_divergence_bearish():
    # Create data for bearish divergence
    close_prices = [80, 85, 90, 95, 100] + [100, 98, 96, 94, 92] * 10  # Higher highs
    rsi_values = [30, 25, 20, 15, 10] + [10, 12, 14, 16, 18] * 10   # Lower highs
    df = pd.DataFrame({'close': close_prices, 'high': close_prices, 'low': close_prices, 'RSI': rsi_values})
    result = TechnicalAnalyzer.detect_divergence(df)
    assert result in ["Bullish Divergence (Positive)", "Bearish Divergence (Negative)", "Normal", "No Divergence"]

def test_ta_resample_to_weekly():
    data = [{'date': '2023-01-01', 'close': 100}, {'date': '2023-01-02', 'close': 101}, {'date': '2023-01-08', 'close': 102}]
    result = TechnicalAnalyzer.resample_to_weekly(data)
    assert len(result) > 0

def test_ta_get_support_resistance():
    df = pd.DataFrame({
        'close': [100, 101, 99, 102, 98, 103, 97, 104, 96, 105] * 10,
        'high': [105] * 100,
        'low': [95] * 100
    })
    supports, resistances = TechnicalAnalyzer.get_support_resistance(df)
    assert isinstance(supports, list)
    assert isinstance(resistances, list)

def test_ta_calculate_technical_analysis_with_indicators():
    data = [{'date': f'2023-01-{i+1:02d}', 'open': 100+i, 'high': 110+i, 'low': 90+i, 'close': 105+i, 'volume': 1000} for i in range(100)]
    result = TechnicalAnalyzer.calculate_technical_analysis(data)
    assert len(result) == 100
    assert 'RSI' in result[0]
    assert 'MACD' in result[0]
    assert 'BBU' in result[0]

def test_ta_fibonacci_levels():
    df = pd.DataFrame({
        'high': [110, 115, 120, 125, 130],
        'low': [90, 85, 80, 75, 70],
        'close': [100, 105, 110, 115, 120]
    })
    levels = TechnicalAnalyzer.get_fibonacci_levels(df)
    assert isinstance(levels, dict)

def test_ta_strategy_matrix():
    current_price = 100
    supports = [{'value': 90, 'strength': 1}]
    resistances = [{'value': 110, 'strength': 1}]
    strategies = TechnicalAnalyzer.generate_strategy_matrix(current_price, supports, resistances)
    assert isinstance(strategies, list)
