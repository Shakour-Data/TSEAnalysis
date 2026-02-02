#!/usr/bin/env python3
"""
Simple Load Testing Script for TSEAnalysis
"""
import threading
import time
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app

def run_load_test(num_users=10, duration_seconds=60, ramp_up_seconds=10):
    """Run load test with specified parameters"""

    print(f"🚀 Starting Load Test: {num_users} users, {duration_seconds}s duration")
    print("=" * 60)

    app = create_app()
    client = app.test_client()

    results = []
    errors = []

    def single_user_test(user_id):
        """Simulate a single user making requests"""
        user_results = []
        user_errors = []

        # Ramp up delay
        time.sleep((user_id / num_users) * ramp_up_seconds)

        start_time = time.time()
        request_count = 0

        while time.time() - start_time < duration_seconds:
            try:
                # Mix of different endpoints
                endpoints = [
                    ('/api/market_status', 'GET', None),
                    ('/api/health', 'GET', None),
                    ('/api/symbols/1', 'GET', None),
                    ('/api/fetch_data', 'POST', {
                        'symbol': 'شاخص کل',
                        'service_type': 'history',
                        'asset_type': 'indices_market',
                        'candle_count': 50
                    })
                ]

                for endpoint, method, data in endpoints:
                    req_start = time.time()

                    if method == 'GET':
                        response = client.get(endpoint)
                    else:
                        response = client.post(endpoint, json=data)

                    req_end = time.time()
                    response_time = (req_end - req_start) * 1000  # ms

                    user_results.append({
                        'endpoint': endpoint,
                        'method': method,
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'user_id': user_id
                    })

                    request_count += 1

                    # Small delay between requests
                    time.sleep(0.1)

            except Exception as e:
                user_errors.append({
                    'user_id': user_id,
                    'error': str(e),
                    'time': time.time()
                })

        return user_results, user_errors, request_count

    # Run test with thread pool
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(single_user_test, i) for i in range(num_users)]

        for future in as_completed(futures):
            user_results, user_errors, req_count = future.result()
            results.extend(user_results)
            errors.extend(user_errors)
            print(f"✅ User completed: {req_count} requests")

    # Analyze results
    print("\n📊 Load Test Results")
    print("=" * 60)

    if results:
        response_times = [r['response_time'] for r in results]
        status_codes = [r['status_code'] for r in results]

        print(f"Total Requests: {len(results)}")
        print(f"Total Errors: {len(errors)}")
        print(f"Success Rate: {((len(results) - len(errors)) / len(results) * 100):.1f}%")

        print("\nResponse Time Statistics (ms):")
        print(f"  Average: {statistics.mean(response_times):.1f}")
        print(f"  Median: {statistics.median(response_times):.1f}")
        print(f"  Min: {min(response_times):.1f}")
        print(f"  Max: {max(response_times):.1f}")
        print(f"  95th percentile: {statistics.quantiles(response_times, n=20)[18]:.1f}")

        print("\nStatus Code Distribution:")
        from collections import Counter
        status_counts = Counter(status_codes)
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count} ({count/len(results)*100:.1f}%)")

        print("\nEndpoint Performance:")
        endpoint_stats = {}
        for result in results:
            endpoint = result['endpoint']
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = []
            endpoint_stats[endpoint].append(result['response_time'])

        for endpoint, times in endpoint_stats.items():
            print(f"  {endpoint}:")
            print(f"    Requests: {len(times)}")
            print(f"    Avg Response: {statistics.mean(times):.1f}ms")
            print(f"    Success Rate: {(sum(1 for t in times if t < 5000) / len(times) * 100):.1f}%")

    if errors:
        print("\n🚨 Sample Errors:")
        for i, error in enumerate(errors[:5]):
            print(f"  {i+1}. User {error['user_id']}: {error['error']}")

    return {
        'total_requests': len(results),
        'total_errors': len(errors),
        'response_times': response_times if results else [],
        'status_codes': status_codes if results else []
    }

if __name__ == "__main__":
    # Run different load scenarios
    scenarios = [
        (5, 30, 5),   # Light load
        (10, 60, 10), # Medium load
        (20, 30, 15)  # Heavy load (short duration)
    ]

    all_results = []

    for num_users, duration, ramp_up in scenarios:
        print(f"\n🔥 Running Scenario: {num_users} users, {duration}s duration")
        result = run_load_test(num_users, duration, ramp_up)
        all_results.append(result)

        # Save results to file
        import json
        with open(f'load_test_results_{num_users}users_{duration}s.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print("\n✅ Load testing completed!")
    print("Results saved to load_test_results_*.json files")