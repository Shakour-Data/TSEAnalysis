
import requests
import urllib.parse

API_KEY = "677e4860b2d6a"
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbxyrNakdMLbd8YsUAIYfgA9E5cP_66MNGkoTekIdC4FQhFcf-0p8n1CXqrDuWJBiE4w/exec"
TARGET_URL = f"https://brsapi.ir/Api/Tsetmc/Symbol.php?key={API_KEY}&l18=وبملت"

def test_bridge():
    encoded_target = urllib.parse.quote(TARGET_URL, safe='')
    bridge_request_url = f"{BRIDGE_URL}?url={encoded_target}"
    
    print(f"Testing Bridge: {bridge_request_url}")
    try:
        resp = requests.get(bridge_request_url, timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:500]}")
    except Exception as e:
        print(f"Bridge error: {e}")

if __name__ == "__main__":
    test_bridge()
