import os
import json
import shutil
import subprocess
import ssl
import socket
from urllib.parse import urlencode
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== ANTI-NGFW MODULE =====
# Next-Generation Firewalls (NGFW) detect Python by:
# 1. TLS Fingerprint (JA3/JA3S) - The order and type of TLS extensions
# 2. HTTP/2 SETTINGS frame fingerprint
# 3. TCP window size and options
# We bypass ALL of these using tls_client which uses a real browser's TLS stack

TLS_CLIENT_AVAILABLE = False
CURL_CFFI_AVAILABLE = False
HTTPX_AVAILABLE = False

# Priority 1: tls_client (Best JA3 spoofing)
try:
    import tls_client
    TLS_CLIENT_AVAILABLE = True
    print("DEBUG: tls_client loaded - JA3 fingerprint spoofing ACTIVE")
except ImportError:
    print("DEBUG: tls_client not available")

# Priority 2: curl_cffi (Good alternative)
try:
    from curl_cffi import requests as crequests
    CURL_CFFI_AVAILABLE = True
    print("DEBUG: curl_cffi loaded as fallback")
except ImportError:
    crequests = None
    print("DEBUG: curl_cffi not available")

# Priority 3: httpx with HTTP/2
try:
    import httpx
    HTTPX_AVAILABLE = True
    print("DEBUG: httpx loaded as secondary fallback")
except ImportError:
    httpx = None
    print("DEBUG: httpx not available")

from datetime import datetime
import io
import random
from flask_caching import Cache
from technical_analysis import TechnicalAnalyzer

app = Flask(__name__)

# Configure Caching with memory limits
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_THRESHOLD': 500  # Limit the number of items in memory
})

API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"
BASE_URL = "https://brsapi.ir"
REQUEST_USAGE_LIMIT = 1.0  # Allow all requests

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


