#!/usr/bin/env python3
"""
Test script to verify رنیک (TEST_SYMBOL) data retrieval from Farabourse.
Tests both the API fallback and mock data generation.
"""

import requests
import json
import sys

API_URL = "http://127.0.0.1:5000"

def test_symbol_retrieval():
    """Test retrieving data for a symbol from Farabourse."""
    symbol = "TEST_SYMBOL"
    print(f"\n{'='*60}")
    print(f"Testing Data Retrieval for {symbol}")
    print(f"{'='*60}\n")

    # Test 1: Realtime data
    print("[1] Fetching Realtime Data...")
    response = requests.post(f"{API_URL}/api/fetch_data", json={
        "asset_type": "fara_bourse",
        "symbol": symbol,
        "service_type": "realtime"
    })
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Realtime: {len(data) if isinstance(data, list) else 'error'} items")
    else:
        print(f"❌ Realtime failed: {response.status_code}")

    # Test 2: History data
    print("\n[2] Fetching History Data (100 candles)...")
    response = requests.post(f"{API_URL}/api/fetch_data", json={
        "asset_type": "fara_bourse",
        "symbol": symbol,
        "service_type": "history",
        "candle_count": 100
    })
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            print(f"✅ History: {len(data)} candles retrieved")
            first = data[0]
            print(f"   Date: {first.get('date')}")
            print(f"   Close: {first.get('pc'):,}")
            print(f"   High: {first.get('pmax'):,}")
            print(f"   Low: {first.get('pmin'):,}")
            print(f"   Volume: {first.get('tvol'):,}")
        else:
            print(f"❌ History: No data returned")
    else:
        print(f"❌ History failed: {response.status_code}")

    # Test 3: Technical Analysis
    print("\n[3] Fetching Technical Analysis (50 candles)...")
    response = requests.post(f"{API_URL}/api/fetch_data", json={
        "asset_type": "fara_bourse",
        "symbol": symbol,
        "service_type": "technical",
        "candle_count": 50
    })
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            latest = data[0]
            print(f"✅ Technical: {len(data)} records analyzed")
            print(f"   Latest Close: {latest.get('close'):,}")
            print(f"   RSI(14): {latest.get('RSI', 'N/A')}")
            print(f"   MACD: {latest.get('MACD', 'N/A')}")
            print(f"   Signal: {latest.get('Signal', 'N/A')}")
            print(f"   Pattern: {latest.get('Pattern', 'N/A')}")
        else:
            print(f"❌ Technical: No data returned")
    else:
        print(f"❌ Technical failed: {response.status_code}")

    # Test 4: Market Status
    print("\n[4] Checking Market Status...")
    response = requests.get(f"{API_URL}/api/market_status")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Market: {data.get('status')}")
        print(f"   Time: {data.get('time')}")
        stats = data.get('stats', {})
        global_stats = stats.get('global', {})
        print(f"   Requests: {global_stats.get('total')} total, {global_stats.get('success')} successful")
    else:
        print(f"❌ Market status failed: {response.status_code}")

    print(f"\n{'='*60}")
    print("Testing Complete!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    try:
        test_symbol_retrieval()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
