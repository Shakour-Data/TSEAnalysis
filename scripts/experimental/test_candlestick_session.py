
import requests
import json
import urllib3
urllib3.disable_warnings()

API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"
BASE_URL = "https://brsapi.ir"

def test_candlestick_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })

    endpoint = "Api/Tsetmc/Candlestick.php"
    params = {"key": API_KEY, "l18": "وبملت", "adjusted": "true"}
    
    print(f"Connecting to {BASE_URL}/{endpoint}...")
    try:
        response = session.get(f"{BASE_URL}/{endpoint}", params=params, timeout=20, verify=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Success! Body length: {len(response.text)}")
            print(f"Preview: {response.text[:200]}")
        else:
            print(f"Body: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_candlestick_session()
