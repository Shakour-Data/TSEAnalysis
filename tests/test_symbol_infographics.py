import pytest
import pandas as pd
import numpy as np
from app.services.symbol_infographics import SymbolInfographics

def test_symbol_infographics_basic():
    """Test basic infographics generation"""
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    np.random.seed(42)

    data = []
    price = 1000
    for i, date in enumerate(dates):
        change = np.random.normal(0, 0.02)  # 2% daily volatility
        price *= (1 + change)
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'close': price,
            'open': price * (1 + np.random.normal(0, 0.01)),
            'high': price * (1 + abs(np.random.normal(0, 0.015))),
            'low': price * (1 - abs(np.random.normal(0, 0.015))),
            'volume': np.random.randint(1000, 10000)
        })

    # Test infographics generation
    result = SymbolInfographics.generate_symbol_infographics("TEST", data)

    assert isinstance(result, dict)
    assert 'symbol' in result
    assert 'charts' in result
    assert 'statistics' in result
    assert 'analysis' in result
    assert result['symbol'] == "TEST"

    # Check charts
    charts = result['charts']
    assert 'price_chart' in charts
    assert 'volume_chart' in charts
    assert 'technical_chart' in charts
    assert 'price_distribution' in charts

    # Check that charts are base64 strings
    for chart_name, chart_data in charts.items():
        if chart_data:
            assert isinstance(chart_data, str)
            assert chart_data.startswith('data:image/png;base64,')

    # Check statistics
    stats = result['statistics']
    assert 'current_price' in stats
    assert 'highest_price' in stats
    assert 'lowest_price' in stats
    assert 'average_price' in stats
    assert 'total_volume' in stats

    # Check analysis
    analysis = result['analysis']
    assert isinstance(analysis, dict)

def test_infographics_insufficient_data():
    """Test with insufficient data"""
    data = [{'close': 100, 'open': 100, 'high': 100, 'low': 100, 'volume': 1000}]

    result = SymbolInfographics.generate_symbol_infographics("TEST", data)
    assert result == {} or not result.get('charts')

def test_infographics_empty_data():
    """Test with empty data"""
    result = SymbolInfographics.generate_symbol_infographics("TEST", [])
    assert result == {}

def test_calculate_statistics():
    """Test statistics calculation"""
    data = [
        {'close': 100, 'open': 99, 'high': 101, 'low': 98, 'volume': 1000},
        {'close': 105, 'open': 100, 'high': 106, 'low': 99, 'volume': 1200},
        {'close': 102, 'open': 105, 'high': 107, 'low': 101, 'volume': 800}
    ]

    df = pd.DataFrame(data)
    stats = SymbolInfographics._calculate_statistics(df)

    assert isinstance(stats, dict)
    assert 'current_price' in stats
    assert 'price_change' in stats
    assert stats['current_price'] == '۱۰۲ تومان'  # Persian digits

def test_infographics_report():
    """Test full infographics report generation"""
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    data = []
    price = 1000
    for date in dates:
        price += np.random.normal(0, 10)
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'close': price,
            'open': price * 0.99,
            'high': price * 1.01,
            'low': price * 0.98,
            'volume': 1000
        })

    report = SymbolInfographics.generate_infographics_report("TEST", data)

    assert isinstance(report, dict)
    assert 'symbol' in report
    assert 'summary' in report
    assert 'charts' in report
    assert 'full_statistics' in report
    assert 'technical_analysis' in report
    assert report['symbol'] == "TEST"