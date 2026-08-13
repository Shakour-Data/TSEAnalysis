
import os
import requests
import json

# API Key from app/core_utils.py
API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"
SYMBOL = "وبملت"

def test_api_key():
    print(f"Testing API Key: {API_KEY}")
    url = f"https://brsapi.ir/Api/Tsetmc/Symbol.php?key={API_KEY}&l18={SYMBOL}"
    
    try:
        resp = requests.get(url, timeout=15)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_key()
