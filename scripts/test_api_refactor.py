import requests
import json

url = "http://127.0.0.1:5000/api/fetch_data"
payload = {
    "symbol": "فولاد",
    "asset_type": "tse"
}
headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
except Exception as e:
    print(f"Error: {e}")
