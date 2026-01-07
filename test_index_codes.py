
import requests
import json

BRIDGE_URL = "https://script.google.com/macros/s/AKfycbxyrNakdMLbd8YsUAIYfgA9E5cP_66MNGkoTekIdC4FQhFcf-0p8n1CXqrDuWJBiE4w/exec" 
API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"

def call_api(endpoint, params):
    try:
        query = params.copy()
        query["key"] = API_KEY
        target_url = f"https://brsapi.ir/{endpoint}"
        full_query = "&".join([f"{k}={v}" for k, v in query.items()])
        bridge_target = f"{target_url}?{full_query}"
        resp = requests.get(BRIDGE_URL, params={"url": bridge_target}, timeout=20)
        try: return resp.json()
        except: return resp.text[:100]
    except Exception as e: return str(e)

# Index codes (standard TSETMC codes)
indices = {
    "Total_Index": "32097828799138957",
    "Farabourse_Total": "43685683301327944",
}

for name, code in indices.items():
    print(f"\n--- Testing {name} ({code}) with History.php ---")
    res = call_api("Api/Tsetmc/History.php", {"l18": code, "type": "0"})
    if isinstance(res, list): print(f"  SUCCESS! Records: {len(res)}")
    else: print(f"  FAILED: {res}")

    print(f"\n--- Testing {name} ({code}) with Candlestick.php ---")
    res = call_api("Api/Tsetmc/Candlestick.php", {"l18": code, "adjusted": "false"})
    if isinstance(res, dict) and "candle_daily" in res: print(f"  SUCCESS! Records: {len(res['candle_daily'])}")
    elif isinstance(res, list): print(f"  SUCCESS! Records: {len(res)}")
    else: print(f"  FAILED: {res}")
