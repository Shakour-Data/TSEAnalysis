import pytest
from app.core_utils import update_stats, stats

def test_update_stats():
    # Reset stats
    stats["global"] = {"total": 0, "blocked": 0, "success": 0}
    stats["services"] = {}
    stats["history"] = []
    
    # Success case
    update_stats("test_service", "success", endpoint="test_endpoint")
    assert stats["global"]["total"] == 1
    assert stats["global"]["success"] == 1
    assert stats["services"]["test_service"]["total"] == 1
    assert stats["services"]["test_service"]["success"] == 1
    assert len(stats["history"]) == 1
    assert stats["history"][0]["status"] == "success"
    
    # Blocked case
    update_stats("test_service", "blocked", endpoint="test_endpoint_blocked")
    assert stats["global"]["total"] == 2
    assert stats["global"]["blocked"] == 1
    assert stats["services"]["test_service"]["blocked"] == 1
    assert len(stats["history"]) == 2
    assert stats["history"][0]["status"] == "blocked"

def test_stats_history_limit():
    stats["history"] = []
    for i in range(100):
        update_stats("service", "success", endpoint=f"ep_{i}")
    
    assert len(stats["history"]) == 50 # Limit is 50
    assert stats["history"][0]["endpoint"] == "ep_99"

def test_core_utils_imports():
    from app.core_utils import TLS_CLIENT_AVAILABLE, CURL_CFFI_AVAILABLE, HTTPX_AVAILABLE
    # These are boolean flags, just check they are defined
    assert isinstance(TLS_CLIENT_AVAILABLE, bool)
    assert isinstance(CURL_CFFI_AVAILABLE, bool)
    assert isinstance(HTTPX_AVAILABLE, bool)