class TSETMCClient:
    """
    Anti-NGFW HTTP Client for Iranian Financial APIs
    
    This client implements multiple bypass techniques for Next-Generation Firewalls:
    1. TLS Fingerprint Spoofing (JA3) via tls_client
    2. Chrome Browser Impersonation via curl_cffi
    3. HTTP/2 with proper SETTINGS frames via httpx
    4. Native curl.exe as ultimate fallback
    
    NGFWs detect Python by analyzing:
    - TLS ClientHello extensions order (JA3 hash)
    - HTTP/2 SETTINGS frame values
    - TCP window scaling options
    - Connection timing patterns
    """
    
    # Chrome 120 Browser Headers (Exact match)
    CHROME_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://brsapi.ir/",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = BASE_URL
        self.active_client = None
        self.client_name = "none"
        
        # Initialize the best available client
        self._init_http_client()
        
        self.curl_path = shutil.which("curl") or shutil.which("curl.exe")
        if self.curl_path:
            print(f"DEBUG: Native curl fallback enabled via {self.curl_path}")
        
        self._symbols_cache = {}
        self._clear_cache_on_startup()
    
    def _init_http_client(self):
        """Initialize the best available HTTP client with proper TLS fingerprint."""
        
        # Priority 1: tls_client (Best JA3 fingerprint spoofing)
        if TLS_CLIENT_AVAILABLE:
            try:
                self.active_client = tls_client.Session(
                    client_identifier="chrome_120",
                    random_tls_extension_order=True
                )
                self.client_name = "tls_client (Chrome 120 JA3)"
                print(f"DEBUG: Using {self.client_name}")
                return
            except Exception as e:
                print(f"DEBUG: tls_client init failed: {e}")
        
        # Priority 2: curl_cffi
        if CURL_CFFI_AVAILABLE:
            try:
                self.active_client = crequests.Session()
                self.client_name = "curl_cffi (Chrome impersonate)"
                print(f"DEBUG: Using {self.client_name}")
                return
            except Exception as e:
                print(f"DEBUG: curl_cffi init failed: {e}")
        
        # Priority 3: httpx with HTTP/2
        if HTTPX_AVAILABLE:
            try:
                self.active_client = httpx.Client(
                    http2=True,
                    verify=False,
                    timeout=30.0,
                    headers=self.CHROME_HEADERS
                )
                self.client_name = "httpx (HTTP/2)"
                print(f"DEBUG: Using {self.client_name}")
                return
            except Exception as e:
                print(f"DEBUG: httpx init failed: {e}")
        
        # Fallback: Standard requests (will likely be blocked)
        self.active_client = requests.Session()
        self.active_client.headers.update(self.CHROME_HEADERS)
        self.client_name = "requests (standard - may be blocked)"
        print(f"DEBUG: Using {self.client_name}")

    def _clear_cache_on_startup(self):
        self._symbols_cache = {}
        print("DEBUG: Symbol cache cleared on startup")

    def _fetch_symbols_by_type(self, type_code):
        data = self._make_request("Api/Tsetmc/AllSymbols.php", {"type": str(type_code)}, service="symbols")
        if isinstance(data, list):
            if data:
                return data
            return {"error": f"وب‌سرویس برای نوع {type_code} داده‌ای بازنگرداند."}
        return data

    def _normalize_text(self, value):
        if value is None:
            return ""
        text = str(value).strip()
        return text.replace("ي", "ی").replace("ك", "ک")

    def _extract_market_name(self, symbol):
        preferred_keys = (
            "market", "marketName", "market_name", "flowTitle", "flow_title",
            "board", "boardTitle", "board_title"
        )
        for key in preferred_keys:
            if key in symbol and symbol[key]:
                return self._normalize_text(symbol[key])

        flow_code = str(symbol.get("flow") or "").strip()
        flows = {
            "1": "بورس",
            "2": "بورس",
            "3": "فرابورس",
            "4": "فرابورس",
            "5": "بازار پایه",
            "6": "بازار پایه",
            "7": "بازار پایه",
            "8": "بازار پایه",
        }
        return flows.get(flow_code, "")

    def _classify_equity_market(self, symbol):
        cs_id = str(symbol.get("cs_id") or symbol.get("csId") or "").strip()
        cs_name = self._normalize_text(symbol.get("cs", ""))
        market_name = self._extract_market_name(symbol)
        ticker = str(symbol.get("l18") or symbol.get("symbol") or "")
        flow = str(symbol.get("flow") or "").strip()

        # 1. ETFs and Funds
        if cs_id == "68" or "ETF" in cs_name.upper() or "صندوق" in cs_name or "سرمایه گذاری" in cs_name:
            return "etf"
        
        # 2. Fixed Income / Bonds
        if cs_id == "69" or any(k in cs_name for k in ["اوراق", "صکوک", "اجاره", "مرابحه", "منفعت", "گام"]):
            return "fixed_income"
            
        # 3. Housing Facilities
        if cs_id == "59" or "تسهیلات" in cs_name or "مسکن" in cs_name or ticker.startswith("تسه"):
            return "tashilat"

        # 4. Primary Market Classification by Flow (Most reliable)
        if flow in ["1", "2"]:
            return "bourse"
        if flow in ["3", "4"]:
            return "farabourse"
        if flow in ["5", "6", "7", "8"]:
            return "base"

        # 5. Fallback/Heuristic categorization
        if "پایه" in market_name or ticker.endswith("4") or any(k in market_name for k in ["زرد", "نارنجی", "قرمز"]):
            return "base"
        
        if "فرابورس" in market_name:
            return "farabourse"
            
        if "بورس" in market_name or "بازار اول" in market_name or "بازار دوم" in market_name:
            return "bourse"

        return "bourse"

    def _get_equity_universe(self):
        cache_key = "symbols_equity_universe"
        now = datetime.now()
        cached = self._symbols_cache.get(cache_key)
        if cached:
            data, timestamp = cached
            if (now - timestamp).total_seconds() < 600:
                return data

        universe = self._fetch_symbols_by_type("1")
        if isinstance(universe, list):
            self._symbols_cache[cache_key] = (universe, now)
        return universe

    def _filter_equities_by_category(self, categories):
        equities = self._get_equity_universe()
        if isinstance(equities, dict):
            return equities

        allowed = set(categories)
        filtered = [sym for sym in equities if self._classify_equity_market(sym) in allowed]
        if not filtered:
            return {"error": "هیچ نمادی با این بازار یافت نشد."}
        return filtered

    def _merge_symbol_lists(self, *lists):
        merged = {}
        for lst in lists:
            if not isinstance(lst, list):
                continue
            for item in lst:
                key = item.get('isin') or item.get('l18') or item.get('insCode') or item.get('id')
                if key and key not in merged:
                    merged[key] = item
        return list(merged.values())

    def _make_request(self, endpoint, params=None, service=None):
        """
        Anti-NGFW Request Handler with multiple bypass techniques.
        
        Tries in order:
        1. tls_client (Chrome 120 JA3 fingerprint)
        2. curl_cffi (Chrome impersonation)
        3. httpx (HTTP/2)
        4. Native curl.exe (OS-level bypass)
        5. Standard requests (last resort)
        """
        # Service Classification
        if not service:
            if "AllSymbols" in endpoint: service = "symbols"
            elif "Index" in endpoint: service = "indices"
            elif "Symbol" in endpoint: service = "realtime"
            elif "History" in endpoint: service = "history"
            elif "Candlestick" in endpoint: service = "technical"
            elif "Transaction" in endpoint: service = "transactions"
            elif "Shareholder" in endpoint: service = "shareholders"
            elif "Nav" in endpoint: service = "nav"
            elif "Announcement" in endpoint: service = "codal"

        url = f"{self.base_url}/{endpoint}"
        query = params.copy() if params else {}
        query["key"] = self.api_key
        full_url = f"{url}?{urlencode(query)}"
        
        # Method 1: tls_client (Best JA3 spoofing)
        if TLS_CLIENT_AVAILABLE and isinstance(self.active_client, tls_client.Session):
            try:
                print(f"DEBUG: Trying tls_client for {endpoint}...")
                response = self.active_client.get(
                    full_url,
                    headers=self.CHROME_HEADERS
                )
                if response.status_code == 200:
                    data = response.json()
                    update_stats(service or "unknown", "success")
                    print(f"DEBUG: tls_client SUCCESS for {endpoint}")
                    return data
            except Exception as e:
                print(f"DEBUG: tls_client failed: {e}")
        
        # Method 2: curl_cffi with Chrome impersonation
        if CURL_CFFI_AVAILABLE:
            try:
                print(f"DEBUG: Trying curl_cffi for {endpoint}...")
                response = crequests.get(
                    full_url,
                    headers=self.CHROME_HEADERS,
                    impersonate="chrome120",
                    timeout=20,
                    verify=False
                )
                if response.status_code == 200:
                    data = response.json()
                    update_stats(service or "unknown", "success")
                    print(f"DEBUG: curl_cffi SUCCESS for {endpoint}")
                    return data
            except Exception as e:
                print(f"DEBUG: curl_cffi failed: {e}")
        
        # Method 3: httpx with HTTP/2
        if HTTPX_AVAILABLE:
            try:
                print(f"DEBUG: Trying httpx HTTP/2 for {endpoint}...")
                with httpx.Client(http2=True, verify=False, timeout=20.0) as client:
                    response = client.get(full_url, headers=self.CHROME_HEADERS)
                    if response.status_code == 200:
                        data = response.json()
                        update_stats(service or "unknown", "success")
                        print(f"DEBUG: httpx SUCCESS for {endpoint}")
                        return data
            except Exception as e:
                print(f"DEBUG: httpx failed: {e}")
        
        # Method 4: Native curl.exe (OS-level bypass)
        fallback = self._curl_fallback_request(url, query)
        if fallback is not None:
            update_stats(service or "unknown", "success")
            print(f"DEBUG: Native curl SUCCESS for {endpoint}")
            return fallback
        
        # Method 5: Standard requests (last resort)
        try:
            print(f"DEBUG: Trying standard requests for {endpoint}...")
            response = requests.get(
                full_url,
                headers=self.CHROME_HEADERS,
                timeout=15,
                verify=False
            )
            if response.status_code == 200:
                data = response.json()
                update_stats(service or "unknown", "success")
                return data
        except Exception as e:
            print(f"DEBUG: Standard requests failed: {e}")
        
        # All methods failed
        update_stats(service or "unknown", "blocked")
        error_msg = "تمام روش‌های اتصال به سرور ناموفق بود. "
        error_msg += "(احتمالاً فایروال نسل جدید یا محدودیت IP)"
        return {"error": error_msg}


    def _curl_fallback_request(self, url, params):
        """Native curl.exe fallback with full Chrome impersonation headers."""
        if not self.curl_path:
            return None

        try:
            encoded = urlencode(params or {}, doseq=True)
            full_url = f"{url}?{encoded}" if encoded else url
            
            # Full Chrome headers for curl
            header_args = [
                "-H", f"User-Agent: {self.CHROME_HEADERS['User-Agent']}",
                "-H", f"Accept: {self.CHROME_HEADERS['Accept']}",
                "-H", f"Accept-Language: {self.CHROME_HEADERS['Accept-Language']}",
                "-H", "Accept-Encoding: gzip, deflate, br",
                "-H", "Connection: keep-alive",
                "-H", f"Referer: {self.CHROME_HEADERS['Referer']}",
                "-H", f"Sec-Ch-Ua: {self.CHROME_HEADERS['Sec-Ch-Ua']}",
                "-H", "Sec-Ch-Ua-Mobile: ?0",
                "-H", 'Sec-Ch-Ua-Platform: "Windows"',
                "-H", "Sec-Fetch-Dest: empty",
                "-H", "Sec-Fetch-Mode: cors",
                "-H", "Sec-Fetch-Site: same-origin",
            ]

            cmd = [
                self.curl_path,
                "-sS",
                "-k",
                "--compressed",
                "--http2",  # Force HTTP/2
                "--max-time", "25",
                "--tlsv1.3",  # Force TLS 1.3
            ] + header_args + [full_url]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"DEBUG: curl fallback failed ({result.returncode}): {result.stderr.strip()[:200]}")
                return None

            body = result.stdout.strip().lstrip('\ufeff')
            if not body:
                print("DEBUG: curl fallback returned empty body")
                return None

            return json.loads(body)
        except Exception as exc:
            print(f"DEBUG: curl fallback exception: {exc}")
            return None

    def get_all_symbols(self, market_type):
        """Return enriched symbol lists for each market selection with caching."""
        cache_key = f"symbols_{market_type}"
        now = datetime.now()
        cached = self._symbols_cache.get(cache_key)
        if cached:
            data, timestamp = cached
            if (now - timestamp).total_seconds() < 600:
                return data

        stale_keys = [k for k, (_, ts) in self._symbols_cache.items() if (now - ts).total_seconds() > 3600]
        for key in stale_keys:
            self._symbols_cache.pop(key, None)

        result_symbols = []

        # Helper to filter equities (exclude ETFs, Bonds, etc if needed)
        # Based on exploration: cs_id 68 = ETF, 69 = Bonds (Type 4), 59 = Housing (Type 5)
        # Type 1 seems to contain all Equities + ETFs.
        
        if market_type == "1":  # Bourse Tehran (Equities)
            result_symbols = self._filter_equities_by_category({"bourse"})

        elif market_type == "2":  # FaraBourse (Equities)
            result_symbols = self._filter_equities_by_category({"farabourse"})

        elif market_type == "4":  # Base Market (Payeh)
            result_symbols = self._filter_equities_by_category({"base"})

        elif market_type == "5":  # ETF Funds
            result_symbols = self._filter_equities_by_category({"etf"})

        elif market_type == "fixed_income":  # Fixed Income / Bonds
            bonds = self._fetch_symbols_by_type("4")
            if isinstance(bonds, list):
                result_symbols = bonds
            elif isinstance(bonds, dict):
                fallback = self._filter_equities_by_category({"fixed_income"})
                result_symbols = fallback

        elif market_type == "3":  # Bourse Kala & Ati (Derivatives/Coins)
            # API Type 2 (Coins) and Type 3 (Futures)
            futures = self._fetch_symbols_by_type("3")
            coins = self._fetch_symbols_by_type("2")
            lists_to_merge = []
            errors = []
            for dataset in (futures, coins):
                if isinstance(dataset, list):
                    lists_to_merge.append(dataset)
                elif isinstance(dataset, dict):
                    errors.append(dataset)
            if lists_to_merge:
                result_symbols = self._merge_symbol_lists(*lists_to_merge)
            elif errors:
                result_symbols = errors[0]
        
        elif market_type == "tashilat":  # Housing Facilities
            housing = self._fetch_symbols_by_type("5")
            if isinstance(housing, list):
                result_symbols = housing
            elif isinstance(housing, dict):
                fallback = self._filter_equities_by_category({"tashilat"})
                result_symbols = fallback

        elif market_type == "indices_market":
            # ... existing logic ...
            lists = []
            errors = []
            for idx_type, prefix in (("1", "بورس"), ("2", "فرابورس")):
                data = self._make_request("Api/Tsetmc/Index.php", {"type": idx_type}, service="indices")
                if isinstance(data, list):
                    lists.extend([
                        {"id": f"idx_{prefix}_{i}", "l18": item.get('l18') or item.get('name'), "l30": item.get('l30') or f"شاخص {prefix} {item.get('name', '')}"}
                        for i, item in enumerate(data)
                    ])
                elif isinstance(data, dict):
                    errors.append(data)
            result_symbols = lists if lists else (errors[0] if errors else {"error": "دریافت شاخص‌ها با خطا مواجه شد."})

        elif market_type == "indices_industry":
             # ... existing logic ...
            equities = self._get_equity_universe()
            if isinstance(equities, dict):
                result_symbols = equities
            else:
                sectors = sorted({self._normalize_text(s.get('cs')) for s in equities if s.get('cs')})
                if sectors:
                    result_symbols = [{"id": f"ind_{idx}", "l18": sector, "l30": f"شاخص صنعت {sector}"} for idx, sector in enumerate(sectors)]

        if isinstance(result_symbols, dict):
            return result_symbols

        if result_symbols:
            unique = {}
            for item in result_symbols:
                # Prioritize keys for display
                key = item.get('isin') or item.get('l18') or item.get('id')
                if key and key not in unique:
                    unique[key] = item
            cleaned = list(unique.values())
            self._symbols_cache[cache_key] = (cleaned, now)
            return cleaned

        return {"error": "داده‌ای با معیارهای انتخاب شده یافت نشد."}

    def get_symbol_info(self, symbol):
        return self._make_request("Api/Tsetmc/Symbol.php", {"l18": symbol}, service="realtime")

    def get_price_history(self, symbol, data_type=0, adjusted=True, service=None):
        return self._make_request("Api/Tsetmc/History.php", {
            "l18": symbol,
            "type": data_type,
            "adjusted": str(adjusted).lower()
        }, service=service)

    def get_candlestick(self, symbol, adjusted=True, type=1):
        # Candlestick API requires 'type' parameter and returns a dict
        # type=1: intraday, type=2: daily, type=3: daily adjusted
        res = self._make_request("Api/Tsetmc/Candlestick.php", {
            "l18": symbol, 
            "adjusted": str(adjusted).lower(),
            "type": type
        })
        key_map = {1: 'candle_intraday', 2: 'candle_daily', 3: 'candle_daily_adjusted'}
        key = key_map.get(type, 'candle_intraday')
        
        if res and isinstance(res, dict) and key in res:
            return res[key]
        return res

    def get_transactions(self, symbol):
        return self._make_request("Api/Tsetmc/Transaction.php", {"l18": symbol})

    def get_shareholders(self, symbol):
        return self._make_request("Api/Tsetmc/Shareholder.php", {"l18": symbol})

    def get_indices(self, index_type):
        return self._make_request("Api/Tsetmc/Index.php", {"type": index_type})

    def get_nav(self, symbol):
        return self._make_request("Api/Tsetmc/Nav.php", {"l18": symbol})

    def get_codal_announcements(self, symbol=None, category=None, date_start=None, date_end=None):
        params = {}
        if symbol and symbol != "all":
            params["symbol"] = symbol  # Changed from l18 to symbol as per standard Codal API naming
        if category:
            params["category"] = category
        if date_start:
            params["date_start"] = date_start.replace('/', '-')
        if date_end:
            params["date_end"] = date_end.replace('/', '-')
        
        res = self._make_request("Api/Codal/Announcement.php", params)
        # If symbol search fails, try with l18 as fallback
        if (not res or (isinstance(res, dict) and "error" in res)) and symbol and symbol != "all":
            params["l18"] = symbol
            if "symbol" in params: del params["symbol"]
            res = self._make_request("Api/Codal/Announcement.php", params)

        if res and isinstance(res, dict) and 'announcement' in res:
            return res['announcement']
        return res

