
import subprocess
import json
from urllib.parse import urlencode
import shutil

API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"
BASE_URL = "https://brsapi.ir"

def curl_request(endpoint, params):
    curl_path = shutil.which("curl") or shutil.which("curl.exe")
    if not curl_path:
        return None
    
    params['key'] = API_KEY
    encoded = urlencode(params)
    url = f"{BASE_URL}/{endpoint}?{encoded}"
    
    headers = [
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "-H", "Accept: application/json, text/plain, */*",
        "-H", "Accept-Language: en-US,en;q=0.9,fa;q=0.8",
        "-H", "Accept-Encoding: gzip, deflate, br",
        "-H", "Connection: keep-alive",
        "-H", "Referer: https://brsapi.ir/"
    ]
    
    cmd = [curl_path, "-sS", "-k", "--compressed"] + headers + [url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        output = result.stdout.strip()
        try:
            return json.loads(output.lstrip('\ufeff'))
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return None
    else:
        print(f"DEBUG: Curl failed with code {result.returncode}")
        print(f"DEBUG: Error: {result.stderr}")
    return None

def test_farabourse_symbols():
    for t in ["1", "2"]:
        print(f"\n--- Testing Type {t} ---")
        data = curl_request("Api/Tsetmc/AllSymbols.php", {"type": t})
        if not data or not isinstance(data, list):
            print(f"No/Invalid data for type {t}")
            continue
            
        print(f"Total symbols in Type {t}: {len(data)}")
        
        flow_counts = {}
        market_counts = {}
        
        for sym in data:
            f = str(sym.get('flow', 'None'))
            m = 'None'
            for k in ["market", "marketName", "market_name", "flowTitle"]:
                if sym.get(k):
                    m = str(sym.get(k))
                    break
            
            flow_counts[f] = flow_counts.get(f, 0) + 1
            market_counts[m] = market_counts.get(m, 0) + 1
            
            is_farabourse = "فرابورس" in m or f in ["3", "4"]
            if is_farabourse:
                if flow_counts[f] <= 2:
                    print(f"Candidate Farabourse: Ticker={sym.get('l18')} / Market={m} / Flow={f} / Name={sym.get('cs')}")

        print("\nFlow distribution:")
        for f, c in sorted(flow_counts.items()):
            print(f"  Flow {f}: {c}")
            
        print("\nMarket distribution:")
        for m, c in market_counts.items():
            print(f"  Market {m}: {c}")

if __name__ == "__main__":
    test_farabourse_symbols()
