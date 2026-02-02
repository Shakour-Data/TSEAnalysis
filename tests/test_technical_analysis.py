import pytest
import pandas as pd
import numpy as np
from app.services.technical_analysis import TechnicalAnalyzer

@pytest.fixture
def sample_df():
    data = {
        'date': pd.date_range(start='2023-01-01', periods=100),
        'open': np.linspace(100, 200, 100) + np.random.normal(0, 5, 100),
        'high': np.linspace(105, 205, 100) + np.random.normal(0, 5, 100),
        'low': np.linspace(95, 195, 100) + np.random.normal(0, 5, 100),
        'close': np.linspace(100, 200, 100) + np.random.normal(0, 5, 100),
        'volume': np.random.randint(1000, 5000, 100)
    }
    return pd.DataFrame(data)

def test_fibonacci_levels(sample_df):
    levels = TechnicalAnalyzer.get_fibonacci_levels(sample_df)
    assert '0%' in levels
    assert '61.8%' in levels
    assert '100%' in levels
    assert levels['0%'] > levels['100%']

def test_risk_reward_calculation():
    current = 100
    supports = [{'value': 90, 'strength': 5}]
    resistances = [{'value': 120, 'strength': 5}]
    
    rr = TechnicalAnalyzer.calculate_risk_reward(current, supports, resistances)
    assert rr is not None
    assert rr['entry'] == 100
    assert rr['rr_ratio'] > 0
    assert rr['status'] in ["Attractive", "Fair", "Risky"]

def test_prepare_ohlcv_data():
    raw_data = [
        {"date": "20230101", "pf": 100, "pmax": 110, "pmin": 90, "pc": 105, "tvol": 1000},
        {"date": "20230102", "pf": 105, "pmax": 115, "pmin": 95, "pc": 110, "tvol": 1100}
    ]
    prepared = TechnicalAnalyzer.prepare_ohlcv_data(raw_data)
    assert isinstance(prepared, list)
    assert len(prepared) == 2
    assert "close" in prepared[0]
    assert prepared[0]["close"] == 105

def test_resample_to_weekly(sample_df):
    raw_list = sample_df.to_dict('records')
    # prepare_ohlcv_data usually handles numeric conversion, let's assume raw_list is ready
    weekly = TechnicalAnalyzer.resample_to_weekly(raw_list)
    assert len(weekly) < len(raw_list)
    assert len(weekly) > 0

def test_calculate_technical_analysis(sample_df):
    raw_list = sample_df.to_dict('records')
    # calculate_technical_analysis expects a list and returns a list with indicators
    analyzed = TechnicalAnalyzer.calculate_technical_analysis(raw_list)
    assert "RSI" in analyzed[-1]
    assert "MACD" in analyzed[-1]
    assert "Signal" in analyzed[-1]

def test_get_support_resistance(sample_df):
    # Support/Resistance requires some volatility or clear peaks/troughs
    # We'll use a larger window and more data
    supports, resistances = TechnicalAnalyzer.get_support_resistance(sample_df)
    assert isinstance(supports, list)
    assert isinstance(resistances, list)

def test_prioritize_indicators(sample_df):
    # Need indicators calculated first
    raw_list = sample_df.to_dict('records')
    analyzed = TechnicalAnalyzer.calculate_technical_analysis(raw_list)
    df = pd.DataFrame(analyzed)
    
    rankings = TechnicalAnalyzer.prioritize_indicators(df)
    assert isinstance(rankings, list)
    if rankings:
        assert 'name' in rankings[0]
        assert 'accuracy' in rankings[0]

def test_prepare_ohlcv_data():
    raw_data = [
        {"close": 100, "date": "2023-01-01", "volume": 10},
        {"close": 110, "date": "2023-01-02", "volume": 20}
    ]
    prepared = TechnicalAnalyzer.prepare_ohlcv_data(raw_data)
    assert len(prepared) == 2
    assert "close" in prepared[0]
    assert prepared[0]["close"] == 100

def test_resample_to_weekly():
    daily_data = [
        {"date": f"2023-01-{i+1:02d}", "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000}
        for i in range(21) # 3 weeks
    ]
    weekly = TechnicalAnalyzer.resample_to_weekly(daily_data)
    assert len(weekly) < len(daily_data)
    assert "close" in weekly[0]

def test_generate_strategy_matrix():
    current_price = 1000
    supports = [{"value": 900}, {"value": 850}]
    resistances = [{"value": 1100}, {"value": 1150}]
    
    strategies = TechnicalAnalyzer.generate_strategy_matrix(current_price, supports, resistances)
    assert len(strategies) == 6
    assert "پروفایل سرمایه‌گذار" in strategies[0]
