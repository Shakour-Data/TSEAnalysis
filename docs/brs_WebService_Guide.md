# راهنمای کامل وب سرویس TSETMC

## مقدمه

وب سرویس TSETMC (سامانه معاملات بورس تهران) مجموعه‌ای از APIهای رایگان و حرفه‌ای برای دسترسی به داده‌های بازار سرمایه ایران است. این راهنما نحوه استفاده کامل از این APIها را توضیح می‌دهد.

### ویژگی‌های کلیدی
- ✅ دسترسی رایگان به داده‌های لحظه‌ای و تاریخی
- ✅ پوشش کامل بازار بورس، فرابورس و بورس کالا
- ✅ داده‌های OHLCV، معاملات، شاخص‌ها و اطلاعات شرکت‌ها
- ✅ پشتیبانی از انواع تحلیل‌های تکنیکال و بنیادی
- ✅ محدودیت روزانه ۵۰,۰۰۰ درخواست

## ⚠️ هشدارهای مهم و قوانین استفاده

### هشدار درباره مصرف غیرمجاز API
**سلام کاربر گرامی،**

بررسی‌های سیستم نشان می‌دهد که تعداد درخواست‌های ارسالی شما از حد مجاز تعریف‌شده فراتر رفته است.

لازم است بلافاصله ارسال ریکوئست بیش از ظرفیت را متوقف کنید یا در صورت نیاز، نسبت به ارتقای تعداد درخواست‌های مجاز روزانه اقدام نمایید.

مطابق با قوانین استفاده منصفانه BrsApi، ارسال درخواست‌های مکرر و بدون منطق که منجر به ایجاد بار اضافی بر روی سرورها شود، تخلف محسوب شده و منجر به مسدودسازی دائمی و غیرقابل بازگشت کلید API، ایمیل و شماره موبایل ثبت‌نامی شما خواهد شد.

⚠️ **در صورتیکه تعداد ریکوئست‌های بیش از ظرفیت مجاز به 500 عدد برسد، کلیه درخواست‌های ارسالی شما به فایل‌های حجیم هدایت خواهند شد.** این اقدام با هدف جلوگیری از فشار اضافی بر سرور انجام می‌گیرد و ممکن است باعث کندی یا ایجاد هزینه‌های ناخواسته سمت کاربر شود.

لطفاً جهت جلوگیری از بروز این مشکلات، در اسرع وقت اقدامات لازم را انجام دهید.

### کلید دسترسی API
کلید دسترسی شما به وب‌سرویس با موفقیت صادر شد:

```
BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3
```

لطفاً از این کلید به‌صورت محرمانه نگهداری نمایید. در صورت از دست‌دادن، امکان بازیابی وجود ندارد. با این کلید می‌توانید از خدمات وب‌سرویس سایت BrsApi.ir استفاده نمایید.

### 🔔 نکته حیاتی برای کاربران Python
اگر از زبان برنامه‌نویسی Python برای اتصال به وب‌سرویس‌ها استفاده می‌کنید، توجه داشته باشید که **User-Agent پیش‌فرض پایتون طبق استاندارد 6G Firewall به‌صورت خودکار مسدود می‌شود**.

✅ **الزاما جهت جلوگیری از این مشکل، طبق نمونه‌کدی که در صفحه اصلی سایت قرار داده شده، از یک User-Agent معتبر استفاده کنید.** در غیر این صورت IP شما مسدود خواهد شد و امکان ارسال ریکوئست یا دسترسی به سایت نخواهید داشت.

### قوانین استفاده منصفانه
- **محدودیت روزانه:** مجموع ۵۰,۰۰۰ درخواست در روز
- **نرخ درخواست:** حداکثر ۶۰ درخواست در دقیقه
- **استفاده منطقی:** ارسال درخواست‌های مکرر بدون منطق تخلف است
- **مسدودسازی:** در صورت تخلف، کلید API دائماً مسدود می‌شود
- **هزینه‌های اضافی:** درخواست‌های بیش از حد به فایل‌های حجیم هدایت می‌شوند

### نکات امنیتی مهم
- کلید API را در متغیرهای محیطی ذخیره کنید
- از سیستم‌های کنترل نرخ استفاده کنید
- درخواست‌های خود را مانیتور کنید
- در صورت مشکل، با پشتیبانی تماس بگیرید

## ثبت‌نام و دریافت API Key

1. به وب‌سایت [brsapi.ir](https://brsapi.ir) مراجعه کنید
2. در بخش ثبت‌نام، اطلاعات خود را وارد کنید
3. پس از تایید ایمیل، API Key خود را دریافت کنید
4. API Key را در متغیر محیطی `BRS_API_KEY` ذخیره کنید

```bash
# در فایل .env
BRS_API_KEY=your_api_key_here
```

## تنظیمات اولیه در پایتون

### نصب کتابخانه‌های مورد نیاز
```bash
pip install requests python-dotenv
```

### تنظیمات امنیتی (حل مشکل فایروال نسل ۶)
**⚠️ این بخش بسیار مهم است - عدم رعایت آن منجر به مسدودسازی IP شما می‌شود**

یکی از مشکلات رایج در استفاده از APIهای ایرانی، بلاک شدن درخواست‌های پایتون توسط فایروال‌های نسل جدید (6G Firewall) است. این مشکل با تنظیم User-Agent مناسب حل می‌شود:

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# تنظیمات Session با User-Agent مناسب (الزامی!)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
})

