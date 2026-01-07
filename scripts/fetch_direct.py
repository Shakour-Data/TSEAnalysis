import requests
import json

# تنظیمات طبق مستندات brs_WebService_Guide.md
API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"
BASE_URL = "https://brsapi.ir"

def fetch_live_data():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })

    # دریافت لیست نمادها (بورس تهران - Type 1)
    endpoint = "Api/Tsetmc/AllSymbols.php"
    params = {"key": API_KEY, "type": "1"}
    
    print(f"Connecting to {BASE_URL}/{endpoint}...")
    
    try:
        response = session.get(f"{BASE_URL}/{endpoint}", params=params, timeout=20, verify=False)
        if response.status_code == 200:
            data = response.json()
            print("--- SUCCESS! Data received from WebService ---")
            print(f"Total Symbols: {len(data)}")
            print("Sample Data (First 3 symbols):")
            print(json.dumps(data[:3], indent=4, ensure_ascii=False))
            
            # ذخیره در فایل محلی برای استفاده در برنامه
            with open("tmp_type1.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        else:
            print(f"Failed! Status Code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")

if __name__ == "__main__":
    fetch_live_data()
