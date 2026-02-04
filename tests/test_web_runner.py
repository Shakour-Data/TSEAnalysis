import pytest
import time
import os
from app.services.test_runner import test_runner
from app.database import db

def test_runner_singleton():
    """Ensure the test runner service is initialized as a singleton."""
    from app.services.test_runner import test_runner as runner2
    assert test_runner is runner2

def test_execution_and_storage():
    """Test that a suite run results in database entries and captured logs."""
    # Use a specific health test that is fast
    suite = "test_health.py"
    run_id = test_runner.run_test_suite(suite)
    
    assert run_id is not None and run_id > 0
    
    # Wait for background thread to finish
    max_wait = 15
    start = time.time()
    while time.time() - start < max_wait:
        results = test_runner.get_recent_results(5)
        current = next((r for r in results if r['id'] == run_id), None)
        if current and current['status'] != 'running':
            break
        time.sleep(1)
    
    results = test_runner.get_recent_results(10)
    current = next((r for r in results if r['id'] == run_id), None)
    
    assert current is not None
    assert current['status'] in ['success', 'fail']
    assert len(current['logs']) > 0
    assert "pytest" in current['logs'].lower()

def test_ai_diagnosis_on_failure():
    """Test that AI analysis is triggered and stored on test failure."""
    # Run a non-existent file to force 'fail' status
    run_id = test_runner.run_test_suite("non_existent_test.py")
    
    # Wait up to 15 seconds
    max_wait = 15
    start = time.time()
    current = None
    while time.time() - start < max_wait:
        results = test_runner.get_recent_results(5)
        current = next((r for r in results if r['id'] == run_id), None)
        if current and current['status'] != 'running':
            break
        time.sleep(1)
    
    assert current is not None
    assert current['status'] == 'fail'
    assert "AI Diagnosis" in current['ai_analysis']
