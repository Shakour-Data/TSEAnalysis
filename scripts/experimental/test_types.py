
from curl_cffi import requests
import json

def check_type(api_type):
    url = f"https://brsapi.ir/FreeTsetmcApi/Api/Tsetmc/AllSymbols.php?type={api_type}"
    try:
        response = requests.get(url, impersonate="chrome110", timeout=20)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            print(f"Type {api_type}: {len(data)} symbols")
            sample = data[0]
            print(f"  Sample: {sample.get('l18')} | Market: {sample.get('market_name')} | CS: {sample.get('cs')}")
        else:
            print(f"Type {api_type}: Empty or error")
    except Exception as e:
        print(f"Type {api_type}: Error {e}")

if __name__ == "__main__":
    for i in range(1, 11):
        check_type(i)
