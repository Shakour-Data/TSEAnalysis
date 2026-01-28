
import requests
import json

API_KEY = "677e4860b2d6a"
BASE_URL = "https://brsapi.ir"

def test_history_endpoint():
    url = f"{BASE_URL}/Api/Tsetmc/History.php?key={API_KEY}&l18=وبملت&type=0"
    print(f"Testing {url}")
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20, verify=False)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_history_endpoint()