# متغیرهای محیطی
API_KEY = os.getenv("BRS_API_KEY")
BASE_URL = "https://brsapi.ir"
```

### کلاس کلاینت آماده

```python
import requests
import time
from typing import Dict, List, Any, Optional

class TSETMCClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://brsapi.ir"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """ارسال درخواست با مدیریت خطا"""
        url = f"{self.base_url}/{endpoint}"
        request_params = {"key": self.api_key}
        if params:
            request_params.update(params)

        try:
            response = self.session.get(url, params=request_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"خطا در درخواست {endpoint}: {e}")
            return {}

    # متدهای API در ادامه تعریف می‌شوند
```

## APIهای اصلی TSETMC

### ۱. دریافت لیست تمام نمادها

**Endpoint:** `Api/Tsetmc/AllSymbols.php`  
**محدودیت روزانه:** ۱۰,۰۰۰ درخواست  
**توضیح:** لیست کامل تمام نمادهای فعال بورس و فرابورس

#### پارامترها:
- `type`: نوع بازار (۱ برای بورس، ۲ برای فرابورس)

#### پاسخ نمونه:
```json
[
  {
    "l18": "فولاد",
    "l30": "فولاد مبارکه اصفهان",
    "insCode": "12345678901234567",
    "sector": "فلزی",
    "market": "بورس"
  }
]
```

#### نمونه کد:
```python
def get_all_symbols(self, market_type: int = 1) -> List[Dict[str, Any]]:
    """دریافت لیست تمام نمادها"""
    return self._make_request("Api/Tsetmc/AllSymbols.php", {"type": market_type})

# استفاده
client = TSETMCClient("your_api_key")
symbols = client.get_all_symbols()
print(f"تعداد نمادها: {len(symbols)}")
```

### ۲. اطلاعات لحظه‌ای نماد

**Endpoint:** `Api/Tsetmc/Symbol.php`  
**محدودیت روزانه:** ۸,۰۰۰ درخواست  
**توضیح:** اطلاعات کامل لحظه‌ای یک نماد شامل قیمت، حجم، ارزش معاملات و غیره

#### پارامترها:
- `l18`: کد ۱۸ رقمی نماد (مثال: "فولاد")

#### پاسخ نمونه:
```json
{
  "symbol": "فولاد",
  "price": 1250,
  "volume": 1000000,
  "value": 1250000000,
  "last_trade": 1250,
  "change_percent": 2.5,
  "market_cap": 15000000000,
  "pe_ratio": 8.5
}
```

#### نمونه کد:
```python
def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
    """دریافت اطلاعات لحظه‌ای نماد"""
    return self._make_request("Api/Tsetmc/Symbol.php", {"l18": symbol})

# استفاده
info = client.get_symbol_info("فولاد")
print(f"قیمت فعلی فولاد: {info.get('price')}")
```

### ۳. داده‌های تاریخی قیمت

**Endpoint:** `Api/Tsetmc/History.php`  
**محدودیت روزانه:** ۴,۰۰۰ درخواست  
**توضیح:** داده‌های OHLCV تاریخی یک نماد

#### پارامترها:
- `l18`: کد نماد
- `type`: نوع داده (۰ برای قیمت، ۱ برای نوع مشتری)

#### پاسخ نمونه:
```json
[
  {
    "date": "2024-01-01",
    "open": 1200,
    "high": 1250,
    "low": 1180,
    "close": 1240,
    "volume": 500000,
    "value": 620000000
  }
]
```

#### نمونه کد:
```python
def get_price_history(self, symbol: str, data_type: int = 0) -> List[Dict[str, Any]]:
    """دریافت تاریخچه قیمت"""
    return self._make_request("Api/Tsetmc/History.php", {
        "l18": symbol,
        "type": data_type
    })

# استفاده
history = client.get_price_history("فولاد")
print(f"تعداد روزهای تاریخی: {len(history)}")
```

### ۴. داده‌های کندل‌استیک

**Endpoint:** `Api/Tsetmc/Candlestick.php`  
**محدودیت روزانه:** ۲,۰۰۰ درخواست  
**توضیح:** داده‌های کندل‌استیک با امکان تنظیم تعدیل قیمت

#### پارامترها:
- `l18`: کد نماد
- `adjusted`: تعدیل قیمت (true/false)

#### پاسخ نمونه:
```json
[
  {
    "date": "2024-01-01",
    "open": 1200,
    "high": 1250,
    "low": 1180,
    "close": 1240,
    "volume": 500000
  }
]
```

#### نمونه کد:
```python
def get_candlestick(self, symbol: str, adjusted: bool = True) -> List[Dict[str, Any]]:
    """دریافت کندل‌استیک"""
    return self._make_request("Api/Tsetmc/Candlestick.php", {
        "l18": symbol,
        "adjusted": str(adjusted).lower()
    })
```

### ۵. ریزمعاملات

**Endpoint:** `Api/Tsetmc/Transaction.php`  
**محدودیت روزانه:** ۱۰,۰۰۰ درخواست  
**توضیح:** لیست کامل معاملات روزانه یک نماد

#### پارامترها:
- `l18`: کد نماد

#### پاسخ نمونه:
```json
[
  {
    "time": "09:00:00",
    "price": 1240,
    "volume": 1000,
    "buyer": "مشتری حقوقی",
    "seller": "فروشنده حقیقی"
  }
]
```

#### نمونه کد:
```python
def get_transactions(self, symbol: str) -> List[Dict[str, Any]]:
    """دریافت ریزمعاملات"""
    return self._make_request("Api/Tsetmc/Transaction.php", {"l18": symbol})
