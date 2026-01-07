
import subprocess
import json
import time

def fetch_with_curl(type_code):
    url = f"https://brsapi.ir/FreeTsetmcApi/Api/Tsetmc/AllSymbols.php?type={type_code}"
    cmd = [
        "curl", "-s", "-L", "-k", "--compressed",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return f"Error {result.returncode}"
        data = json.loads(result.stdout)
        return data
    except Exception as e:
        return str(e)

for i in range(1, 6):
    print(f"Checking Type {i}...")
    data = fetch_with_curl(i)
    if isinstance(data, list):
        print(f"  Count: {len(data)}")
        markets = set()
        for s in data[:200]:
            m = s.get('market_name') or s.get('flowTitle') or s.get('market')
            if m: markets.add(m)
        print(f"  Sample Markets: {list(markets)}")
        if data:
            print(f"  Sample Symbol: {data[0].get('l18')} ({data[0].get('isin')})")
    else:
        print(f"  Error: {data}")
    time.sleep(2)
