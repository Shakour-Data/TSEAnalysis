import tls_client

API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"
BASE_URL = "https://brsapi.ir"

CHROME_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://brsapi.ir/",
}

def classify(symbol):
    cs_id = str(symbol.get("cs_id") or symbol.get("csId") or "").strip()
    cs_name = str(symbol.get("cs") or "").strip()
    flow = str(symbol.get("flow") or "").strip()
    ticker = str(symbol.get("l18") or symbol.get("symbol") or "")
    
    if cs_id == "68" or "ETF" in cs_name.upper() or "صندوق" in cs_name: return "etf"
    if cs_id == "69" or any(k in cs_name for k in ["اوراق", "صکوک", "گام"]): return "fixed_income"
    if cs_id == "59" or ticker.startswith("تسه"): return "tashilat"
    
    if flow in ["1", "2"]: return "bourse"
    if flow in ["3", "4"]: return "farabourse"
    if flow in ["5", "6", "7", "8"]: return "base"
    return "bourse" # Default fallback

def run():
    print("Connecting with tls_client (Chrome 120 JA3 Fingerprint)...")
    url = f"{BASE_URL}/Api/Tsetmc/AllSymbols.php?type=1&key={API_KEY}"
    
    try:
        # Create session with Chrome 120 JA3 fingerprint
        session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True
        )
        
        r = session.get(url, headers=CHROME_HEADERS)
        data = r.json()
        print(f"Success! Retrieved {len(data)} symbols.")
        
        counts = {}
        for s in data:
            cat = classify(s)
            counts[cat] = counts.get(cat, 0) + 1
            
        print("\n--- Market Counts ---")
        labels = {
            "bourse": "Tehran Stock Exchange (Bourse)",
            "farabourse": "Iran Fara Bourse",
            "base": "Base Market (Payeh)",
            "etf": "ETFs",
            "fixed_income": "Fixed Income / Bonds",
            "tashilat": "Housing Facilities"
        }
        for k, v in counts.items():
            print(f"{labels.get(k, k)}: {v}")
            
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    run()