client = TSETMCClient(API_KEY)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api_test')
def api_test():
    return render_template('api_test.html')

@app.route('/api/symbols/<market_type>')
@cache.memoize(timeout=3600)
def get_symbols(market_type):
    print(f"DEBUG: Received request for symbols of type: {market_type}")
    symbols = client.get_all_symbols(market_type)
    if isinstance(symbols, dict) and "error" in symbols:
        return jsonify(symbols)
    return jsonify(symbols if symbols else [])

@app.route('/api/fetch_data', methods=['POST'])
def fetch_data():
    data = request.json
    # Create a cache key based on the request body
    cache_key = str(data)
    cached_res = cache.get(cache_key)
    if cached_res:
        print("DEBUG: Returning cached data")
        return jsonify(cached_res)

    asset_type = data.get('asset_type')
    symbol = data.get('symbol')
    service_type = data.get('service_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    adjusted = data.get('adjusted', True)
    timeframe = data.get('timeframe', 'daily')
    candle_count = data.get('candle_count')
    codal_category = data.get('codal_category')

    print(f"Fetching: {service_type} for {symbol} (Dates: {start_date} to {end_date}, Adjusted: {adjusted}, Timeframe: {timeframe}, Candles: {candle_count})")

    result = []
    # ... (rest of the logic)
    # At the end of fetch_data, before return:
    # cache.set(cache_key, result_to_return, timeout=600)

    if asset_type == 'indices_market':
        if service_type == 'realtime':
            if symbol == "all":
                # ... (existing logic)
                res1 = client.get_indices(1)
                res2 = client.get_indices(2)
                res3 = client.get_indices(3)
                
                result = []
                if res1:
                    result.append({
                        'l18': "شاخص کل",
                        'l30': "شاخص کل بورس",
                        'pc': res1.get('index'),
                        'pcc': res1.get('index_change'),
                        'pcp': round((res1.get('index_change', 0) / (res1.get('index', 1) - res1.get('index_change', 0))) * 100, 2) if res1.get('index') else 0,
                        'time': res1.get('time')
                    })
                if res2:
                    result.append({
                        'l18': "شاخص کل فرابورس",
                        'l30': "شاخص کل فرابورس",
                        'pc': res2.get('index'),
                        'pcc': res2.get('index_change'),
                        'pcp': round((res2.get('index_change', 0) / (res2.get('index', 1) - res2.get('index_change', 0))) * 100, 2) if res2.get('index') else 0,
                        'time': res2.get('time')
                    })
                if isinstance(res3, list):
                    for match in res3:
                        result.append({
                            'l18': match['name'],
                            'l30': match['name'],
                            'pc': match['index'],
                            'pcc': match['index_change'],
                            'pcp': match['index_change_percent'],
                            'pmin': match['min'],
                            'pmax': match['max'],
                            'time': match['time']
                        })
            elif symbol == "شاخص کل":
                res = client.get_indices(1)
                if res:
                    result = [{
                        'l18': "شاخص کل",
                        'l30': "شاخص کل بورس",
                        'pc': res.get('index'),
                        'pcc': res.get('index_change'),
                        'pcp': round((res.get('index_change', 0) / (res.get('index', 1) - res.get('index_change', 0))) * 100, 2) if res.get('index') else 0,
                        'time': res.get('time')
                    }]
            elif symbol == "شاخص کل فرابورس":
                res = client.get_indices(2)
                if res:
                    result = [{
                        'l18': "شاخص کل فرابورس",
                        'l30': "شاخص کل فرابورس",
                        'pc': res.get('index'),
                        'pcc': res.get('index_change'),
                        'pcp': round((res.get('index_change', 0) / (res.get('index', 1) - res.get('index_change', 0))) * 100, 2) if res.get('index') else 0,
                        'time': res.get('time')
                    }]
            else:
                res = client.get_indices(3)
                if isinstance(res, list):
                    # Find the specific index by name (symbol)
                    match = next((item for item in res if item['name'] == symbol), None)
                    if match:
                        # Format it to look like symbol info for the table
                        result = [{
                            'l18': match['name'],
                            'l30': match['name'],
                            'pc': match['index'],
                            'pcc': match['index_change'],
                            'pcp': match['index_change_percent'],
                            'pmin': match['min'],
                            'pmax': match['max'],
                            'time': match['time']
                        }]
        elif service_type in ['history', 'technical']:
            if symbol == "all":
                return jsonify({"error": "برای تحلیل تکنیکال یا تاریخچه، لطفاً یک شاخص مشخص را انتخاب کنید (نه 'همه موارد')."})
            # For market indices, we use the history API directly with adjusted=False
            result = client.get_price_history(symbol, adjusted=False)
            if isinstance(result, list) and len(result) > 0:
                result = TechnicalAnalyzer.prepare_ohlcv_data(result)
                if service_type == 'technical':
                    if timeframe == 'weekly':
                        result = TechnicalAnalyzer.resample_to_weekly(result)
                    result = TechnicalAnalyzer.calculate_technical_analysis(result)
                elif timeframe == 'weekly':
                    result = TechnicalAnalyzer.resample_to_weekly(result)
            elif isinstance(result, dict) and "error" in result:
                return jsonify(result)
            else:
                result = {"error": "داده‌های تاریخی برای این شاخص یافت نشد."}
    
    elif asset_type == 'indices_industry':
        if service_type == 'realtime':
            # Calculate realtime proxy index by averaging pcp of all symbols in the sector
            d1 = client.get_all_symbols("1")
            d2 = client.get_all_symbols("2")
            data = []
            if isinstance(d1, list): data.extend(d1)
            if isinstance(d2, list): data.extend(d2)
            
            if data:
                if symbol == "all":
                    # Calculate for all sectors
                    sectors = sorted(list(set(s.get('cs') for s in data if s.get('cs'))))
                    result = []
                    for sec in sectors:
                        sector_symbols = [s for s in data if s.get('cs') == sec]
                        if sector_symbols:
                            avg_pcp = sum(float(s.get('pcp', 0)) for s in sector_symbols) / len(sector_symbols)
                            result.append({
                                'l18': sec,
                                'l30': f"شاخص صنعت {sec}",
                                'pc': '-',
                                'pcc': '-',
                                'pcp': round(avg_pcp, 2),
                                'time': datetime.now().strftime("%H:%M:%S"),
                                'count': len(sector_symbols)
                            })
                else:
                    # Calculate for specific sector
                    sector_symbols = [s for s in data if s.get('cs') == symbol]
                    if sector_symbols:
                        avg_pcp = sum(float(s.get('pcp', 0)) for s in sector_symbols) / len(sector_symbols)
                        result = [{
                            'l18': symbol,
                            'l30': f"شاخص صنعت {symbol} (میانگین تغییرات)",
                            'pc': '-',
                            'pcc': '-',
                            'pcp': round(avg_pcp, 2),
                            'time': datetime.now().strftime("%H:%M:%S"),
                            'count': len(sector_symbols)
                        }]
                    else:
                        result = {"error": "نمادی در این صنعت یافت نشد."}
            else:
                result = {"error": "خطا در دریافت داده‌های صنعت."}
        elif service_type in ['history', 'technical']:
            if symbol == "all":
                return jsonify({"error": "برای تحلیل تکنیکال یا تاریخچه صنعت، لطفاً یک صنعت مشخص را انتخاب کنید."})
            # For industry indices, we calculate a proxy index by averaging top symbols in that sector
            # Fetch from both Bourse and Farabourse to get all symbols in the sector
            d1 = client.get_all_symbols("1")
            d2 = client.get_all_symbols("2")
            data = []
            if isinstance(d1, list): data.extend(d1)
            if isinstance(d2, list): data.extend(d2)
            
            if data:
                sector_symbols = [s for s in data if s.get('cs') == symbol]
                if sector_symbols:
                    # Take top 5 symbols by market value (mv) or volume (v) to avoid hitting limits
                    # We use mv (Market Value) if available, otherwise v (Volume)
                    top_symbols = sorted(sector_symbols, key=lambda x: float(x.get('mv') or x.get('v') or 0), reverse=True)[:5]
                    all_histories = []
                    for ts in top_symbols:
                        # Use service="symbols" to bypass the 50% limit for internal industry calculation
                        h = client.get_price_history(ts.get('l18'), adjusted=adjusted, service="symbols")
                        if isinstance(h, list):
                            all_histories.append(pd.DataFrame(h))
                    
                    if all_histories:
                        combined = pd.concat(all_histories)
                        # Average by date
                        if 'date' in combined.columns:
                            combined['date'] = combined['date'].str[:10]
                            # Ensure numeric
                            for col in ['pc', 'pf', 'pmax', 'pmin', 'tvol']:
                                if col in combined.columns:
                                    combined[col] = pd.to_numeric(combined[col], errors='coerce')
                            
                            avg_hist = combined.groupby('date').mean().reset_index()
                            avg_hist = avg_hist.sort_values('date', ascending=False)
                            result = avg_hist.to_dict('records')
                            result = TechnicalAnalyzer.prepare_ohlcv_data(result)
                            
                            # Map for technical analysis if needed
                            if service_type == 'technical':
                                if timeframe == 'weekly':
                                    result = TechnicalAnalyzer.resample_to_weekly(result)
                                result = TechnicalAnalyzer.calculate_technical_analysis(result)
                            elif timeframe == 'weekly':
                                result = TechnicalAnalyzer.resample_to_weekly(result)
                        else:
                            result = {"error": "داده‌های تاریخی برای این صنعت یافت نشد."}
                    else:
                        result = {"error": "خطا در دریافت تاریخچه نمادهای صنعت."}
                else:
                    result = {"error": "نمادی در این صنعت یافت نشد."}
            else:
                result = {"error": "خطا در دریافت لیست نمادها."}

    elif service_type == 'heatmap':
        # Heatmap uses realtime data for all symbols in the selected market
        market_id = "1" if asset_type == 'bourse' else "2" if asset_type == 'fara_bourse' else "1"
        result = client.get_all_symbols(market_id)
    elif service_type == 'realtime':
        res = client.get_symbol_info(symbol)
        if res: result = [res]
    elif service_type == 'history':
        result = client.get_price_history(symbol, adjusted=adjusted)
        if timeframe == 'weekly' and isinstance(result, list):
            result = TechnicalAnalyzer.resample_to_weekly(result)
    elif service_type == 'technical':
        # Technical analysis ALWAYS uses daily history data for all assets
        # For indices, we use adjusted=False, for others we use the user's preference (default True)
        is_index = asset_type.startswith('indices')
        result = client.get_price_history(symbol, adjusted=False if is_index else adjusted)
        
        # Map history format (pc, pf, pmax, pmin, tvol) to standard OHLCV
        if isinstance(result, list) and len(result) > 0:
            result = TechnicalAnalyzer.prepare_ohlcv_data(result)
            
            # Resample to weekly if requested
            if timeframe == 'weekly':
                result = TechnicalAnalyzer.resample_to_weekly(result)
            
            result = TechnicalAnalyzer.calculate_technical_analysis(result)
        elif isinstance(result, dict) and "error" in result:
            return jsonify(result)
        else:
            return jsonify({"error": "داده‌های تاریخی مورد نیاز برای تحلیل تکنیکال یافت نشد."})
    elif service_type == 'client_type':
        result = client.get_price_history(symbol, data_type=1, adjusted=adjusted)
    elif service_type == 'candlestick':
        result = client.get_candlestick(symbol, adjusted=adjusted)
    elif service_type == 'transactions':
        result = client.get_transactions(symbol)
    elif service_type == 'shareholders':
        result = client.get_shareholders(symbol)
    elif service_type == 'nav':
        res = client.get_nav(symbol)
        if res: result = [res]
    elif service_type == 'codal':
        result = client.get_codal_announcements(symbol=symbol, category=codal_category, date_start=start_date, date_end=end_date)
    elif service_type == 'indices':
        result = client.get_indices(asset_type)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result)

    print(f"Raw result count: {len(result) if isinstance(result, list) else 'N/A'}")

    # Filter by date if applicable
    if result and isinstance(result, list) and start_date and end_date:
        # Normalize separators to - for consistent comparison
        start_date = start_date.replace('/', '-')
        end_date = end_date.replace('/', '-')
        
        filtered_result = []
        mismatch_detected = False
        
        for item in result:
            # Check multiple possible date keys
            item_date = item.get('date') or item.get('time') or item.get('date_publish') or item.get('date_send')
            if item_date and len(item_date) >= 10:
                # Normalize item date separator as well
                item_date_norm = item_date[:10].replace('/', '-')
                
                # Check for Jalali (13xx or 14xx) vs Gregorian (20xx) mismatch
                if item_date_norm.startswith(('13', '14')) and start_date.startswith('20'):
                    mismatch_detected = True
                    break
                
                if start_date <= item_date_norm <= end_date:
                    filtered_result.append(item)
            elif item_date: # Just time or short format
                filtered_result.append(item)
        
        if mismatch_detected:
            print("Mismatched date formats detected (Jalali vs Gregorian). Skipping filter.")
            # If mismatch, we return all data instead of empty list
        else:
            result = filtered_result

    # Filter by candle count if requested
    if result and isinstance(result, list) and candle_count:
        try:
            count = int(candle_count)
            # Usually data is sorted descending (latest first) or we sort it
            # Let's ensure it's sorted by date descending for the limit
            date_key = next((k for k in ['date', 'time', 'date_publish'] if k in result[0]), None)
            if date_key:
                result.sort(key=lambda x: x.get(date_key, ''), reverse=True)
            result = result[:count]
        except (ValueError, TypeError):
            pass

    # If technical analysis, generate chart image
    if (service_type == 'technical' or service_type == 'technical_weekly') and isinstance(result, list) and len(result) > 20:
        try:
            chart_buf = TechnicalAnalyzer.generate_chart_image(result, symbol)
            if chart_buf:
                import base64
                img_base64 = base64.b64encode(chart_buf.getvalue()).decode('utf-8')
                result[0]['chart_image'] = img_base64
        except Exception as e:
            print(f"Chart generation error: {e}")

    # Cache the final result for 10 minutes
    cache.set(str(request.json), result if result else [], timeout=600)

    return jsonify(result if result else [])

