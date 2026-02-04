#!/usr/bin/env python3
"""
Performance Profiling Script for TSEAnalysis
"""
import cProfile
import pstats
import io
import time
import tracemalloc
from memory_profiler import profile, memory_usage
import psutil
import os
import sys
import pandas as pd  # type: ignore[import]

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.services.tsetmc import TSETMCClient
from app.services.symbol_infographics import SymbolInfographics

def profile_api_endpoints():
    """Profile API endpoints performance"""
    print("🔍 Profiling API Endpoints...")

    app = create_app()
    client = app.test_client()

    # Profile main endpoints
    endpoints = [
        '/api/symbols',
        '/api/symbols/1',
        '/api/market/overview',
        '/api/technical-analysis/1'
    ]

    results = {}

    for endpoint in endpoints:
        print(f"  Profiling {endpoint}...")

        # Memory profiling
        tracemalloc.start()
        start_time = time.time()

        try:
            response = client.get(endpoint)
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            results[endpoint] = {
                'response_time': end_time - start_time,
                'status_code': response.status_code,
                'current_memory': current / 1024 / 1024,  # MB
                'peak_memory': peak / 1024 / 1024,  # MB
                'response_size': len(response.get_data())
            }

        except Exception as e:
            results[endpoint] = {'error': str(e)}

    return results

def profile_data_fetching():
    """Profile data fetching operations"""
    print("🔍 Profiling Data Fetching...")

    service = TSETMCClient(api_key=os.getenv('TSE_API_KEY', 'fallback'))

    # Profile symbol list fetching
    tracemalloc.start()
    start_time = time.time()

    try:
        symbols = service.get_all_symbols("1")  # Get bourse symbols
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            'operation': 'get_symbol_list',
            'response_time': end_time - start_time,
            'symbols_count': len(symbols) if symbols else 0,
            'current_memory': current / 1024 / 1024,
            'peak_memory': peak / 1024 / 1024
        }

    except Exception as e:
        return {'error': str(e)}

def profile_chart_generation():
    """Profile chart generation performance"""
    print("🔍 Profiling Chart Generation...")

    infographics = SymbolInfographics()

    # Mock data for testing
    mock_data = {
        'symbol': 'TEST',
        'data': [
            {'date': '2024-01-01', 'close': 100, 'high': 105, 'low': 95, 'volume': 1000},
            {'date': '2024-01-02', 'close': 102, 'high': 107, 'low': 97, 'volume': 1200},
            {'date': '2024-01-03', 'close': 101, 'high': 106, 'low': 96, 'volume': 1100}
        ]
    }

    chart_types = ['correlation_matrix', 'volatility_analysis', 'seasonal_analysis']

    results = {}

    for chart_type in chart_types:
        print(f"  Profiling {chart_type}...")

        tracemalloc.start()
        start_time = time.time()

        try:
            # Convert mock_data to DataFrame for the methods
            df = pd.DataFrame(mock_data['data'])
            symbol = mock_data.get('symbol', 'TEST')
            
            if chart_type == 'correlation_matrix':
                result = infographics.generate_correlation_matrix(df, symbol)
            elif chart_type == 'volatility_analysis':
                result = infographics.generate_volatility_analysis(df, symbol)
            elif chart_type == 'seasonal_analysis':
                result = infographics.generate_seasonal_analysis(df, symbol)

            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            results[chart_type] = {
                'response_time': end_time - start_time,
                'current_memory': current / 1024 / 1024,
                'peak_memory': peak / 1024 / 1024,
                'success': result is not None
            }

        except Exception as e:
            results[chart_type] = {'error': str(e)}

    return results

@profile
def memory_profile_main():
    """Memory profiling of main operations"""
    print("🔍 Memory Profiling Main Operations...")

    # API profiling
    api_results = profile_api_endpoints()

    # Data fetching
    data_results = profile_data_fetching()

    # Chart generation
    chart_results = profile_chart_generation()

    return {
        'api_profiling': api_results,
        'data_fetching': data_results,
        'chart_generation': chart_results
    }

def run_cprofile():
    """Run cProfile on main operations"""
    print("🔍 Running cProfile...")

    pr = cProfile.Profile()
    pr.enable()

    results = memory_profile_main()

    pr.disable()

    # Save profile stats
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(20)  # Top 20 functions

    with open('profile_stats.txt', 'w', encoding='utf-8') as f:
        f.write(s.getvalue())

    return results

def benchmark_operations():
    """Benchmark critical operations"""
    print("🔍 Benchmarking Operations...")

    import timeit

    # Benchmark API response times
    app = create_app()
    client = app.test_client()

    def api_call():
        return client.get('/api/symbols')

    # Run benchmark
    times = timeit.repeat(api_call, repeat=5, number=1)

    return {
        'api_response_times': times,
        'average_time': sum(times) / len(times),
        'min_time': min(times),
        'max_time': max(times)
    }

if __name__ == "__main__":
    print("🚀 Starting TSEAnalysis Performance Profiling")
    print("=" * 60)

    # Run profiling
    results = run_cprofile()

    # Run benchmarks
    benchmark_results = benchmark_operations()

    # Save results
    import json
    with open('profiling_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'profiling_results': results,
            'benchmark_results': benchmark_results,
            'timestamp': time.time()
        }, f, indent=2, ensure_ascii=False)

    print("✅ Profiling completed!")
    print("📊 Results saved to profiling_results.json and profile_stats.txt")