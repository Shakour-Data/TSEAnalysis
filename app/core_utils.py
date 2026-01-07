import os
import requests
import requests.utils
import urllib3
import threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== FIREWALL NUCLEAR OPTION =====
SAFE_BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
requests.utils.default_user_agent = lambda: SAFE_BROWSER_UA

TLS_CLIENT_AVAILABLE = False
CURL_CFFI_AVAILABLE = False
HTTPX_AVAILABLE = False

try:
    import tls_client
    TLS_CLIENT_AVAILABLE = True
except ImportError:
    pass

try:
    from curl_cffi import requests as crequests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    crequests = None

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None

# Exporting for other modules
try:
    import tls_client
except ImportError:
    tls_client = None

# Configuration
API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"
BRIDGE_URL = "https://script.google.com/macros/s/AKfycbxyrNakdMLbd8YsUAIYfgA9E5cP_66MNGkoTekIdC4FQhFcf-0p8n1CXqrDuWJBiE4w/exec"
PROXY_URL = None

stats = {
    "global": {"total": 0, "blocked": 0, "success": 0},
    "services": {}
}

def update_stats(service, status):
    global stats
    if service not in stats["services"]:
        stats["services"][service] = {"total": 0, "blocked": 0, "success": 0}
    stats["global"]["total"] += 1
    stats["services"][service]["total"] += 1

    if status == "blocked":
        stats["global"]["blocked"] += 1
        stats["services"][service]["blocked"] += 1
    elif status == "success":
        stats["global"]["success"] += 1
        stats["services"][service]["success"] += 1