```

### ۶. اطلاعات سهامداران

**Endpoint:** `Api/Tsetmc/Shareholder.php`  
**محدودیت روزانه:** ۱,۵۰۰ درخواست  
**توضیح:** لیست سهامداران عمده یک نماد

#### پارامترها:
- `l18`: کد نماد

#### پاسخ نمونه:
```json
[
  {
    "name": "صندوق بازنشستگی",
    "shares": 1000000,
    "percentage": 15.5,
    "change": 50000
  }
]
```

#### نمونه کد:
```python
def get_shareholders(self, symbol: str) -> List[Dict[str, Any]]:
    """دریافت اطلاعات سهامداران"""
    return self._make_request("Api/Tsetmc/Shareholder.php", {"l18": symbol})
```

### ۷. شاخص‌های بازار

**Endpoint:** `Api/Tsetmc/Index.php`  
**محدودیت روزانه:** ۲,۰۰۰ درخواست  
**توضیح:** اطلاعات شاخص‌های بورس و فرابورس

#### پارامترها:
- `type`: نوع شاخص (۱ برای بورس، ۲ برای فرابورس)

#### پاسخ نمونه:
```json
[
  {
    "name": "شاخص کل",
    "value": 1500000,
    "change": 2500,
    "change_percent": 0.17
  }
]
```

#### نمونه کد:
```python
def get_indices(self, index_type: int = 1) -> List[Dict[str, Any]]:
    """دریافت شاخص‌ها"""
    return self._make_request("Api/Tsetmc/Index.php", {"type": index_type})
```

### ۸. NAV صندوق‌های ETF

**Endpoint:** `Api/Tsetmc/Nav.php`  
**محدودیت روزانه:** ۱,۰۰۰ درخواست  
**توضیح:** ارزش خالص دارایی صندوق‌های ETF

#### پارامترها:
- `l18`: کد صندوق

#### پاسخ نمونه:
```json
{
  "nav": 12500,
  "date": "2024-01-01",
  "change": 150
}
```

## مدیریت محدودیت‌ها و نرخ درخواست

### محدودیت‌های روزانه
| API | محدودیت روزانه |
|-----|----------------|
| AllSymbols | ۱۰,۰۰۰ |
| Symbol | ۸,۰۰۰ |
| History | ۴,۰۰۰ |
| Candlestick | ۲,۰۰۰ |
| Transaction | ۱۰,۰۰۰ |
| Shareholder | ۱,۵۰۰ |
| Index | ۲,۰۰۰ |
| Nav | ۱,۰۰۰ |
| **مجموع** | **۵۰,۰۰۰** |

### مدیریت نرخ درخواست
```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)

    def can_make_request(self, endpoint: str) -> bool:
        """بررسی امکان ارسال درخواست"""
        now = time.time()
        # پاک کردن درخواست‌های قدیمی‌تر از ۲۴ ساعت
        self.requests[endpoint] = [t for t in self.requests[endpoint] if now - t < 86400]

        # محدودیت‌های روزانه
        limits = {
            "Api/Tsetmc/AllSymbols.php": 10000,
            "Api/Tsetmc/Symbol.php": 8000,
            "Api/Tsetmc/History.php": 4000,
            # ... سایر محدودیت‌ها
        }

        return len(self.requests[endpoint]) < limits.get(endpoint, 1000)

    def record_request(self, endpoint: str):
        """ثبت درخواست"""
        self.requests[endpoint].append(time.time())
```

## بهترین روش‌ها

### ۱. استفاده از Session
```python
# استفاده از Session برای بهبود عملکرد
session = requests.Session()
# تنظیم headers یک بار
```

### ۲. مدیریت خطا
```python
def safe_api_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            print("مشکل اتصال - بررسی اینترنت")
        except requests.exceptions.Timeout:
            print("زمان انتظار تمام شد - دوباره تلاش کنید")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("محدودیت نرخ - صبر کنید")
            elif e.response.status_code == 403:
                print("API Key نامعتبر")
        return None
    return wrapper
```

### ۳. کش کردن داده‌ها
```python
import json
from pathlib import Path

class DataCache:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get(self, key: str) -> Optional[Dict]:
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None

    def set(self, key: str, data: Dict, ttl: int = 3600):
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps(data))
```

### ۴. پردازش موازی (با احتیاط)
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_multiple_symbols(symbols: List[str]) -> Dict[str, Dict]:
    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_symbol = {
            executor.submit(client.get_symbol_info, symbol): symbol
            for symbol in symbols
        }

        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                results[symbol] = future.result()
            except Exception as e:
                print(f"خطا در دریافت {symbol}: {e}")

    return results
```

## عیب‌یابی

### مشکل فایروال نسل ۶ (6G Firewall)
**علت:** فایروال‌های مدرن درخواست‌های پایتون را با User-Agent پیش‌فرض بلاک می‌کنند.

**راه حل:** استفاده از User-Agent شبیه مرورگر (الزامی):
```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
}
```

