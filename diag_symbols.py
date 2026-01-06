import requests
import os

API_KEY = 'BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3'
BASE_URL = 'https://brsapi.ir'

def diag():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
        "DNT": "1",
        "Connection": "keep-alive",
    }
    for i in range(1, 11):
        try:
            url = f"{BASE_URL}/Api/Tsetmc/AllSymbols.php"
            resp = requests.get(url, params={"key": API_KEY, "type": i}, headers=headers, timeout=15)
            # BrsApi sometimes returns a string if there's an error
            try:
                data = resp.json()
            except:
                print(f"Type {i}: Not JSON: {resp.text[:50]}")
                continue

            if isinstance(data, list):
                print(f"Type {i}: {len(data)} items")
                if len(data) > 0:
                    print(f"  Sample: {data[0].get('l18')} - {data[0].get('l30')} (Market: {data[0].get('market', 'N/A')}, Sector: {data[0].get('sector', 'N/A')}, cs_id: {data[0].get('cs_id', 'N/A')})")
            else:
                print(f"Type {i}: Error or not a list: {data}")
        except Exception as e:
            print(f"Type {i}: Failed - {e}")

if __name__ == '__main__':
    diag()
