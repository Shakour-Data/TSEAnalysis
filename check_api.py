import requests
import json

url = "https://brsapi.ir/Api/Tsetmc/Index.php?key=BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3&type=1"

try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print("Response is valid JSON")
        if isinstance(data, list):
            print(f"Response is a list with {len(data)} items.")
        else:
            print(f"Response is not a list, it is a {type(data)}")
    except json.JSONDecodeError:
        print("Response is not valid JSON")
        print(f"Raw response: {response.text[:200]}")
except Exception as e:
    print(f"Connection error: {e}")
