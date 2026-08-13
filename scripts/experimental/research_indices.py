
import requests
import json
import urllib.parse

BRIDGE_URL = "https://script.google.com/macros/s/AKfycbxyrNakdMLbd8YsUAIYfgA9E5cP_66MNGkoTekIdC4FQhFcf-0p8n1CXqrDuWJBiE4w/exec" 
API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"

def call_api_direct(endpoint, params):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    })
    try:
        query = params.copy()
        query["key"] = API_KEY
        target_url = f"https://brsapi.ir/{endpoint}"
        resp = session.get(target_url, params=query, timeout=20)
        print(f"Direct Status for {endpoint}: {resp.status_code}")
        try: return resp.json()
        except: return resp.text[:100]
    except Exception as e: return str(e)

print("\n--- Testing Direct IndexHistory.php type=1 ---")
res1 = call_api_direct("Api/Tsetmc/IndexHistory.php", {"type": "1"})
print(f"Result: {str(res1)[:200]}")

print("\n--- Testing Direct Candlestick.php with index_1 ---")
res_c1 = call_api_direct("Api/Tsetmc/Candlestick.php", {"l18": "index_1", "adjusted": "false"})
print(f"Result: {str(res_c1)[:200]}")