**⚠️ هشدار:** عدم استفاده از User-Agent معتبر منجر به مسدودسازی IP شما می‌شود.

### مصرف بیش از حد API
**علت:** ارسال درخواست‌های مکرر بدون منطق.

**راه حل:**
- از RateLimiter استفاده کنید
- بین درخواست‌ها حداقل ۱ ثانیه صبر کنید
- درخواست‌های روزانه را مانیتور کنید
- در صورت نیاز، پلن پریمیوم خریداری کنید

**⚠️ عواقب:** مسدودسازی دائمی API Key و هدایت به فایل‌های حجیم.

### خطای JSON Decode
**علت:** برخی APIها ممکن است پاسخ فشرده یا رمزگذاری شده بدهند.

**راه حل:** اضافه کردن Accept-Encoding و مدیریت پاسخ:
```python
response = session.get(url, headers=headers)
response.encoding = 'utf-8'  # تنظیم encoding
data = response.json()
```

### خطای 429 (Too Many Requests)
- نرخ درخواست را کاهش دهید
- از RateLimiter استفاده کنید
- بین درخواست‌ها صبر کنید

### خطای 403 (Forbidden)
- API Key را بررسی کنید
- مطمئن شوید Key معتبر است
- User-Agent را چک کنید

### خطای اتصال
- اینترنت را بررسی کنید
- از VPN استفاده کنید اگر لازم است
- timeout را افزایش دهید

### نکات مهم برای توسعه‌دهندگان
- همیشه از try-except استفاده کنید
- پاسخ‌های API را validate کنید
- از کش برای کاهش درخواست‌ها استفاده کنید
- محدودیت‌های روزانه را رعایت کنید
- در صورت مشکل، با پشتیبانی تماس بگیرید

## نمونه پروژه کامل

```python
import os
import time
import requests
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class TSETMCTrader:
    def __init__(self):
        self.client = TSETMCClient(os.getenv("BRS_API_KEY"))
        self.watchlist = ["فولاد", "شپنا", "وتجارت"]

    def analyze_market(self):
        """تحلیل کلی بازار"""
        print("📊 تحلیل بازار...")

        # دریافت شاخص‌ها
        indices = self.client.get_indices()
        for index in indices[:3]:  # ۳ شاخص اول
            print(f"شاخص {index['name']}: {index['value']} ({index['change_percent']}%)")

        # تحلیل نمادهای دیده‌بانی
        for symbol in self.watchlist:
            info = self.client.get_symbol_info(symbol)
            if info:
                print(f"{symbol}: قیمت {info.get('price'):,} - تغییر {info.get('change_percent')}%")

    def get_historical_data(self, symbol: str, days: int = 30):
        """دریافت داده‌های تاریخی"""
        history = self.client.get_price_history(symbol)
        return history[-days:] if history else []

    def monitor_realtime(self):
        """مانیتورینگ لحظه‌ای"""
        while True:
            self.analyze_market()
            time.sleep(60)  # هر دقیقه بروزرسانی

# استفاده
if __name__ == "__main__":
    trader = TSETMCTrader()
    trader.analyze_market()

    # داده‌های تاریخی فولاد
    history = trader.get_historical_data("فولاد", 7)
    print(f"داده‌های ۷ روز گذشته فولاد: {len(history)} رکورد")
```

## منابع اضافی

