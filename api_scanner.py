
import requests
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
        return resp.status_code, resp.text[:100]
    except Exception as e: return 0, str(e)

endpoints = [
    ("Api/Tsetmc/IndexHistory.php", {"type": "1"}),
    ("Api/Tsetmc/HistoryIndex.php", {"type": "1"}),
    ("Api/Tsetmc/History.php", {"l18": "index_1", "type": "0"}),
    ("Api/Tsetmc/History.php", {"l18": "Overall_Index", "type": "0"}),
    ("Api/Tsetmc/History.php", {"l18": "TEDPIX", "type": "0"}),
    ("Api/Tsetmc/History.php", {"l18": "TEPIX", "type": "0"}),
    ("Api/Tsetmc/History.php", {"l18": "IRX6XTBP0001", "type": "0"}),
    ("Api/Tsetmc/IndexHistory.php", {"l18": "32097828799138957"}),
]

for ep, p in endpoints:
    status, text = call_api(ep, p)
    print(f"Testing {ep} with {p} -> Status: {status}, Sample: {text[:50]}")
