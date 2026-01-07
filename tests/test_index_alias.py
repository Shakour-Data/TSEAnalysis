
import requests
import json
import urllib.parse

BRIDGE_URL = "https://script.google.com/macros/s/AKfycbxyrNakdMLbd8YsUAIYfgA9E5cP_66MNGkoTekIdC4FQhFcf-0p8n1CXqrDuWJBiE4w/exec" 
API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"

def call_api(endpoint, params):
    try:
        query = params.copy()
        query["key"] = API_KEY
        target_url = f"https://brsapi.ir/{endpoint}"
        full_query = "&".join([f"{k}={v}" for k, v in query.items()])
        bridge_target = f"{target_url}?{full_query}"
        encoded_url = urllib.parse.quote(bridge_target, safe='')
        bridge_call = f"{BRIDGE_URL}?url={encoded_url}"
        resp = requests.get(bridge_call, timeout=20)
        try: return resp.json()
        except: return resp.text[:100]
    except Exception as e: return str(e)

print("\n--- Testing Candlestick.php with index_1 ---")
res = call_api("Api/Tsetmc/Candlestick.php", {"l18": "index_1", "adjusted": "false"})
if isinstance(res, list) or (isinstance(res, dict) and "candle_daily" in res):
    print("SUCCESS! index_1 works.")
    print(json.dumps(res, indent=2, ensure_ascii=False)[:500])
else:
    print(f"Failed: {res}")