- [مستندات رسمی BRS API](https://brsapi.ir)
- [سایت TSETMC](https://www.tsetmc.com)
- [کد نمونه‌های پایتون](https://github.com/brsapi/python-examples)

## نمونه پروژه کامل

```python
import os
import time
import requests
from typing import Dict, List, Any
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

load_dotenv()

class TSETMCTrader:
    def __init__(self):
        self.client = TSETMCClient(os.getenv("BRS_API_KEY"))
        self.watchlist = ["فولاد", "شپنا", "وتجارت", "شیراز", "غگل"]

    def analyze_market(self):
        """تحلیل کلی بازار"""
        print("📊 تحلیل بازار..."        print(f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # دریافت شاخص‌ها
        indices = self.client.get_indices()
        for index in indices[:3]:  # ۳ شاخص اول
            print(f"📈 شاخص {index['name']}: {index['value']:,} ({index['change_percent']:+.2f}%)")

        # تحلیل نمادهای دیده‌بانی
        for symbol in self.watchlist:
            info = self.client.get_symbol_info(symbol)
            if info:
                price = info.get('price', 0)
                change = info.get('change_percent', 0)
                volume = info.get('volume', 0)
                print(f"💰 {symbol}: قیمت {price:,} - تغییر {change:+.2f}% - حجم {volume:,}")

    def get_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """دریافت داده‌های تاریخی و تبدیل به DataFrame"""
        history = self.client.get_price_history(symbol)
        if not history:
            return pd.DataFrame()

        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()

        # محاسبه اندیکاتورهای ساده
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()

        return df.tail(days)

    def technical_analysis(self, symbol: str) -> Dict[str, Any]:
        """تحلیل تکنیکال ساده"""
        df = self.get_historical_data(symbol, 100)
        if df.empty:
            return {"error": "No data available"}

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        signals = {
            "symbol": symbol,
            "price": latest['close'],
            "sma_20": latest['SMA_20'],
            "sma_50": latest['SMA_50'],
            "trend": "صعودی" if latest['SMA_20'] > latest['SMA_50'] else "نزولی",
            "momentum": "قوی" if latest['close'] > prev['close'] else "ضعیف"
        }

        return signals

    def monitor_realtime(self, interval_minutes: int = 5):
        """مانیتورینگ لحظه‌ای با تحلیل"""
        print(f"🔄 شروع مانیتورینگ هر {interval_minutes} دقیقه... (Ctrl+C برای توقف)")

        try:
            while True:
                self.analyze_market()
                print("\n" + "="*50 + "\n")

                # تحلیل تکنیکال
                for symbol in self.watchlist[:2]:  # فقط ۲ نماد اول
                    analysis = self.technical_analysis(symbol)
                    if "error" not in analysis:
                        print(f"📊 تحلیل {symbol}: روند {analysis['trend']} - حرکت {analysis['momentum']}")

                time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n⏹️ مانیتورینگ متوقف شد")

    def export_data(self, symbol: str, filename: str = None):
        """اکسپورت داده‌ها به CSV"""
        df = self.get_historical_data(symbol, 365)  # یک سال
        if df.empty:
            print(f"❌ داده‌ای برای {symbol} یافت نشد")
            return

        if not filename:
            filename = f"{symbol}_data.csv"

        df.to_csv(filename)
        print(f"✅ داده‌های {symbol} در {filename} ذخیره شد ({len(df)} رکورد)")

# استفاده
if __name__ == "__main__":
    trader = TSETMCTrader()

    # تحلیل بازار
    trader.analyze_market()

    print("\n" + "="*50)

    # تحلیل تکنیکال یک نماد
    analysis = trader.technical_analysis("فولاد")
    print(f"تحلیل تکنیکال فولاد: {analysis}")

    print("\n" + "="*50)

    # اکسپورت داده‌ها
    trader.export_data("فولاد")

    # برای مانیتورینگ لحظه‌ای:
    # trader.monitor_realtime(10)  # هر ۱۰ دقیقه
```

## مثال‌های پیشرفته تحلیل داده‌ها

### تحلیل تکنیکال با TA-Lib

```python
import talib
import numpy as np

def advanced_technical_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """تحلیل تکنیکال پیشرفته"""
    if len(df) < 50:
        return {"error": "Not enough data"}

    close = df['close'].values
    high = df['high'].values
    low = df['low'].values

    # RSI
    rsi = talib.RSI(close, timeperiod=14)

    # MACD
    macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

    # Bollinger Bands
    upperband, middleband, lowerband = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)

    # Stochastic
    slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)

    latest = {
        "rsi": rsi[-1],
        "macd": macd[-1],
        "macd_signal": macdsignal[-1],
        "macd_hist": macdhist[-1],
        "bb_upper": upperband[-1],
        "bb_middle": middleband[-1],
        "bb_lower": lowerband[-1],
        "stoch_k": slowk[-1],
        "stoch_d": slowd[-1],
        "price": close[-1]
    }

    # سیگنال‌های خرید/فروش
    signals = []

    # RSI سیگنال
    if latest['rsi'] < 30:
        signals.append("RSI سیگنال خرید (کم‌فروش)")
    elif latest['rsi'] > 70:
        signals.append("RSI سیگنال فروش (پرکیف)")

    # MACD سیگنال
    if latest['macd'] > latest['macd_signal'] and macd[-2] <= macdsignal[-2]:
        signals.append("MACD سیگنال خرید")
    elif latest['macd'] < latest['macd_signal'] and macd[-2] >= macdsignal[-2]:
        signals.append("MACD سیگنال فروش")

    # Bollinger Bands سیگنال
    if latest['price'] <= latest['bb_lower']:
        signals.append("BB سیگنال خرید (لمس باند پایین)")
    elif latest['price'] >= latest['bb_upper']:
        signals.append("BB سیگنال فروش (لمس باند بالا)")

    return {
        "indicators": latest,
        "signals": signals,
        "signal_count": len(signals)
    }

# استفاده
analysis = advanced_technical_analysis(df)
print(f"سیگنال‌های {symbol}: {analysis['signals']}")
```

### تحلیل بنیادی ساده

```python
def fundamental_analysis(symbol: str) -> Dict[str, Any]:
    """تحلیل بنیادی ساده"""
    # دریافت اطلاعات شرکت
    info = client.get_symbol_info(symbol)
    shareholders = client.get_shareholders(symbol)

    if not info or not shareholders:
        return {"error": "Data not available"}

    market_cap = info.get('market_cap', 0)
    price = info.get('price', 0)

    # محاسبه تمرکز مالکیت
    total_shares = sum(s.get('shares', 0) for s in shareholders)
    major_shareholders = [s for s in shareholders if s.get('percentage', 0) > 5]

    concentration = {
        "total_shareholders": len(shareholders),
        "major_shareholders": len(major_shareholders),
        "concentration_ratio": len(major_shareholders) / len(shareholders) if shareholders else 0,
        "largest_shareholder": max((s.get('percentage', 0) for s in shareholders), default=0)
    }

    # تحلیل ساده
    analysis = {
        "symbol": symbol,
        "market_cap": market_cap,
        "pe_ratio": info.get('pe_ratio'),
        "concentration": concentration,
        "ownership_type": "متمرکز" if concentration['concentration_ratio'] > 0.3 else "پخش شده"
    }

    return analysis
```

## ویژوالیزیشن داده‌ها

### نمودار قیمت با اندیکاتورها

```python
def plot_technical_chart(symbol: str, days: int = 90):
    """رسم نمودار تکنیکال"""
    df = trader.get_historical_data(symbol, days)

    if df.empty:
        print(f"❌ داده‌ای برای {symbol} یافت نشد")
        return

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10), sharex=True)

    # نمودار قیمت و میانگین‌ها
    ax1.plot(df.index, df['close'], label='Close Price', color='blue', linewidth=2)
    ax1.plot(df.index, df['SMA_20'], label='SMA 20', color='orange', linestyle='--')
    ax1.plot(df.index, df['SMA_50'], label='SMA 50', color='red', linestyle='--')
    ax1.set_title(f'نمودار قیمت {symbol}')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # نمودار حجم معاملات
    ax2.bar(df.index, df['volume'], color='green', alpha=0.7)
    ax2.set_title('حجم معاملات')
    ax2.grid(True, alpha=0.3)

    # RSI
    if 'RSI' in df.columns:
        ax3.plot(df.index, df['RSI'], color='purple', linewidth=2)
        ax3.axhline(y=70, color='red', linestyle='--', alpha=0.7)
        ax3.axhline(y=30, color='green', linestyle='--', alpha=0.7)
        ax3.fill_between(df.index, 30, 70, alpha=0.1, color='gray')
        ax3.set_title('RSI (14)')
        ax3.set_ylim(0, 100)
        ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{symbol}_technical_chart.png', dpi=300, bbox_inches='tight')
    plt.show()

    print(f"✅ نمودار {symbol} ذخیره شد")

# استفاده
plot_technical_chart("فولاد", 60)
```

### نمودار مقایسه نمادها

```python
def compare_symbols(symbols: List[str], days: int = 30):
    """مقایسه عملکرد نمادها"""
    plt.figure(figsize=(15, 8))

    for symbol in symbols:
        df = trader.get_historical_data(symbol, days)
        if not df.empty:
            # نرمال‌سازی قیمت‌ها به درصد تغییر
            start_price = df['close'].iloc[0]
            normalized = (df['close'] / start_price - 1) * 100
            plt.plot(df.index, normalized, label=symbol, linewidth=2)

    plt.title('مقایسه عملکرد نمادها (تغییر درصدی)')
    plt.xlabel('تاریخ')
    plt.ylabel('تغییر قیمت (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.8)
    plt.tight_layout()
    plt.savefig('symbols_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

# استفاده
compare_symbols(["فولاد", "شپنا", "وتجارت"], 30)
```

## راه‌اندازی محیط توسعه

### ساختار پروژه پیشنهادی

```
tsetmc_project/
├── config/
│   ├── .env                    # API keys and settings
│   └── settings.py            # Configuration
├── src/
│   ├── __init__.py
│   ├── client.py              # TSETMC API client
│   ├── analyzer.py            # Analysis functions
│   ├── visualizer.py          # Charts and plots
│   └── trader.py              # Trading logic
├── data/
│   ├── cache/                 # Cached data
│   └── exports/               # Exported files
├── tests/
│   ├── test_client.py
│   ├── test_analyzer.py
│   └── test_integration.py
├── notebooks/
│   └── exploration.ipynb      # Jupyter notebooks
├── logs/
│   └── app.log
├── requirements.txt
├── main.py                    # Entry point
└── README.md
```

### فایل تنظیمات (config/settings.py)

```python
import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
EXPORT_DIR = DATA_DIR / "exports"
LOG_DIR = PROJECT_ROOT / "logs"

# API Settings
API_KEY = os.getenv("BRS_API_KEY")
BASE_URL = "https://brsapi.ir"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = 60
DAILY_QUOTA = 50000

# Cache Settings
CACHE_TTL_HOURS = 24
MAX_CACHE_SIZE_MB = 100

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Watchlist
DEFAULT_WATCHLIST = ["فولاد", "شپنا", "وتجارت", "شیراز", "غگل"]
```

### سیستم لاگ‌گیری

```python
import logging
from config.settings import LOG_DIR, LOG_LEVEL, LOG_FORMAT

def setup_logging():
    """راه‌اندازی سیستم لاگ‌گیری"""
    LOG_DIR.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_DIR / "app.log"),
            logging.StreamHandler()
        ]
    )

    # لاگ درخواست‌های API
    api_logger = logging.getLogger("api")
    api_handler = logging.FileHandler(LOG_DIR / "api.log")
    api_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)

setup_logging()
logger = logging.getLogger(__name__)
```

## تست و دیباگینگ

### تست واحد API Client

```python
import unittest
from unittest.mock import Mock, patch
import sys
import os

# اضافه کردن مسیر پروژه
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.client import TSETMCClient

class TestTSETMCClient(unittest.TestCase):

    def setUp(self):
        self.client = TSETMCClient("test_key")

    @patch('src.client.requests.Session.get')
    def test_get_symbols_success(self, mock_get):
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = [
            {"l18": "فولاد", "l30": "فولاد مبارکه"},
            {"l18": "شپنا", "l30": "پالایش نفت اصفهان"}
        ]
        mock_get.return_value = mock_response

        symbols = self.client.get_all_symbols()
        self.assertEqual(len(symbols), 2)
        self.assertEqual(symbols[0]["l18"], "فولاد")

    @patch('src.client.requests.Session.get')
    def test_get_symbols_failure(self, mock_get):
        mock_get.side_effect = Exception("Connection error")

        symbols = self.client.get_all_symbols()
        self.assertEqual(symbols, [])

    def test_rate_limiting(self):
        # تست محدودیت نرخ
        pass

if __name__ == '__main__':
    unittest.main()
```

### تست انتگراسیون

```python
import pytest
from src.client import TSETMCClient
from config.settings import API_KEY

class TestIntegration:

    @pytest.fixture
    def client(self):
        return TSETMCClient(API_KEY)

    def test_real_api_connection(self, client):
        """تست اتصال واقعی به API"""
        symbols = client.get_all_symbols()
        assert isinstance(symbols, list)
        assert len(symbols) > 0

        # چک کردن ساختار داده
        symbol = symbols[0]
        assert "l18" in symbol
        assert "l30" in symbol

    def test_symbol_data_quality(self, client):
        """تست کیفیت داده‌های نماد"""
        symbols = client.get_all_symbols()
        if symbols:
            symbol_code = symbols[0]["l18"]
            history = client.get_price_history(symbol_code)

            if history:  # ممکن است داده موجود نباشد
                record = history[0]
                required_fields = ["date", "open", "high", "low", "close", "volume"]

                for field in required_fields:
                    assert field in record, f"فیلد {field} موجود نیست"

                # چک کردن منطق داده‌ها
                assert record["high"] >= record["low"], "high باید بزرگتر از low باشد"
                assert record["close"] >= 0, "قیمت close باید مثبت باشد"

    def test_error_handling(self, client):
        """تست مدیریت خطا"""
        # تست با نماد نامعتبر
        history = client.get_price_history("نماد_نامعتبر_12345")
        assert history == []  # باید لیست خالی برگرداند

        # تست با API key نامعتبر
        invalid_client = TSETMCClient("invalid_key")
        symbols = invalid_client.get_all_symbols()
        assert symbols == []  # باید لیست خالی برگرداند
```

### اجرای تست‌ها

```bash
# نصب pytest
pip install pytest pytest-cov

# اجرای تست‌ها
pytest tests/ -v

# اجرای تست‌ها با پوشش کد
pytest tests/ --cov=src --cov-report=html

# اجرای تست‌های انتگراسیون (نیاز به API key واقعی دارد)
pytest tests/test_integration.py -v -k "not real_api"
```

## نکات بهینه‌سازی عملکرد

### ۱. کش هوشمند

```python
from cachetools import TTLCache, cached
import pickle
from pathlib import Path

class SmartCache:
    def __init__(self, cache_dir: Path, ttl_seconds: int = 3600):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache = TTLCache(maxsize=1000, ttl=ttl_seconds)

    def _get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.pkl"

    def get(self, key: str):
        # اول از کش حافظه چک کن
        if key in self.memory_cache:
            return self.memory_cache[key]

        # سپس از فایل چک کن
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                # ذخیره در کش حافظه
                self.memory_cache[key] = data
                return data
            except Exception:
                pass

        return None

    def set(self, key: str, value):
        # ذخیره در کش حافظه
        self.memory_cache[key] = value

        # ذخیره در فایل
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            print(f"خطا در ذخیره کش: {e}")

# استفاده
cache = SmartCache(Path("data/cache"))

@cached(cache.memory_cache)
def get_expensive_data(symbol: str):
    # این تابع فقط یک بار در ساعت اجرا می‌شود
    return client.get_price_history(symbol)
```

### ۲. پردازش موازی ایمن

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
import time

class SafeParallelProcessor:
    def __init__(self, max_workers: int = 3, requests_per_minute: int = 60):
        self.max_workers = max_workers
        self.semaphore = Semaphore(requests_per_minute)
        self.last_request_time = 0
        self.min_interval = 60 / requests_per_minute

    def _wait_for_rate_limit(self):
        """انتظار برای رعایت محدودیت نرخ"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)

        self.last_request_time = time.time()

    def process_symbols_parallel(self, symbols: List[str], func) -> Dict[str, Any]:
        """پردازش موازی ایمن"""
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self._safe_request, symbol, func): symbol
                for symbol in symbols
            }

            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    results[symbol] = future.result()
                except Exception as e:
                    print(f"خطا در پردازش {symbol}: {e}")
                    results[symbol] = None

        return results

    def _safe_request(self, symbol: str, func):
        """ارسال درخواست ایمن"""
        with self.semaphore:
            self._wait_for_rate_limit()
            return func(symbol)

# استفاده
processor = SafeParallelProcessor(max_workers=3, requests_per_minute=60)

def fetch_symbol_data(symbol):
    return client.get_price_history(symbol)

results = processor.process_symbols_parallel(
    ["فولاد", "شپنا", "وتجارت"],
    fetch_symbol_data
)
```

### ۳. بهینه‌سازی مصرف حافظه

```python
import gc
from typing import Iterator

def process_large_dataset(symbols: List[str]) -> Iterator[Dict]:
    """پردازش داده‌های بزرگ به صورت streaming"""
    for symbol in symbols:
        data = client.get_price_history(symbol)

        if data:
            # پردازش داده‌ها
            processed = process_symbol_data(data)
            yield processed

        # آزادسازی حافظه
        del data
        gc.collect()

def process_symbol_data(data: List[Dict]) -> Dict:
    """پردازش داده‌های یک نماد"""
    df = pd.DataFrame(data)

    # محاسبات سنگین
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(20).std()

    # فقط نتایج مهم را نگه دار
    return {
        'symbol': data[0].get('symbol'),
        'avg_volume': df['volume'].mean(),
        'volatility': df['volatility'].iloc[-1],
        'total_return': (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
    }

# استفاده
for result in process_large_dataset(all_symbols):
    print(f"{result['symbol']}: بازدهی {result['total_return']:.2f}%")
```

## امنیت و مانیتورینگ

### مانیتورینگ استفاده از API

```python
import psutil
import time
from datetime import datetime, timedelta

class APIMonitor:
    def __init__(self):
        self.requests_log = []
        self.start_time = datetime.now()

    def log_request(self, endpoint: str, success: bool, response_time: float):
        """لاگ کردن درخواست"""
        self.requests_log.append({
            'timestamp': datetime.now(),
            'endpoint': endpoint,
            'success': success,
            'response_time': response_time
        })

    def get_stats(self) -> Dict:
        """آمار استفاده"""
        total_requests = len(self.requests_log)
        successful_requests = len([r for r in self.requests_log if r['success']])
        failed_requests = total_requests - successful_requests

        if self.requests_log:
            avg_response_time = sum(r['response_time'] for r in self.requests_log) / total_requests
            min_response_time = min(r['response_time'] for r in self.requests_log)
            max_response_time = max(r['response_time'] for r in self.requests_log)
        else:
            avg_response_time = min_response_time = max_response_time = 0

        # آمار ساعتی
        hourly_stats = {}
        for request in self.requests_log:
            hour = request['timestamp'].strftime('%Y-%m-%d %H:00')
            if hour not in hourly_stats:
                hourly_stats[hour] = 0
            hourly_stats[hour] += 1

        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
            'avg_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'hourly_stats': hourly_stats,
            'uptime': str(datetime.now() - self.start_time)
        }

    def generate_report(self) -> str:
        """تولید گزارش"""
        stats = self.get_stats()

        report = f"""
گزارش استفاده از API
==================

زمان شروع: {self.start_time}
آپ‌تایم: {stats['uptime']}

آمار کلی:
- کل درخواست‌ها: {stats['total_requests']}
- درخواست‌های موفق: {stats['successful_requests']}
- درخواست‌های ناموفق: {stats['failed_requests']}
- نرخ موفقیت: {stats['success_rate']:.2%}

زمان پاسخ:
- میانگین: {stats['avg_response_time']:.2f}s
- حداقل: {stats['min_response_time']:.2f}s
- حداکثر: {stats['max_response_time']:.2f}s

آمار ساعتی:
"""

        for hour, count in sorted(stats['hourly_stats'].items()):
            report += f"- {hour}: {count} درخواست\n"

        return report

# استفاده
monitor = APIMonitor()

# در کلاینت
def monitored_request(self, endpoint, *args, **kwargs):
    start_time = time.time()
    try:
        result = self._make_request(endpoint, *args, **kwargs)
        success = True
    except Exception:
        result = None
        success = False

    response_time = time.time() - start_time
    monitor.log_request(endpoint, success, response_time)

    return result

# نمایش گزارش
print(monitor.generate_report())
```

### هشدارهای امنیتی

```python
import smtplib
from email.mime.text import MIMEText

class SecurityMonitor:
    def __init__(self, alert_email: str = None):
        self.alert_email = alert_email
        self.alerts = []

    def check_rate_limit_violation(self, requests_per_minute: int):
        """بررسی violation محدودیت نرخ"""
        if requests_per_minute > 60:  # بیش از حد مجاز
            alert = f"⚠️ VIOLATION: {requests_per_minute} requests/minute (limit: 60)"
            self.alerts.append(alert)
            self.send_alert(alert)

    def check_api_key_exposure(self, code_content: str):
        """بررسی افشای API key"""
        import re
        api_key_pattern = r'BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3'  # الگوی API key

        if re.search(api_key_pattern, code_content):
            alert = "🚨 SECURITY: API key found in code!"
            self.alerts.append(alert)
            self.send_alert(alert)

    def send_alert(self, message: str):
        """ارسال هشدار"""
        if not self.alert_email:
            print(message)
            return

        try:
            msg = MIMEText(message)
            msg['Subject'] = 'TSETMC API Security Alert'
            msg['From'] = 'security@tsetmc.local'
            msg['To'] = self.alert_email

            # ارسال ایمیل (پیکربندی SMTP نیاز است)
            # server = smtplib.SMTP('localhost')
            # server.send_message(msg)
            # server.quit()

            print(f"Alert sent: {message}")
        except Exception as e:
            print(f"Failed to send alert: {e}")

# استفاده
security = SecurityMonitor("admin@example.com")

# چک کردن کد برای API key
with open('config.py', 'r') as f:
    security.check_api_key_exposure(f.read())
```

---

**نکته نهایی:** این راهنما یک نقطه شروع کامل برای توسعه‌دهندگانی است که می‌خواهند از API وب سرویس TSETMC استفاده کنند. با رعایت تمام قوانین و بهترین روش‌ها، می‌توانید برنامه‌های قدرتمند و قابل اعتمادی بسازید.

برای آخرین تغییرات و بروزرسانی‌ها، مستندات رسمی BrsApi.ir را بررسی کنید.