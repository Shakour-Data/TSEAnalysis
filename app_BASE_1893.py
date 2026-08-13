import os
import json
import shutil
import subprocess
import ssl
import socket
import time
from urllib.parse import urlencode
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file
import requests
import requests.utils
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== FIREWALL NUCLEAR OPTION =====
# To prevent NO 10054 errors, we globally disable the "python-requests" User-Agent
# This ensures that even 3rd party libraries or accidental calls are masked as a browser.
SAFE_BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
requests.utils.default_user_agent = lambda: SAFE_BROWSER_UA

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
import threading
from flask_caching import Cache
from technical_analysis import TechnicalAnalyzer
from database import db

app = Flask(__name__)

# Configure Caching with memory limits
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_THRESHOLD': 500  # Limit the number of items in memory
})

API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"
BASE_URL = "https://brsapi.ir"

# Set YOUR_PROXY if you are on a foreign server (OVH, etc.)
# Examples: "http://user:pass@host:port" or "socks5://host:port"
# If you have a local v2ray/xray running on 1080: "socks5://127.0.0.1:1080"
PROXY_URL = None # DEFAULT: NO PROXY

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
    
    # Chrome 131 Browser Headers (COMPLIANT with BrsApi 6G Firewall Rules)
    CHROME_HEADERS = {
        "User-Agent": SAFE_BROWSER_UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://brsapi.ir/",
        "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
    }
    
    # BrsApi Fair Use Constants (STRICT MODE ENABLED)
    MAX_REQS_STRICT = 200  # Conservative limit (Official is 300)
    WINDOW_SECONDS = 300  # 5 minutes window
    MIN_REQUEST_GAP = 2.5 # High-safety gap between any network calls
    
    def __init__(self, api_key, proxy=None):
        self.api_key = api_key
        self.base_url = BASE_URL
        self.proxy = proxy
        self.active_client = None
        self.client_name = "none"
        self._request_history = [] # Timestamps of successful network requests
        self._last_network_call = 0
        self._network_lock = threading.Lock() # ENSURE ABSOLUTE SEQUENTIAL ACCESS
        self._consecutive_failures = 0
        self._cooling_until = 0
        
        # Rule Check: Proxy usage in free versions
        if self.proxy:
            print("⚠️ WARNING: BrsApi rules prohibit usage of proxies/CORS proxies for FREE accounts.")
            print("   Ensure your API Key supports proxy usage or disable PROXY_URL if you face a 10054 Connection Reset.")

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
                # We rotate fingerprints if one fails, starting with chrome_120
                self.active_client = tls_client.Session(
                    client_identifier="chrome_120",
                    random_tls_extension_order=True
                )
                if self.proxy:
                    self.active_client.proxies = {"http": self.proxy, "https": self.proxy}
                self.client_name = "tls_client (JA3 Spoofing)"
                print(f"DEBUG: Using {self.client_name}")
                return
            except Exception as e:
                print(f"DEBUG: tls_client init failed: {e}")
        
        # Priority 2: curl_cffi
        if CURL_CFFI_AVAILABLE:
            try:
                self.active_client = crequests.Session()
                self.active_client.headers.update(self.CHROME_HEADERS)
                if self.proxy:
                    self.active_client.proxies = {"http": self.proxy, "https": self.proxy}
                self.client_name = "curl_cffi (Chrome impersonate)"
                print(f"DEBUG: Using {self.client_name}")
                return
            except Exception as e:
                print(f"DEBUG: curl_cffi init failed: {e}")
        
        # Fallback will be handled per-request for httpx and others
        self.client_name = "per-request clients"
        print(f"DEBUG: Using {self.client_name}")

    def _clear_cache_on_startup(self):
        self._symbols_cache = {}
        print("DEBUG: Symbol cache cleared on startup")

    def _fetch_symbols_by_type(self, type_code, force_refresh=False):
        """Fetch symbols with absolute priority on stability and local cache."""
        db_category = f"api_type_{type_code}"
        
        # 1. Check if we already have data in DB (Registry)
        stored_data = []
        try:
            stored_data = db.get_symbols_by_market(db_category)
        except Exception as e:
            print(f"DEBUG: DB Error: {e}")

        # If not forcing refresh and we have data, return immediately (Speed + Safety)
        if not force_refresh and stored_data:
            return stored_data

        # 2. API Call (With multiple retries and jitter)
        data = self._make_request("Api/Tsetmc/AllSymbols.php", {"type": str(type_code)}, service="symbols")
        
        if isinstance(data, list) and len(data) > 10: # Sanity check: Type 1/2 usually have hundreds
            # Success: Update Database Registry. NO CLEAR needed, save_symbols uses REPLACE.
            try:
                db.save_symbols(data, db_category)
                return data
            except Exception as e:
                print(f"DEBUG: Save to DB failed: {e}")
                return data # Still return API data even if DB save fails
            
        # 3. Handle API Failure
        if stored_data:
            print(f"DEBUG: API returned error/empty for Type {type_code}. Returning cached DB data.")
            return stored_data
            
        # 4. Total Failure (No DB, No API)
        if isinstance(data, dict) and "error" in data:
            return data
        return {"error": "دیتابیس محلی خالی است و ارتباط با سرور نیز برقرار نشد. لطفاً دکمه همگام‌سازی را بزنید."}

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
        """Categorizes symbols into markets with robust fallback logic and partial matches."""
        # Normalize all inputs
        cs_id = str(symbol.get("cs_id") or symbol.get("csId") or symbol.get("sectorId") or "").strip()
        cs_name = self._normalize_text(symbol.get("cs", "") or symbol.get("sectorName") or "")
        
        # Robust market name extraction
        market_name = str(symbol.get("market_name") or symbol.get("market") or symbol.get("flowTitle") or symbol.get("marketName") or "").lower()
        market_name = self._normalize_text(market_name).lower()
        
        ticker = str(symbol.get("l18") or symbol.get("symbol") or "")
        
        # Robust flow extraction
        flow = str(symbol.get("flow") or symbol.get("flow_id") or symbol.get("flowId") or "").strip()
        
        isin = str(symbol.get("isin") or "").upper().strip()

        # 0. Bourse Kala (Commodity Exchange) - Check this FIRST to avoid confusion
        if any(k in market_name for k in ["کالا", "kala", "گواهی", "سپرده", "آتی", "futures"]) or \
           any(k in cs_name for k in ["بورس کالا", "مشتقه", "کالایی"]) or \
           any(k in ticker for k in ["سکه", "طلا", "زعف", "نفت", "برنج", "پسته", "میوه", "شمش"]):
            return "kala"

        if "انرژی" in market_name or "energy" in market_name:
            return "energy"

        # 1. ETFs and Funds (Critical check)
        if cs_id == "68" or isin.startswith("IRO5") or "etf" in cs_name.lower() or "صندوق" in cs_name:
            return "etf"
        
        # 2. Fixed Income / Bonds
        if cs_id == "69" or isin.startswith(("IRO2", "IRO4", "IROB")) or any(k in cs_name for k in ["اوراق", "صکوک", "اجاره", "مرابحه", "منفعت", "گام"]):
            return "fixed_income"
            
        # 3. Housing Facilities (Tashilat)
        if cs_id == "59" or isin.startswith("IROL") or any(k in cs_name for k in ["تسهیلات", "مسکن"]) or ticker.startswith("تسه"):
            return "tashilat"

        # 4. Payeh (Base Market)
        if flow in ["5", "6", "7", "8"] or any(k in market_name for k in ["پایه", "payeh", "زرد", "نارنجی", "قرمز"]):
            return "base"
        if isin.startswith("IRO7"):
            return "base"

        # 5. Farabourse
        if flow in ["3", "4"] or any(k in market_name for k in ["فرابورس", "farabourse", "ifb", "پذیرفته", "پذيرفته"]):
            return "farabourse"
        if isin.startswith("IRO3"):
            return "farabourse"

        # 6. Bourse Tehran
        if flow in ["1", "2"] or any(k in market_name for k in ["بورس", "bourse", "tse"]):
            return "bourse"
        if isin.startswith("IRO1"):
            return "bourse"

        # Default catch-all
        return "bourse"

    def _get_equity_universe(self, api_type="1", force_refresh=False):
        """Unified fetch for symbol universes (Type 1 or 2)."""
        cache_key = f"symbols_universe_type_{api_type}"
        now = datetime.now()
        
        if not force_refresh:
            cached = self._symbols_cache.get(cache_key)
            if cached:
                data, timestamp = cached
                if (now - timestamp).total_seconds() < 21600: # 6 hours
                    return data

        data = self._fetch_symbols_by_type(api_type, force_refresh=force_refresh)
        if isinstance(data, list):
            self._symbols_cache[cache_key] = (data, now)
        return data

    def _filter_symbols(self, universe, categories):
        """Filters a list of symbols by allowed categories."""
        if not isinstance(universe, list):
            return []

        allowed = set(categories)
        filtered = [sym for sym in universe if self._classify_equity_market(sym) in allowed]
        return filtered

    def _filter_equities_by_category(self, categories, force_refresh=False):
        equities = self._get_equity_universe(force_refresh=force_refresh)
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

    def _apply_fair_use_control(self, endpoint):
        """
        Enforces BrsApi Fair Use Policy and Anti-NGFW Timing.
        Absolute sequential execution via locking.
        """
        now = time.time()
        
        # 0. Circuit Breaker: If we are in a cooling period, block immediately
        if now < self._cooling_until:
            wait_time = self._cooling_until - now
            print(f"⚠️ COOLING DOWN: Suspicious activity detected. Waiting {wait_time:.1f}s until cooldown ends...")
            time.sleep(wait_time)
            now = time.time()

        # 1. Human-Like Behavior: Random "Think Time" (0.5s - 1.5s)
        # This breaks the "robotic" exact-interval pattern.
        think_time = random.uniform(0.5, 1.5)
        time.sleep(think_time)
        now = time.time()

        # 2. Mandatory gap between requests (Very Strict: 2.5s)
        elapsed_since_last = now - self._last_network_call
        if elapsed_since_last < self.MIN_REQUEST_GAP:
            sleep_time = self.MIN_REQUEST_GAP - elapsed_since_last
            time.sleep(sleep_time)
            now = time.time() 
            
        # 3. 5-Minute window rate limiting (STRICT 200/5min)
        self._request_history = [t for t in self._request_history if (now - t) < self.WINDOW_SECONDS]
        
        if len(self._request_history) >= self.MAX_REQS_STRICT:
            wait_needed = self.WINDOW_SECONDS - (now - self._request_history[0])
            print(f"⚠️ RATE LIMIT: Safe window reached. Professional Pause for {int(wait_needed)}s...")
            time.sleep(wait_needed + 2)
            now = time.time()
            self._request_history = [t for t in self._request_history if (now - t) < self.WINDOW_SECONDS]
            
        self._last_network_call = now
        self._request_history.append(now)

    def _make_request(self, endpoint, params=None, service=None):
        """
        Professional Resilient Request Handler.
        Uses Thread-Locking for absolute sequential safety.
        """
        with self._network_lock: # ABSOLUTE SEQUENTIAL ACCESS
            return self._locked_make_request(endpoint, params, service)

    def _locked_make_request(self, endpoint, params=None, service=None):
        self._apply_fair_use_control(endpoint)

        query = params.copy() if params else {}
        query["key"] = self.api_key
        
        # We will try both HTTPS and HTTP for absolute resilience
        protocols = ["https", "http"]
        
        # Rotational identifiers
        idents = ["chrome_120", "firefox_117", "chrome_110", "safari_15_6_1", "chrome_131"]
        
        is_discovery = (service == "symbols" or "AllSymbols" in endpoint)
        current_max = 3 if is_discovery else 5
        
        for protocol in protocols:
            url = f"{protocol}://brsapi.ir/{endpoint}"
            full_url = f"{url}?{urlencode(query, doseq=True)}"

            for attempt in range(current_max):
                tech_variant = attempt % 3 # 0: Curl, 1: TLS/CFFI, 2: Requests

                if attempt > 0:
                    wait = (attempt * (3 if is_discovery else 10)) + random.uniform(1, 3)
                    print(f"DEBUG: Retrying {service or 'request'} via {protocol.upper()} (Attempt {attempt}, Tech {tech_variant})...")
                    time.sleep(wait)

                # --- Technique A: Native Curl ---
                if tech_variant == 0 and self.curl_path:
                    try:
                        is_safe_mode = (attempt > 0) or (protocol == "http")
                        data = self._curl_fallback_request(url, query, force_http11=is_safe_mode)
                        if data and isinstance(data, (list, dict)) and "error" not in str(data)[:50]:
                            self._consecutive_failures = 0
                            if service: update_stats(service, "success")
                            return data
                    except Exception as e:
                        print(f"DEBUG: Curl {protocol} failed: {str(e)[:40]}")

                # --- Technique B: curl_cffi or tls_client ---
                if tech_variant == 1:
                    if CURL_CFFI_AVAILABLE:
                        try:
                            # impersonate only works for https, but cffi handles http fine
                            if protocol == "https":
                                resp = crequests.get(full_url, impersonate="chrome120", timeout=30, verify=False)
                            else:
                                resp = crequests.get(full_url, timeout=30)
                                
                            if resp.status_code == 200:
                                self._consecutive_failures = 0
                                if service: update_stats(service, "success")
                                return resp.json()
                        except Exception as e:
                            print(f"DEBUG: CFFI {protocol} failed: {str(e)[:40]}")
                    
                    if TLS_CLIENT_AVAILABLE and protocol == "https":
                        try:
                            selected_id = random.choice(idents)
                            sess = tls_client.Session(client_identifier=selected_id, random_tls_extension_order=True)
                            if self.proxy: sess.proxies = {"http": self.proxy, "https": self.proxy}
                            response = sess.get(full_url, headers=self.CHROME_HEADERS, timeout_seconds=45)
                            if response.status_code == 200:
                                self._consecutive_failures = 0
                                if service: update_stats(service, "success")
                                return response.json()
                        except Exception: pass

                # --- Technique C: Final Requests Fallback ---
                if tech_variant == 2 or attempt == current_max - 1:
                    try:
                        resp = requests.get(full_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, verify=False)
                        if resp.status_code == 200:
                            self._consecutive_failures = 0
                            if service: update_stats(service, "success")
                            return resp.json()
                    except Exception as e:
                        print(f"DEBUG: Final {protocol} Fallback failed: {str(e)[:40]}")

        # If we reach here, all attempts failed
        if service: update_stats(service, "blocked")
        
        # CIRCUIT BREAKER
        if not is_discovery:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 3:
                cooldown_period = 60
                self._cooling_until = time.time() + cooldown_period
                print(f"🚨 CRITICAL: Persistent Connection Resets. IP might be throttled. CIRCUIT BREAKER ACTIVE.")
                self._consecutive_failures = 0 
        else:
            print("🚨 DEBUG: Connectivity lost. Your server (OVH France) is likely blocked by the Iranian firewall.")

        return {
            "error": "ارتباط با سرور بورس با خطا مواجه شد. سرور شما (خارج از کشور) توسط فایروال مسدود شده است.",
            "blocked": True,
            "technical_info": "ConnectionReset/SSL-Code-35. Recommending Proxy Iran or Local hosting."
        }


    def _curl_fallback_request(self, url, params, force_http11=False):
        """Native curl.exe fallback with full browser impersonation."""
        if not self.curl_path:
            return None

        try:
            encoded = urlencode(params or {}, doseq=True)
            full_url = f"{url}?{encoded}" if encoded else url
            
            # Simple Headers (Less is more when bypassing DPI)
            header_args = [
                "-H", f"User-Agent: {SAFE_BROWSER_UA}",
                "-H", "Accept: */*",
                "-H", "Connection: close",
            ]

            cmd = [
                self.curl_path,
                "-sS",
                "-L",
                "-k",
                "--max-time", "25",
                "--retry", "0",
            ]
            
            # Rotation of HTTP versions and compression
            if force_http11:
                cmd.append("--http1.1")
            
            # Add proxy
            if hasattr(self, 'proxy') and self.proxy:
                if "socks5" in self.proxy:
                    cmd += ["--socks5-hostname", self.proxy.split("//")[-1]]
                else:
                    cmd += ["-x", self.proxy]
                    
            cmd = cmd + header_args + [full_url]

            # Try 1: Standard
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            
            # Try 2: If Code 35 (SSL Error), try with specific ciphers and TLS 1.2
            if result.returncode == 35 or not result.stdout:
                print("DEBUG: Curl Code 35 detected. Retrying with Compatibility Mode...")
                compat_cmd = cmd + ["--tlsv1.2", "--ciphers", "DEFAULT@SECLEVEL=1"]
                result = subprocess.run(compat_cmd, capture_output=True, text=True, timeout=35)

            body = result.stdout.strip().lstrip('\ufeff')
            if not body or not (body.startswith('[') or body.startswith('{')):
                # Try 3: Absolute Desperation - No headers at all
                if result.returncode != 0:
                    minimal_cmd = [self.curl_path, "-sS", "-k", "--max-time", "15", full_url]
                    result = subprocess.run(minimal_cmd, capture_output=True, text=True, timeout=20)
                    body = result.stdout.strip().lstrip('\ufeff')

            if body and (body.startswith('[') or body.startswith('{')):
                return json.loads(body)
            return None
        except Exception as exc:
            print(f"DEBUG: curl exception: {exc}")
            return None
        except Exception as exc:
            print(f"DEBUG: curl exception: {exc}")
            return None

    def get_all_symbols(self, market_type, force_refresh=False):
        """Return enriched symbol lists for each market selection with heavy caching."""
        cache_key = f"symbols_{market_type}"
        now = datetime.now()
        
        # INCREASE CACHE: Symbols change very rarely. 6 hours (21600s)
        if not force_refresh:
            cached = self._symbols_cache.get(cache_key)
            if cached:
                data, timestamp = cached
                if (now - timestamp).total_seconds() < 21600:
                    return data

        result_symbols = []

        # BrsApi Mapping:
        # 1: Bourse Tehran
        # 2: Farabourse (Usually includes Payeh)
        # 3: Kala/Ati
        # 4: Bonds
        # 5: Tashilat
        
        if market_type == "1":  # Bourse Tehran
            u1 = self._get_equity_universe("1", force_refresh=force_refresh)
            u2 = self._get_equity_universe("2", force_refresh=force_refresh)
            
            # Combine both (safety first)
            combined = []
            if isinstance(u1, list): combined.extend(u1)
            if isinstance(u2, list): combined.extend(u2)
            
            if not combined and isinstance(u1, dict) and "error" in u1:
                return u1 # Return the actual API error if nothing was found

            result_symbols = self._filter_symbols(combined, ["bourse"])
            
            if not result_symbols and isinstance(u1, list) and len(u1) > 10:
                # Fallback: take from u1 if it's not another known class
                result_symbols = [s for s in u1 if self._classify_equity_market(s) not in ["etf", "fixed_income", "kala"]]

        elif market_type == "2":  # FaraBourse
            u2 = self._get_equity_universe("2", force_refresh=force_refresh)
            u1 = self._get_equity_universe("1", force_refresh=force_refresh)
            
            combined = []
            if isinstance(u2, list): combined.extend(u2)
            if isinstance(u1, list): combined.extend(u1)
            
            if not combined and isinstance(u2, dict) and "error" in u2:
                 return u2 # Return the actual API error (Reset, etc.)

            result_symbols = self._filter_symbols(combined, ["farabourse"])
            
            if not result_symbols and isinstance(u2, list) and len(u2) > 0:
                # Lenient fallback for IFB
                result_symbols = [s for s in u2 if self._classify_equity_market(s) not in ["bourse", "base", "etf", "fixed_income", "kala", "tashilat"]]

        elif market_type == "4":  # Base Market (Payeh)
            u2 = self._get_equity_universe("2", force_refresh=force_refresh)
            u1 = self._get_equity_universe("1", force_refresh=force_refresh)
            u3 = self._get_equity_universe("3", force_refresh=force_refresh)
            
            combined = []
            for u in [u1, u2, u3]:
                if isinstance(u, list): combined.extend(u)
            
            result_symbols = self._filter_symbols(combined, ["base"])

        elif market_type == "3":  # Kala/Ati
            u2 = self._get_equity_universe("2", force_refresh=force_refresh)
            u3 = self._get_equity_universe("3", force_refresh=force_refresh)
            
            combined = []
            for u in [u2, u3]:
                if isinstance(u, list): combined.extend(u)
            
            result_symbols = self._filter_symbols(combined, ["kala"])

        elif market_type == "5":  # ETF Funds
            u1 = self._get_equity_universe("1", force_refresh=force_refresh)
            u2 = self._get_equity_universe("2", force_refresh=force_refresh)
            f1 = self._filter_symbols(u1, ["etf"])
            f2 = self._filter_symbols(u2, ["etf"])
            
            merged_dict = {}
            for s in (f1 + f2):
                key = s.get('isin') or s.get('l18')
                if key: merged_dict[key] = s
            result_symbols = list(merged_dict.values())

        elif market_type == "fixed_income":
            # API Type 4 is specifically for Bonds
            result_symbols = self._fetch_symbols_by_type("4", force_refresh=force_refresh)

        elif market_type == "tashilat":
            # API Type 5 is specifically for Housing
            result_symbols = self._fetch_symbols_by_type("5", force_refresh=force_refresh)

        elif market_type == "indices_market":
            lists = []
            errors = []
            # Note: Index.php type 1/2 returns a single dict, type 3 returns a list.
            # We fetch 1 and 2 for major indices, then 3 for the rest
            for idx_type, prefix in (("1", "بورس"), ("2", "فرابورس"), ("3", "سایر")):
                data = self.get_indices(idx_type, force_refresh=force_refresh)
                
                if isinstance(data, list):
                    for i, item in enumerate(data):
                        name = item.get('l18') or item.get('name') or "نامشخص"
                        lists.append({
                            "id": f"idx_{idx_type}_{i}", 
                            "l18": name, 
                            "l30": item.get('l30') or f"شاخص {prefix} {name}"
                        })
                elif isinstance(data, dict) and "error" not in data:
                    name = data.get('l18') or data.get('name') or (f"شاخص کل {prefix}")
                    lists.append({
                        "id": f"idx_{idx_type}_main", 
                        "l18": name, 
                        "l30": data.get('l30') or f"شاخص {prefix} {name}"
                    })
                elif isinstance(data, dict):
                    errors.append(data)
            
            if lists:
                result_symbols = lists
            else:
                result_symbols = errors[0] if errors else {"error": "دریافت شاخص‌ها با خطا مواجه شد."}

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

        # Diagnostic info
        diag = ""
        u2_data = locals().get('u2')
        if market_type == "2" and isinstance(u2_data, list):
            diag = f" (تعداد کل نمادهای خام دریافتی: {len(u2_data)})"
        elif market_type == "1":
            u1_data = locals().get('u1')
            if isinstance(u1_data, list):
                diag = f" (تعداد کل نمادهای خام دریافتی: {len(u1_data)})"

        return {"error": f"داده‌ای با معیارهای انتخاب شده یافت نشد.{diag}"}

    def get_symbol_info(self, symbol):
        return self._make_request("Api/Tsetmc/Symbol.php", {"l18": symbol}, service="realtime")

    def get_price_history(self, symbol, data_type=0, adjusted=True, service=None, force_refresh=False):
        """
        User-Commanded History Fetcher (STRICTLY FORCES ADJUSTED DATA FOR DB STORAGE).
        1. Checks DB first.
        2. If force_refresh OR DB Empty, fetches from API (Forces adjusted=True).
        3. Saves NEW records to DB.
        4. Returns data ONLY from DB to ensure technical analysis uses adjusted cached records.
        """
        # We always use the same key because we only store adjusted data
        db_key = f"{symbol}_{data_type}"
        
        # Check SQLite storage
        cached_data = db.get_history(db_key)
        
        should_fetch = force_refresh or not cached_data
        
        if should_fetch:
            print(f"DEBUG: Command received - Fetching fresh ADJUSTED history for {symbol}")
            api_data = self._make_request("Api/Tsetmc/History.php", {
                "l18": symbol,
                "type": data_type,
                "adjusted": "true"  # <--- FORCE TRUE: We only store adjusted data
            }, service=service)
            
            if isinstance(api_data, list) and api_data:
                # Save to DB (INSERT OR IGNORE handles new data only)
                db.save_history(db_key, api_data)
                # Always re-read from DB to be the single source of truth
                cached_data = db.get_history(db_key)
            elif isinstance(api_data, dict) and "error" in api_data and not cached_data:
                return api_data
        
        if cached_data:
            return cached_data
            
        return {"error": f"تاریخچه قیمتی برای {symbol} یافت نشد."}

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

    def get_indices(self, index_type, force_refresh=False):
        """Fetch index data with persistent storage fallback."""
        db_category = f"indices_type_{index_type}"
        data = self._make_request("Api/Tsetmc/Index.php", {"type": index_type})
        
        is_error = isinstance(data, dict) and "error" in data
        
        if not is_error and data:
            # Success: Save to Registry
            try:
                # Wrap dict in list for DB compatibility if needed
                save_list = [data] if isinstance(data, dict) else data
                db.clear_symbols(db_category)
                db.save_symbols(save_list, db_category)
            except Exception as e:
                print(f"DEBUG: Index save error: {e}")
            return data
            
        # Failure Case: Check persistent storage
        try:
            stored = db.get_symbols_by_market(db_category)
            if stored:
                print(f"DEBUG: API Failed for Index Type {index_type}. Falling back to DB.")
                # Return dict if it was originally a dict type (1 or 2)
                if index_type in ["1", "2"] or str(index_type) in ["1", "2"]:
                    return stored[0]
                return stored
        except Exception as e:
            print(f"DEBUG: Index DB retrieval error: {e}")
            
        return data

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

