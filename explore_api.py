
from curl_cffi import requests
import json

def check_type(api_type):
    url = f"https://brsapi.ir/FreeTsetmcApi/Api/Tsetmc/AllSymbols.php?type={api_type}"
    try:
        response = requests.get(url, impersonate="chrome110", timeout=20)
        data = response.json()
        print(f"--- API Type {api_type} ---")
        if isinstance(data, list):
            print(f"Count: {len(data)}")
            markets = {}
            for s in data[:200]:
                m = s.get('market_name') or s.get('flowTitle') or s.get('market') or "Unknown"
                markets[m] = markets.get(m, 0) + 1
            print(f"Markets in first 200: {markets}")
            if data:
                print(f"Sample: {data[0].get('l18')} - {data[0].get('isin')} - {data[0].get('cs')}")
        else:
            print(f"Response: {data}")
    except Exception as e:
        print(f"Error Type {api_type}: {e}")

for i in [1, 2, 3]:
    check_type(i)
