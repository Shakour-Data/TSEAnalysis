
import requests
import json

try:
    resp = requests.get("http://127.0.0.1:5000/api/symbols/1")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Status: {resp.status_code}")
        print(f"Symbols Count: {len(data)}")
        if len(data) > 0:
            print(f"First symbol: {data[0].get('l18')}")
    else:
        print(f"Error: {resp.status_code}")
        print(resp.text)
except Exception as e:
    print(f"Failed to connect: {e}")
