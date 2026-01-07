
import requests
import json
import subprocess

url = "https://brsapi.ir/FreeTsetmcApi/Api/Tsetmc/AllSymbols.php"
PROXY_URL = "http://127.0.0.1:2081" # Just in case

def fetch(t):
    try:
        res = requests.get(f"{url}?type={t}", timeout=10)
        data = res.json()
        print(f"Type {t}: {len(data) if isinstance(data, list) else data}")
        if isinstance(data, list) and len(data) > 0:
            sample = data[0]
            print(f"  Sample: {sample.get('l18')} - {sample.get('market_name') or sample.get('market') or sample.get('flowTitle')}")
            # print all markets found in first 50
            markets = set()
            for s in data[:100]:
                m = s.get('market_name') or s.get('market') or s.get('flowTitle') or s.get('flow_title')
                if m: markets.add(m)
            print(f"  Markets found: {markets}")
    except Exception as e:
        print(f"Type {t} Error: {e}")

for i in range(1, 6):
    fetch(i)
