
import os
import requests
import json

# Configuration
API_KEY = "677e4860b2d6a" # From your environment
SYMBOL = "وبملت"

def test_candlestick():
    print(f"Testing Candlestick for {SYMBOL}...")
    url = f"https://brsapi.ir/Api/Tsetmc/Candlestick.php?key={API_KEY}&l18={SYMBOL}&adjusted=true"
    
    try:
        resp = requests.get(url, timeout=30)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        
        if isinstance(data, list):
            print(f"Success! Received list with {len(data)} items.")
            print(f"First item: {data[0]}")
        elif isinstance(data, dict):
            print(f"Received dictionary keys: {list(data.keys())}")
            for k in ['candle_daily', 'candle_daily_adjusted', 'candles', 'history']:
                if k in data and isinstance(data[k], list):
                    print(f"Found list in key: {k}, length: {len(data[k])}")
                    return
            print("No valid list found in dictionary.")
            print(f"Full response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Unexpected response type: {type(data)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_candlestick()