client = TSETMCClient(API_KEY, PROXY_URL)

def background_preload():
    """Fills the database registry in the background with long safety gaps."""
    # Only run if registry seems empty to avoid redundant calls
    if hasattr(db, 'get_total_symbols_count') and db.get_total_symbols_count() < 100:
        print("🚀 STARTUP: Registry empty. Initiating silent background pre-warm...")
        for t in ["1", "2"]:
            try:
                client.get_all_symbols(t)
                time.sleep(random.uniform(15, 25)) # Safety gap
            except: pass
    else:
        print("✅ STARTUP: Registry already populated and ready.")

# Start preload in a separate thread to not block Flask startup
# WERKZEUG_RUN_MAIN check prevents double execution in debug mode
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    threading.Thread(target=background_preload, daemon=True).start()

@app.route('/api/health')
def health_check():
    """Diagnostic endpoint to check connectivity status."""
    test_res = client._make_request("Api/Tsetmc/Index.php", {"type": "1"})
    status = "OK" if "error" not in test_res else "FAILED"
    return jsonify({
        "status": status,
        "proxy": PROXY_URL,
        "active_client": client.client_name,
        "test_response": str(test_res)[:200]
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api_test')
def api_test():
    return render_template('api_test.html')

@app.route('/api/symbols/<market_type>')
def get_symbols(market_type):
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    print(f"DEBUG: Received request for symbols of type: {market_type} (Refresh: {refresh})")
    symbols = client.get_all_symbols(market_type, force_refresh=refresh)
    if isinstance(symbols, dict) and "error" in symbols:
        return jsonify(symbols)
    return jsonify(symbols if symbols else [])

@app.route('/api/sync_registry', methods=['POST'])
def sync_registry():
    """Manual trigger for persistent registry update using ULTRA-STRICT protocol."""
    results = {}
    print("DEBUG: GLOBAL SYNC REQUESTED. Executing under ULTRA-STRICT protocol (Long Gaps)...")
    
    # Process types 1 through 5 with high-safety delays
    for t in range(1, 6):
        try:
            data = client._fetch_symbols_by_type(str(t), force_refresh=True)
            if isinstance(data, list):
                results[f"type_{t}"] = f"Success ({len(data)} symbols)"
            else:
                results[f"type_{t}"] = "Failed/Empty"
            
            # MANDATORY: 20-35 second gap between ANY discovery call to stay invisible to DPI
            if t < 5:
                sleep_time = random.uniform(20.0, 35.0)
                print(f"DEBUG: Type {t} discovery complete. Cooling down for {sleep_time:.1f}s...")
                time.sleep(sleep_time)
        except Exception as e:
            results[f"type_{t}"] = f"Protocol Error: {str(e)}"

    return jsonify({
        "status": "Complete (Ultra-Strict Protocol)",
        "details": results,
        "registry_count": db.get_total_symbols_count() if hasattr(db, 'get_total_symbols_count') else "OK"
    })

@app.route('/api/fetch_data', methods=['POST'])
def fetch_data():
    data = request.json
    force_refresh = data.get('refresh', False)
    
    # Create a cache key based on the request body
    cache_key = str(data)
    if not force_refresh:
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
                # Use individual helpers with refresh flag
                res1 = client.get_indices(1, force_refresh=force_refresh)
                res2 = client.get_indices(2, force_refresh=force_refresh)
                res3 = client.get_indices(3, force_refresh=force_refresh)
                
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
                res = client.get_indices(1, force_refresh=force_refresh)
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
                res = client.get_indices(2, force_refresh=force_refresh)
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
                res = client.get_indices(3, force_refresh=force_refresh)
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
            result = client.get_price_history(symbol, adjusted=False, force_refresh=force_refresh)
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
            # Use force_refresh for getting symbols if requested
            d1 = client.get_all_symbols("1", force_refresh=force_refresh)
            d2 = client.get_all_symbols("2", force_refresh=force_refresh)
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
            d1 = client.get_all_symbols("1", force_refresh=force_refresh)
            d2 = client.get_all_symbols("2", force_refresh=force_refresh)
            data = []
            if isinstance(d1, list): data.extend(d1)
            if isinstance(d2, list): data.extend(d2)
            
            if data:
                sector_symbols = [s for s in data if s.get('cs') == symbol]
                if sector_symbols:
                    # Take top 5 symbols by market value (mv) or volume (v) to avoid hitting limits
                    top_symbols = sorted(sector_symbols, key=lambda x: float(x.get('mv') or x.get('v') or 0), reverse=True)[:5]
                    all_histories = []
                    for ts in top_symbols:
                        # For industry components, we use user's refresh flag
                        h = client.get_price_history(ts.get('l18'), adjusted=adjusted, service="symbols", force_refresh=force_refresh)
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
        result = client.get_all_symbols(market_id, force_refresh=force_refresh)
    elif service_type == 'realtime':
        res = client.get_symbol_info(symbol)
        if res: result = [res]
    elif service_type == 'history':
        result = client.get_price_history(symbol, adjusted=adjusted, force_refresh=force_refresh)
        if timeframe == 'weekly' and isinstance(result, list):
            result = TechnicalAnalyzer.resample_to_weekly(result)
    elif service_type == 'technical':
        # Technical analysis ALWAYS uses daily history data for all assets
        # For indices, we use adjusted=False, for others we use the user's preference (default True)
        is_index = asset_type.startswith('indices')
        result = client.get_price_history(symbol, adjusted=False if is_index else adjusted, force_refresh=force_refresh)
        
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
        result = client.get_price_history(symbol, data_type=1, adjusted=adjusted, force_refresh=force_refresh)
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
        result = client.get_indices(asset_type, force_refresh=force_refresh)

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
        report += "## 3. Weekly Multi-Timeframe Analysis (MTF)\n"
        report += f"- **Weekly Trend Signal:** {w_latest.get('Signal')}\n"
        report += f"- **Weekly Pattern:** {w_latest.get('Pattern')}\n"
        report += f"- **Weekly RSI (14):** {w_latest.get('RSI')}\n"
        report += f"- **Weekly MACD:** {w_latest.get('MACD')}\n"
        report += f"- **Weekly SMA20/50:** {'Bullish' if (w_latest.get('SMA20') or 0) > (w_latest.get('SMA50') or 0) else 'Bearish'}\n\n"
        report += "Note: Weekly indicators provide a broader view of the long-term trend.\n\n"

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
    return jsonify({
        'status': 'در حال فعالیت', 
        'time': datetime.now().strftime('%H:%M:%S'),
        'stats': {
            'global': stats["global"],
            'services': stats["services"]
        }
    })

def startup_sync_worker():
    """
    Background worker that runs at startup.
    Extreme caution protocol enabled: Long gaps, high jitter, sequential.
    """
    print("DEBUG: Starting ULTRA-CAUTIOUS background sync worker...")
    # Give the server plenty of time to stabilize
    time.sleep(30) # Shifting to 30s to allow UI to breathe
    
    # Check all 5 API types
    for type_code in range(1, 6):
        db_category = f"api_type_{type_code}"
        
        try:
            # ONLY SYNC IF ABSOLUTELY EMPTY
            if db.is_market_empty(db_category):
                print(f"DEBUG: Registry for {db_category} is empty. Initializing sequential discovery...")
                # We use a special flag to tell make_request to be even gentler
                client._fetch_symbols_by_type(type_code, force_refresh=True)
                
                # ULTRA-CAUTIOUS: Wait 45-90 seconds between large discovery calls
                jitter = random.uniform(45.0, 90.0)
                print(f"DEBUG: Sync for Type {type_code} finished. Cooling down for {jitter:.1f}s...")
                time.sleep(jitter)
            else:
                print(f"DEBUG: Registry for {db_category} is already populated.")
        except Exception as e:
            print(f"DEBUG: Error in cautious background sync for Type {type_code}: {e}")
            time.sleep(60)

    print("DEBUG: ULTRA-CAUTIOUS Background sync worker finished.")

if __name__ == '__main__':
    # Start auto-sync thread to populate empty registry
    # Ensure it only runs once in debug mode
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        threading.Thread(target=startup_sync_worker, daemon=True).start()
    
    print("Starting Flask server on http://0.0.0.0:5000 ...")
    app.run(debug=True, host='0.0.0.0', port=5000)
