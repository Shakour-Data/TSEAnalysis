
import requests
import json
import time

# Use the bridge URL from app.py
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbxyrNakdMLbd8YsUAIYfgA9E5cP_66MNGkoTekIdC4FQhFcf-0p8n1CXqrDuWJBiE4w/exec" 
API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"

def call_api(endpoint, params):
    try:
        query = params.copy()
        query["key"] = API_KEY
        
        # Format for bridge
        # The bridge usually takes 'url' as a parameter
        target_url = f"https://brsapi.ir/{endpoint}"
        full_query = "&".join([f"{k}={v}" for k, v in query.items()])
        bridge_target = f"{target_url}?{full_query}"
        
        print(f"Testing: {endpoint} with {params}")
        resp = requests.get(BRIDGE_URL, params={"url": bridge_target}, timeout=20)
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            return data
        except:
            return resp.text[:200]
    except Exception as e:
        return str(e)

# 1. Check Index.php Type 1 (Total Index)
print("\n--- Testing Index.php type=1 ---")
idx1 = call_api("Api/Tsetmc/Index.php", {"type": "1"})
print(json.dumps(idx1, indent=2, ensure_ascii=False))

# 2. Check Index.php Type 3 (All Indices)
print("\n--- Testing Index.php type=3 ---")
idx3 = call_api("Api/Tsetmc/Index.php", {"type": "3"})
if isinstance(idx3, list):
    print(f"Got {len(idx3)} indices. Sample:")
    print(json.dumps(idx3[:2], indent=2, ensure_ascii=False))

# 3. Try predicted IndexHistory endpoint
print("\n--- Testing IndexHistory.php type=1 ---")
hist = call_api("Api/Tsetmc/IndexHistory.php", {"type": "1"})
if isinstance(hist, list):
    print(f"SUCCESS! Got {len(hist)} historical records from IndexHistory.php")
    print(json.dumps(hist[0], indent=2, ensure_ascii=False))
else:
    print(f"IndexHistory.php failed or returned: {hist}")

# 4. Try History.php with a known index code if found (e.g. TEDPIX or code from idx3)
# If IndexHistory.php failed, maybe standard History.php works if we know the right symbol.