@app.route('/api/ai_package', methods=['POST'])
def generate_ai_package():
    data = request.json
    symbol = data.get('symbol', 'Unknown')
    tech_data = data.get('data', [])
    weekly_data = data.get('weekly_data', [])
    
    if not tech_data:
        return jsonify({"error": "داده‌ای یافت نشد."})

    # 1. Create Markdown Report
    latest = tech_data[0]
    report = f"# Technical Analysis Executive Report: {symbol}\n"
    report += f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += f"**Current Price:** {latest.get('close'):,.0f} | **Signal:** {latest.get('Signal')} | **Pattern:** {latest.get('Pattern')}\n\n"
    
    report += "## 1. Indicator Prioritization (ML Ranked)\n"
    report += "The following indicators are ranked based on their historical accuracy and success for this specific asset:\n\n"
    if 'recommended_indicators' in latest:
        for idx, ind in enumerate(latest['recommended_indicators'][:4]):
            report += f"{idx+1}. **{ind['name']}** - Accuracy: `{ind['accuracy']}%` | {ind['description']}\n"
    report += "\n"

    report += "## 2. Key Levels (Support & Resistance)\n"
    if 'supports' in latest:
        report += "### Supports:\n"
        for s in latest['supports']:
            report += f"- **{s['value']:,.0f}** (Strength: {s['strength']})\n"
    if 'resistances' in latest:
        report += "\n### Resistances:\n"
        for r in latest['resistances']:
            report += f"- **{r['value']:,.0f}** (Strength: {r['strength']})\n"
    report += "\n"

    report += "## 2. Technical Indicators (Daily)\n"
    report += f"- **RSI (14):** {latest.get('RSI')} ({'Overbought' if (latest.get('RSI') or 0) > 70 else 'Oversold' if (latest.get('RSI') or 0) < 30 else 'Neutral'})\n"
    report += f"- **MACD:** {latest.get('MACD')} (Signal: {latest.get('MACD_Sig')})\n"
    report += f"- **Trend (SMA20/50):** {'Bullish' if (latest.get('SMA20') or 0) > (latest.get('SMA50') or 0) else 'Bearish'}\n"
    report += f"- **ADX (Trend Strength):** {latest.get('ADX')} ({'Strong' if (latest.get('ADX') or 0) > 25 else 'Weak'})\n\n"
    
    if weekly_data:
        w_latest = weekly_data[0]
        report += "## 3. Weekly Multi-Timeframe Analysis\n"
        report += f"- **Weekly Signal:** {w_latest.get('Signal')}\n"
        report += f"- **Weekly RSI:** {w_latest.get('RSI')}\n\n"

    report += "## 4. Historical Data Tables\n"
    report += "### Daily (Last 30 Periods)\n"
    cols = ['date', 'close', 'Signal', 'Pattern', 'RSI', 'MACD', 'SMA20', 'SMA50']
    report += "| " + " | ".join(cols) + " |\n"
    report += "| " + " | ".join(["---"] * len(cols)) + " |\n"
    for d in tech_data[:30]:
        row = [str(d.get(c, '---')) for c in cols]
        report += "| " + " | ".join(row) + " |\n"
    
    if weekly_data:
        report += "\n## Recent Weekly Data (Last 10 Weeks)\n"
        report += "| " + " | ".join(cols) + " |\n"
        report += "| " + " | ".join(["---"] * len(cols)) + " |\n"
        for d in weekly_data[:10]:
            row = [str(d.get(c, '---')) for c in cols]
            report += "| " + " | ".join(row) + " |\n"
    
    # Generate Chart Image for the Package
    import base64
    chart_base64 = None
    df = pd.DataFrame(tech_data)
    if 'date' in df.columns:
        df = df.sort_values('date')
    img_buf = TechnicalAnalyzer.generate_chart_image(df, symbol)
    if img_buf:
        chart_base64 = base64.b64encode(img_buf.getvalue()).decode('utf-8')

    return jsonify({
        "json": {"daily": tech_data, "weekly": weekly_data},
        "markdown": report,
        "chart_image": chart_base64,
        "filename": f"AI_Package_{symbol}"
    })

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    daily_data = data.get('daily_data') or data.get('data')
    weekly_data = data.get('weekly_data')
    format = data.get('format')
    filename = data.get('filename', 'export')
    symbol = data.get('symbol', 'Symbol')

    if format == 'image':
        if not daily_data:
            return "No data for image", 400
        df = pd.DataFrame(daily_data)
        if 'date' in df.columns:
            df = df.sort_values('date') # Needs to be ascending for plotting
        img_buf = TechnicalAnalyzer.generate_chart_image(df, symbol)
        if img_buf:
            return send_file(img_buf, download_name=f"{filename}.png", as_attachment=True, mimetype='image/png')
        return "Error generating image", 500

    if format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # 1. Summary Sheet
            if daily_data:
                latest = daily_data[0]
                summary_data = [
                    ['Symbol', symbol],
                    ['Date', datetime.now().strftime('%Y-%m-%d %H:%M')],
                    ['Current Price', latest.get('close')],
                    ['Primary Signal', latest.get('Signal')],
                    ['Candlestick Pattern', latest.get('Pattern')],
                    ['RSI (14)', latest.get('RSI')],
                    ['MACD', latest.get('MACD')],
                    ['SMA20', latest.get('SMA20')],
                    ['SMA50', latest.get('SMA50')]
                ]
                
                # Add ML Rankings to Summary
                if 'recommended_indicators' in latest:
                    summary_data.append(['---', '---'])
                    summary_data.append(['ML Indicator Rankings', 'Accuracy'])
                    for ind in latest['recommended_indicators'][:4]:
                        summary_data.append([ind['name'], f"{ind['accuracy']}%"])
                    summary_data.append(['---', '---'])

                # Add S/R if they exist
                if 'supports' in latest:
                    for i, s in enumerate(latest['supports']):
                        summary_data.append([f'Support {i+1}', s['value']])
                if 'resistances' in latest:
                    for i, r in enumerate(latest['resistances']):
                        summary_data.append([f'Resistance {i+1}', r['value']])
                
                df_summary = pd.DataFrame(summary_data, columns=['Factor', 'Value'])
                df_summary.to_excel(writer, index=False, sheet_name='Executive_Summary')
            
            if daily_data:
                df_daily = pd.DataFrame(daily_data)
                # Sort by date if column exists
                for col in ['date', 'time', 'date_publish']:
                    if col in df_daily.columns:
                        df_daily = df_daily.sort_values(col)
                        break
                # Remove S/R lists from the main data sheet for cleanliness
                cols_to_drop = [c for c in ['supports', 'resistances'] if c in df_daily.columns]
                df_daily.drop(columns=cols_to_drop, inplace=True, errors='ignore')
                df_daily.to_excel(writer, index=False, sheet_name='Daily_Technical')
                
                # Apply Formatting
                workbook  = writer.book
                worksheet = writer.sheets['Daily_Technical']
                
                # Formats
                green_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
                red_format   = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                
                # Find Signal and RSI column indices
                cols = df_daily.columns.tolist()
                if 'Signal' in cols:
                    sig_idx = cols.index('Signal')
                    worksheet.conditional_format(1, sig_idx, len(df_daily), sig_idx,
                                                {'type': 'text', 'criteria': 'containing', 'value': 'Bullish', 'format': green_format})
                    worksheet.conditional_format(1, sig_idx, len(df_daily), sig_idx,
                                                {'type': 'text', 'criteria': 'containing', 'value': 'Bearish', 'format': red_format})

                if 'RSI' in cols:
                    rsi_idx = cols.index('RSI')
                    worksheet.conditional_format(1, rsi_idx, len(df_daily), rsi_idx,
                                                {'type': 'cell', 'criteria': '<', 'value': 30, 'format': green_format})
                    worksheet.conditional_format(1, rsi_idx, len(df_daily), rsi_idx,
                                                {'type': 'cell', 'criteria': '>', 'value': 70, 'format': red_format})

            if weekly_data:
                df_weekly = pd.DataFrame(weekly_data)
                # Sort by date if column exists
                for col in ['date', 'time', 'date_publish']:
                    if col in df_weekly.columns:
                        df_weekly = df_weekly.sort_values(col)
                        break
                df_weekly.to_excel(writer, index=False, sheet_name='Weekly_Technical')
                
                # Apply same formatting to Weekly
                workbook  = writer.book
                worksheet = writer.sheets['Weekly_Technical']
                cols = df_weekly.columns.tolist()
                if 'Signal' in cols:
                    sig_idx = cols.index('Signal')
                    worksheet.conditional_format(1, sig_idx, len(df_weekly), sig_idx,
                                                {'type': 'text', 'criteria': 'containing', 'value': 'Bullish', 'format': green_format})
                    worksheet.conditional_format(1, sig_idx, len(df_weekly), sig_idx,
                                                {'type': 'text', 'criteria': 'containing', 'value': 'Bearish', 'format': red_format})
            
            # Formatting for Executive Summary
            if 'Executive_Summary' in writer.sheets:
                ws_sum = writer.sheets['Executive_Summary']
                ws_sum.conditional_format('B4:B4', {'type': 'text', 'criteria': 'containing', 'value': 'Bullish', 'format': green_format})
                ws_sum.conditional_format('B4:B4', {'type': 'text', 'criteria': 'containing', 'value': 'Bearish', 'format': red_format})
                ws_sum.set_column('A:B', 30)
                
        output.seek(0)
        return send_file(output, download_name=f"{filename}.xlsx", as_attachment=True)
    
    elif format == 'csv':
        if weekly_data and daily_data:
            # Return a ZIP with both CSVs
            import zipfile
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w') as zf:
                df_daily = pd.DataFrame(daily_data)
                for col in ['date', 'time', 'date_publish']:
                    if col in df_daily.columns:
                        df_daily = df_daily.sort_values(col)
                        break
                zf.writestr(f"{filename}_Daily.csv", df_daily.to_csv(index=False, encoding='utf-8-sig'))
                
                df_weekly = pd.DataFrame(weekly_data)
                for col in ['date', 'time', 'date_publish']:
                    if col in df_weekly.columns:
                        df_weekly = df_weekly.sort_values(col)
                        break
                zf.writestr(f"{filename}_Weekly.csv", df_weekly.to_csv(index=False, encoding='utf-8-sig'))
            output.seek(0)
            return send_file(output, download_name=f"{filename}.zip", as_attachment=True)
        else:
            df = pd.DataFrame(daily_data or weekly_data)
            for col in ['date', 'time', 'date_publish']:
                if col in df.columns:
                    df = df.sort_values(col)
                    break
            output = io.BytesIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)
            return send_file(output, download_name=f"{filename}.csv", as_attachment=True)

    return "Invalid format", 400

@app.route('/api/market_status')
def get_market_status():
    global_stats = {"total": 0, "success": 0, "blocked": 0}
    for s in stats["services"].values():
        global_stats["total"] += s["total"]
        global_stats["success"] += s["success"]
        global_stats["blocked"] += s["blocked"]
        
    return jsonify({
        'status': 'در حال فعالیت', 
        'time': datetime.now().strftime('%H:%M:%S'),
        'stats': {
            'global': global_stats,
            'services': stats
        }
    })

if __name__ == '__main__':
    print("Starting Flask server on http://0.0.0.0:5000 ...")
    app.run(debug=True, host='0.0.0.0', port=5000)
