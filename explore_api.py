import requests
import urllib3
import json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
})

url = "https://brsapi.ir/Api/Tsetmc/AllSymbols.php"
api_key = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"

def check_type(type_code):
    print(f"\n--- Testing Type {type_code} ---")
    params = {"type": str(type_code), "key": api_key}
    try:
        response = session.get(url, params=params, timeout=10, verify=False)
        if response.status_code != 200:
            print(f"Failed with status {response.status_code}")
            return
        
        data = response.json()
        if not isinstance(data, list):
            print(f"Unexpected format: {type(data)}")
            if isinstance(data, dict) and "error" in data:
                 print(f"Error: {data['error']}")
            return

        print(f"Count: {len(data)}")
        if len(data) > 0:
            print(f"Sample: {data[0]}")
            # Collect Sector IDs (cs_id)
            cs_ids = set()
            for item in data:
                if 'cs_id' in item:
                    cs_ids.add(item['cs_id'])
            print(f"Distinct cs_ids: {len(cs_ids)}")
            # print(f"First 10 cs_ids: {list(cs_ids)[:10]}")
    except Exception as e:
        print(f"Error: {e}")

for i in range(1, 6):
    check_type(i)
