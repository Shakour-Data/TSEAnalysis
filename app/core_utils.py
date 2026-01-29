import os
import requests
import requests.utils
import urllib3
import threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== FIREWALL NUCLEAR OPTION =====
# WARNING: These techniques may violate website TOS and could be illegal.
# Use at your own risk. Consider using official APIs or proxies instead.
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
API_KEY = os.getenv('TSE_API_KEY', '677e4860b2d6a')
BRIDGE_URL = os.getenv('BRIDGE_URL')
PROXY_URL = os.getenv('PROXY_URL')

stats = {
    "global": {"total": 0, "blocked": 0, "success": 0},
    "services": {},
    "history": [] # Track last 50 requests
}

def update_stats(service, status, endpoint=None):
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
    
    # Update History
    from datetime import datetime
    stats["history"].insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "service": service,
        "endpoint": endpoint or "Unknown",
        "status": status
    })
    stats["history"] = stats["history"][:50]
