import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
    "DNT": "1",
    "Connection": "keep-alive",
})

url = "https://brsapi.ir/Api/Tsetmc/AllSymbols.php"
params = {"type": "1", "key": "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"}

try:
    print(f"Connecting to {url}...")
    response = session.get(url, params=params, timeout=15, verify=False)
    print(f"Status Code: {response.status_code}")
    print(f"Content Sample: {response.text[:100]}")
except Exception as e:
    print(f"Error: {e}")
