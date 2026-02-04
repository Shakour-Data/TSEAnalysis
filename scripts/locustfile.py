#!/usr/bin/env python3
"""
Load Testing Script for TSEAnalysis using Locust
"""
import os
import sys
from locust import HttpUser, task, between
from app import create_app

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TSEAnalysisUser(HttpUser):
    """Load testing user for TSEAnalysis API"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Setup before starting the test"""
        self.app = create_app()
        self.client = self.app.test_client()

    @task(3)  # 30% of requests
    def get_symbols(self):
        """Test symbols endpoint"""
        with self.app.test_client() as client:
            # Test different market types
            for market_type in ['1', '2', '4', '5']:
                response = client.get(f'/api/symbols/{market_type}')

    @task(2)  # 20% of requests
    def get_symbol_detail(self):
        """Test individual symbol endpoint - but we don't have this route"""
        # Skip this as the route doesn't exist
        pass

    @task(2)  # 20% of requests
    def get_market_overview(self):
        """Test market status endpoint (closest to overview)"""
        with self.app.test_client() as client:
            response = client.get('/api/market_status')

    @task(2)  # 20% of requests
    def get_technical_analysis(self):
        """Test technical analysis via fetch_data endpoint"""
        with self.app.test_client() as client:
            # Test with sample data
            test_data = {
                'symbol': 'شاخص کل',
                'service_type': 'technical',
                'asset_type': 'indices_market',
                'candle_count': 100
            }
            response = client.post('/api/fetch_data', json=test_data)

    @task(1)  # 10% of requests
    def get_chart_data(self):
        """Test chart data via fetch_data endpoint"""
        with self.app.test_client() as client:
            test_data = {
                'symbol': 'شاخص کل',
                'service_type': 'history',
                'asset_type': 'indices_market',
                'candle_count': 50
            }
            response = client.post('/api/fetch_data', json=test_data)

if __name__ == "__main__":
    # Run locust from command line: python -m locust -f scripts/locustfile.py
    # Or use: locust -f scripts/locustfile.py
    pass
