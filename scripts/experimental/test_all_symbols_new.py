
import requests
import json

API_KEY = "677e4860b2d6a"
BASE_URL = "https://brsapi.ir"

def test_all_symbols():
    url = f"{BASE_URL}/Api/Tsetmc/AllSymbols.php?key={API_KEY}&type=1"
    print(f"Testing {url}")
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20, verify=False)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Success! {len(data)} symbols found.")
        else:
            print(f"Body: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_all_symbols()
