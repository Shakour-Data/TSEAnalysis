#!/usr/bin/env python3
"""
نماد انفوگرافکس ڈیمو
نماد کے لیے مکمل انفوگرافکس بنانے کا مظاہرہ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.symbol_infographics import SymbolInfographics
import pandas as pd
import numpy as np

def create_sample_data(symbol: str, days: int = 100) -> list:
    """نماد کے لیے نمونہ ڈیٹا بنائیں"""
    np.random.seed(42)  # Consistent results

    dates = pd.date_range('2023-01-01', periods=days, freq='D')
    price = 1000

    data = []
    for date in dates:
        # Random walk with some volatility
        change = np.random.normal(0, 0.02)  # 2% daily volatility
        price *= (1 + change)

        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'close': round(price, 2),
            'open': round(price * (1 + np.random.normal(0, 0.005)), 2),
            'high': round(price * (1 + abs(np.random.normal(0, 0.01))), 2),
            'low': round(price * (1 - abs(np.random.normal(0, 0.01))), 2),
            'volume': np.random.randint(10000, 100000)
        })

    return data

def main():
    """مین ڈیمو فنکشن"""
    print("Symbol Infographics System Demo")
    print("=" * 50)

    # Sample symbol
    symbol = "FOOLAD"
    print(f"Analyzing {symbol}...")

    # Create sample data
    data = create_sample_data(symbol, days=200)
    print(f"Created {len(data)} data points")

    # Generate infographics
    print("Generating charts and analysis...")
    infographics = SymbolInfographics.generate_symbol_infographics(symbol, data)

    if not infographics:
        print("Failed to generate infographics")
        return

    # Show results
    print("Infographics generated successfully!")
    print("\nStatistics:")
    stats = infographics.get('statistics', {})
    for key, value in stats.items():
        try:
            print(f"  {key}: {value}")
        except UnicodeEncodeError:
            print(f"  {key}: [Unicode content]")

    print("\nCharts:")
    charts = infographics.get('charts', {})
    for chart_name in charts.keys():
        status = "Generated" if charts[chart_name] else "Failed"
        print(f"  {chart_name}: {status}")

    print("\nTechnical Analysis:")
    analysis = infographics.get('analysis', {})
    for key, value in analysis.items():
        try:
            print(f"  {key}: {value}")
        except UnicodeEncodeError:
            print(f"  {key}: [Unicode content]")

    # Generate full report
    print("\nGenerating full report...")
    report = SymbolInfographics.generate_infographics_report(symbol, data)

    print("Report ready!")
    print(f"Charts count: {len(report.get('charts', {}))}")
    print(f"Statistics: {len(report.get('full_statistics', {}))}")
    print(f"Analysis: {len(report.get('technical_analysis', {}))}")

    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()