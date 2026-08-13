# راهنمای فنی دور زدن محدودیت‌های شبکه برای دریافت داده‌های بورس (TSETMC)

این سند شامل استراتژی‌های پیاده‌سازی شده برای دسترسی به APIهای ایرانی (مانند BrsApi) از سرورهای خارج از کشور (مانند OVH فرانسه، Hetzner آلمان و غیره) است که مستقیماً توسط فایروال‌های هوشمند ایران مسدود می‌شوند.

---

## ۱. صورت مسئله (The Problem)

دیتاسنترهای خارجی با سه لایه فیلترینگ روبرو هستند:
1.  **بلاک بودن رنج IP:** دیتاسنترهایی مثل OVH در بسیاری از لایه‌های فایروال ایران بلاک هستند (خطای Connection Reset 10054).
2.  **شناسایی TLS Fingerprint:** فایروال‌های نسل جدید (NGFW) با تحلیل ترتیب افزونه‌های TLS در شروع اتصال، متوجه می‌شوند که درخواست از طرف یک کتابخانه برنامه‌نویسی (مثل Python Requests) ارسال شده و نه یک مرورگر واقعی.
3.  **فایروال 6G:** مسدودسازی خودکار درخواست‌هایی که دارای User-Agentهای پیش‌فرض و غیرمعمول هستند.

---

## ۲. راه حل نهایی: پل ارتباطی گوگل (Google Apps Script Bridge)

این روش **۱۰۰٪ تضمینی** است زیرا ترافیک از سرورهای گوگل عبور می‌کند که فایروال ایران به آن‌ها اعتماد دارد.

### الف) ساخت پل (Google Side)
در [script.google.com](https://script.google.com) یک پروژه جدید بسازید و این کد را قرار دهید:

```javascript
function doGet(e) {
  var url = e.parameter.url;
  var options = {
    'method': 'get',
    'headers': {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0'
    },
    'muteHttpExceptions': true,
    'followRedirects': true
  };
  var response = UrlFetchApp.fetch(url, options);
  return ContentService.createTextOutput(response.getContentText()).setMimeType(ContentService.MimeType.JSON);
}
```
**نکته حیاتی:** موقع Deploy، دسترسی را روی **Anyone** تنظیم کنید.

### ب) پیاده‌سازی در کلاینت (Python Side)

```python
import requests
from urllib.parse import quote

BRIDGE_URL = "لینک_گوگل_اسکریپت_شما"

def fetch_data(api_url):
    try:
        # انکود کردن آدرس مقصد برای ارسال به عنوان پارامتر
        final_url = f"{BRIDGE_URL}?url={quote(api_url)}"
        response = requests.get(final_url, timeout=30)
        return response.json()
    except Exception as e:
        print(f"Bypass Failed: {e}")
```

---

## ۳. لایه دوم: جعل هویت مرورگر (TLS Spoofing)

اگر می‌خواهید مستقیماً متصل شوید (در سرورهای داخلی یا سرورهای خارجی که هنوز مسدود نشده‌اند)، باید اثر انگشت JA3 خود را تغییر دهید.

### استفاده از `tls_client` یا `curl_cffi`

```bash
pip install tls_client curl_cffi
```

```python
import tls_client

# ایجاد یک سشن که دقیقاً رفتار مرورگر کروم نسخه ۱۲۰ را شبیه‌سازی می‌کند
session = tls_client.Session(
    client_identifier="chrome_120",
    random_tls_extension_order=True
)

response = session.get("https://brsapi.ir/Api/...", headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
})
```

---

## ۴. لایه سوم: استفاده از Native Curl (Nuclear Option)

در مواردی که کتابخانه‌های پایتونی شکست می‌خورند، استفاده از خودِ `curl` سیستم با تنظیمات امنیتی پایین (Lower Security Level) راهگشاست.

```python
import subprocess
import json

def native_curl_request(url):
    cmd = [
        'curl', '-s', '-k',
        '--tlsv1.1', # استفاده از پروتکل قدیمی‌تر برای دور زدن فیلترهای حساس به TLS 1.3
        '--ciphers', 'DEFAULT@SECLEVEL=1', # کاهش سطح امنیت برای عبور از فایروال
        '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0',
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)
```

---

## ۵. قوانین طلایی برای جلوگیری از مسدودسازی (Fair Use)

فایروال‌های API (مثل BrsApi) به رفتارهای ربات‌گونه بسیار حساس هستند:
1.  **User-Agent ثابت:** همیشه از یک User-Agent مرورگر مدرن (مثل Chrome 131) استفاده کنید.
2.  **تأخیر انسانی (Jitter):** بین درخواست‌ها زمان‌های تصادفی (مثلاً ۱ تا ۳ ثانیه) وقفه بیندازید.
3.  **Cache محلی:** لیست نمادها را در دیتابیس (مثلاً SQLite) ذخیره کنید و هر ۶ ساعت یک بار بروزرسانی کنید تا تعداد کل ریکوئست‌ها کاهش یابد.
4.  **Sequential Access:** درخواست‌ها را پشت سر هم بفرستید (با قفل Threading) تا نرخ درخواست در ثانیه (Rate Limit) بالاتر از حد مجاز نرود.

---

## ۶. چک‌لیست عیب‌یابی (Troubleshooting)

- **خطای 10054:** آی‌پی سرور شما مسدود است -> **راه حل: استفاده از BRIDGE_URL.**
- **خطای 403:** User-Agent شما مسدود شده یا دسترسی گوگل اسکریپت روی Anyone نیست -> **راه حل: اصلاح هدرها یا تنظیمات گوگل.**
- **خطای SSL Error 35:** ناسازگاری لایه TLS با فایروال -> **راه حل: استفاده از tls_client یا متد Native Curl با SECLEVEL=1.**

---
*گردآوری شده برای پروژه TSEAnalysis*
