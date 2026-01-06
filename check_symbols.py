import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
})

url = "https://brsapi.ir/Api/Tsetmc/AllSymbols.php"
api_key = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"

def check_symbol_in_type(type_code, targets):
    print(f"\nScanning Type {type_code} for {targets}...")
    params = {"type": str(type_code), "key": api_key}
    try:
        response = session.get(url, params=params, timeout=10, verify=False)
        data = response.json()
        found = []
        if isinstance(data, list):
            for item in data:
                if item.get('l18') in targets or item.get('l30') in targets:
                    found.append(item)
                    print(f"  Found: {item['l18']} ({item['l30']}) - Market: {item.get('market')} / Sector: {item.get('cs')}")
        else:
            print("Data is not list")
        
        if not found:
            print("  No targets found.")
            
    except Exception as e:
        print(f"Error: {e}")

# Targets: Folad (Bourse), Arya (FaraBourse), Zagros (FaraBourse), Khodro (Bourse), Tapco (Base?)
targets = ["فولاد", "آریا", "زاگرس", "خودرو", "تپکو"]
check_symbol_in_type(1, targets)
check_symbol_in_type(2, targets)
