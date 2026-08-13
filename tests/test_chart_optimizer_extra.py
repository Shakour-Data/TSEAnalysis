import pytest
import io
from PIL import Image
from unittest.mock import patch, MagicMock
from app.utils.chart_optimizer import ChartOptimizer

def test_chart_optimizer_extra_coverage():
    # Create a test image
    img = Image.new('RGB', (2000, 2000), color='red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    # Test optimize_image_size
    optimized = ChartOptimizer.optimize_image_size(buf, max_size_kb=50)
    assert len(optimized.getvalue()) < len(buf.getvalue())  # Should be smaller

    # Test with small image (should not resize)
    small_img = Image.new('RGB', (100, 100), color='blue')
    small_buf = io.BytesIO()
    small_img.save(small_buf, format='PNG')
    small_buf.seek(0)
    optimized_small = ChartOptimizer.optimize_image_size(small_buf)
    assert len(optimized_small.getvalue()) <= len(small_buf.getvalue())

    # Test encode_chart_to_base64
    b64_str = ChartOptimizer.encode_chart_to_base64(optimized)
    assert isinstance(b64_str, str)
    assert b64_str.startswith('data:image/png;base64,')

    # Test encode_chart_to_base64 with None
    assert ChartOptimizer.encode_chart_to_base64(None) is None

    # Test get_chart_cache_key
    key = ChartOptimizer.get_chart_cache_key("SYMBOL", "type", "1Y", "1d")
    assert isinstance(key, str)
    assert len(key) == 32  # MD5 hash length

    # Test cache operations
    ChartOptimizer.cache_chart(key, b64_str)
    cached = ChartOptimizer.get_cached_chart(key)
    assert cached == b64_str

    # Test get_cached_chart with non-existent key
    assert ChartOptimizer.get_cached_chart("nonexistent") is None

    # Test cleanup_expired_charts
    ChartOptimizer.set_chart_cache_ttl(0.001)  # Very short TTL
    import time
    time.sleep(0.01)  # Wait for expiration
    ChartOptimizer.cleanup_expired_charts()
    assert ChartOptimizer.get_cached_chart(key) is None

    # Test estimate_data_points
    points_1y_1d = ChartOptimizer.estimate_data_points("1Y", "1d")
    points_1m_1h = ChartOptimizer.estimate_data_points("1M", "1h")
    assert points_1y_1d > points_1m_1h  # Year should have more points

    # Test get_chart_stats
    stats = ChartOptimizer.get_chart_stats()
    assert isinstance(stats, dict)
    assert "cached_charts" in stats

    # Test clear_chart_cache
    ChartOptimizer.cache_chart("test_key", "test_data")
    ChartOptimizer.clear_chart_cache()
    assert ChartOptimizer.get_cached_chart("test_key") is None

    # Test with different image formats
    jpg_img = Image.new('RGB', (500, 500), color='green')
    jpg_buf = io.BytesIO()
    jpg_img.save(jpg_buf, format='JPEG')
    jpg_buf.seek(0)
    optimized_jpg = ChartOptimizer.optimize_image_size(jpg_buf)
    assert len(optimized_jpg.getvalue()) > 0