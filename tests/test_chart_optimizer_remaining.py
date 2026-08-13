import pytest
import io
from PIL import Image
from app.utils.chart_optimizer import ChartOptimizer

def test_chart_optimizer_remaining_coverage():
    """Test remaining uncovered parts of ChartOptimizer"""

    # Clear cache at start to ensure clean state
    ChartOptimizer.clear_chart_cache()

    # Test get_cached_chart with non-existent key
    assert ChartOptimizer.get_cached_chart("nonexistent_key") is None

    # Test cache_chart and get_cached_chart
    test_key = "test_key"
    test_data = "test_chart_data"

    # Cache the data
    ChartOptimizer.cache_chart(test_key, test_data)
    cached = ChartOptimizer.get_cached_chart(test_key)
    assert cached == test_data

    # Test clear_chart_cache with specific symbol
    ChartOptimizer.cache_chart("AAPL_data", "data1")
    ChartOptimizer.cache_chart("GOOGL_data", "data2")
    ChartOptimizer.cache_chart("OTHER_data", "data3")

    # Clear cache for AAPL (this clears all keys containing "AAPL")
    ChartOptimizer.clear_chart_cache("AAPL")
    assert ChartOptimizer.get_cached_chart("AAPL_data") is None
    assert ChartOptimizer.get_cached_chart("GOOGL_data") == "data2"
    assert ChartOptimizer.get_cached_chart("OTHER_data") == "data3"
    assert ChartOptimizer.get_cached_chart("OTHER_data") == "data3"

    # Test clear_chart_cache without symbol (clear all)
    ChartOptimizer.clear_chart_cache()
    assert ChartOptimizer.get_cached_chart("SYMBOL_B_data") is None
    assert ChartOptimizer.get_cached_chart("OTHER_data") is None

    # Test set_chart_cache_ttl
    old_ttl = ChartOptimizer._cache_ttl
    ChartOptimizer.set_chart_cache_ttl(3600)  # 1 hour
    assert ChartOptimizer._cache_ttl == 3600

    # Reset to old value
    ChartOptimizer.set_chart_cache_ttl(old_ttl)

    # Test cleanup_expired_charts when cache is empty
    result = ChartOptimizer.cleanup_expired_charts()
    assert result == 0

    # Test get_chart_stats with empty cache
    stats = ChartOptimizer.get_chart_stats()
    assert isinstance(stats, dict)
    assert stats['cached_charts'] == 0
    assert stats['total_size_mb'] == 0.0
    assert 'cache_ttl' in stats
    assert 'estimated_memory' in stats

    # Test get_chart_stats with data in cache
    ChartOptimizer.cache_chart("test_key", "x" * 1000)  # 1KB of data
    stats = ChartOptimizer.get_chart_stats()
    assert stats['cached_charts'] == 1
    assert stats['total_size_mb'] > 0

    # Test estimate_data_points
    # Test 1 year, 1 day resolution
    points = ChartOptimizer.estimate_data_points("1Y", "1d")
    assert points == 365  # Approximately 365 days in a year

    # Test 1 month, 1 hour resolution
    points = ChartOptimizer.estimate_data_points("1M", "1h")
    assert points == 30  # 30 days * 1 (default for unknown resolution)

    # Test 3 months, 1 day resolution
    points = ChartOptimizer.estimate_data_points("3M", "1d")
    assert points == 90  # 3 months * 30 days

    # Test 5 years, 1 week resolution
    points = ChartOptimizer.estimate_data_points("5Y", "1w")
    assert points == 1825 * 7  # 5 years * 365.25 days * 7 points per week

    # Test invalid period
    points = ChartOptimizer.estimate_data_points("invalid", "1d")
    assert points == 30  # Should default to 1M

    # Test invalid resolution
    points = ChartOptimizer.estimate_data_points("1M", "invalid")
    assert points == 30  # Should default to 1d

    # Clean up
    ChartOptimizer.clear_chart_cache()