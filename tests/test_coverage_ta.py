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

def test_ta_indicators_missing_cols():
    # Covers error paths when data is malformed
    # Needs at least 10 rows to even try
    data = [{'date': f'2023-01-{i:02d}', 'open': 100, 'high': 105, 'low': 95, 'close': 100+i} for i in range(1, 15)]
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
