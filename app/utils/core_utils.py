import os
import requests
import requests.utils
import urllib3

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
except Exception:
    # Catch all exceptions including import issues
    httpx = None
    HTTPX_AVAILABLE = False

# Exporting for other modules
try:
    import tls_client
except ImportError:
    tls_client = None

# Configuration - حفاظتی طریقے سے
def _get_api_key():
    """
    API key کو بحفاظت حاصل کریں۔
    ترتیب:
    1. Environment variable (بہترین)
    2. .env file
    3. error اگر موجود نہیں
    """
    key = os.getenv('TSE_API_KEY')
    
    if not key:
        # .env فائل سے کوشش کریں
        try:
            from dotenv import load_dotenv
            load_dotenv()
            key = os.getenv('TSE_API_KEY')
        except:
            pass
    
    if not key:
        import logging
        logging.warning("⚠️ TSE_API_KEY environment variable not set! Using fallback.")
        # Fallback - لیکن warning دیں
        key = 'guest_mode'
    
    return key

API_KEY = _get_api_key()
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
# ===== DATE UTILITIES - Gregorian/Jalali Support =====
from datetime import datetime, timedelta
import jdatetime
import logging

date_logger = logging.getLogger(__name__)

class DateFormatter:
    """Gregorian (ISO 8601) اور Jalali (تاریخ) دونوں کے لیے support"""
    
    # Date format standardization
    GREGORIAN_FORMAT = "%Y-%m-%d"
    JALALI_FORMAT = "%Y-%m-%d"
    
    @staticmethod
    def to_gregorian(date_str, format_str=None):
        """کسی بھی فارمیٹ کو Gregorian میں تبدیل کریں"""
        if not date_str:
            return None
        
        try:
            # اگر پہلے سے Gregorian ہے تو چھوڑ دیں (Year > 1500)
            if isinstance(date_str, str) and len(date_str) == 10 and date_str[4] == '-':
                year = int(date_str[:4])
                if year > 1500:
                    datetime.strptime(date_str, DateFormatter.GREGORIAN_FORMAT)
                    return date_str
            
            # Jalali سے Gregorian
            if format_str:
                j_date = jdatetime.datetime.strptime(date_str, format_str)
            else:
                j_date = jdatetime.datetime.strptime(date_str, DateFormatter.JALALI_FORMAT)
            
            # Convert to Gregorian
            g_date = j_date.togregorian()
            return g_date.strftime(DateFormatter.GREGORIAN_FORMAT)
        
        except Exception as e:
            date_logger.warning(f"تاریخ تبدیلی میں ناکامی: {date_str} -> {e}")
            return None
    
    @staticmethod
    def to_jalali(date_str, format_str=None):
        """Gregorian کو Jalali میں تبدیل کریں"""
        if not date_str:
            return None
        
        try:
            # Gregorian date parse کریں
            if format_str:
                g_date = datetime.strptime(date_str, format_str)
            else:
                g_date = datetime.strptime(date_str, DateFormatter.GREGORIAN_FORMAT)
            
            # Jalali میں convert کریں
            j_date = jdatetime.date.fromgregorian(
                year=g_date.year,
                month=g_date.month,
                day=g_date.day
            )
            return j_date.strftime(DateFormatter.JALALI_FORMAT)
        
        except Exception as e:
            date_logger.warning(f"تاریخ تبدیلی میں ناکامی: {date_str} -> {e}")
            return None
    
    @staticmethod
    def get_gregorian_today():
        """آج کی تاریخ Gregorian میں"""
        return datetime.now().strftime(DateFormatter.GREGORIAN_FORMAT)
    
    @staticmethod
    def get_jalali_today():
        """آج کی تاریخ Jalali میں"""
        today = jdatetime.date.today()
        return today.strftime(DateFormatter.JALALI_FORMAT)
    
    @staticmethod
    def add_days(date_str, days, to_format='gregorian'):
        """تاریخ میں دن شامل کریں"""
        try:
            g_date = datetime.strptime(date_str, DateFormatter.GREGORIAN_FORMAT)
            new_date = g_date + timedelta(days=days)
            
            if to_format == 'jalali':
                return DateFormatter.to_jalali(new_date.strftime(DateFormatter.GREGORIAN_FORMAT))
            else:
                return new_date.strftime(DateFormatter.GREGORIAN_FORMAT)
        
        except Exception as e:
            date_logger.error(f"تاریخ میں دن شامل کرنے میں ناکامی: {date_str} +{days} -> {e}")
            return None
    
    @staticmethod
    def date_range(start_date, end_date, format_in='gregorian'):
        """دو تاریخوں کے درمیان تمام دن"""
        try:
            start = datetime.strptime(start_date, DateFormatter.GREGORIAN_FORMAT)
            end = datetime.strptime(end_date, DateFormatter.GREGORIAN_FORMAT)
            
            dates = []
            current = start
            while current <= end:
                if format_in == 'jalali':
                    dates.append(DateFormatter.to_jalali(current.strftime(DateFormatter.GREGORIAN_FORMAT)))
                else:
                    dates.append(current.strftime(DateFormatter.GREGORIAN_FORMAT))
                current += timedelta(days=1)
            
            return dates
        
        except Exception as e:
            date_logger.error(f"تاریخوں کی رینج بنانے میں ناکامی: {start_date} to {end_date} -> {e}")
            return []
class CoreUtils:
    @staticmethod
    def safe_round(value, decimals=0):
        try:
            if value is None: return 0.0
            return round(float(value), decimals)
        except: return 0.0

    @staticmethod
    def format_number(value, suffix='', persian_digits=False):
        try:
            if value is None: return '0'
            formatted = '{:,}'.format(value)
            if persian_digits:
                formatted = CoreUtils.to_persian_digits(formatted)
            return (formatted + ' ' + suffix).strip()
        except: return str(value)

    @staticmethod
    def to_persian_digits(text):
        """Convert English digits to Persian digits"""
        if not text:
            return text
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        translation_table = str.maketrans(english_digits, persian_digits)
        return text.translate(translation_table)

    @staticmethod
    def to_english_digits(text):
        """Convert Persian digits to English digits"""
        if not text:
            return text
        english_digits = '0123456789'
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        translation_table = str.maketrans(persian_digits, english_digits)
        return text.translate(translation_table)

    @staticmethod
    def get_nested_value(data, path, default=None):
        if not data or not path: return default
        try:
            keys = path.split('.')
            val = data
            for k in keys:
                val = val.get(k)
                if val is None: return default
            return val
        except: return default

    @staticmethod
    def is_numeric(value):
        try:
            float(value)
            return True
        except: return False
