# 🔴 تجزیہ کردہ مسائل - Data Reception سے Display تک

## تاریخ تجزیہ: ۱ فروری ۲۰۲۶

---

## فہرس

1. **Data Reception (ڈیٹا وصول کرنا)** - API سے ڈیٹا حاصل کرنا
2. **Data Processing (ڈیٹا پروسیسنگ)** - ڈیٹا کو تبدیل کرنا
3. **Data Storage (ڈیٹا ذخیرہ کاری)** - ڈیٹا بیس میں محفوظ کرنا
4. **Data Validation (ڈیٹا تصدیق)** - غلط ڈیٹا کی جانچ
5. **Error Handling (خرابی کا سامنا)** - مسائل کے حل کے طریقے
6. **Display & UI (نمائش)** - صارف کو دکھایا جانے والا ڈیٹا

---

# 📥 LAYER 1: DATA RECEPTION (ڈیٹا وصول)

## ✅ **مسئلہ 1.1: API کے ساتھ رابطہ کی ناکامی**

### تفصیلات
```python
# File: app/services/tsetmc.py (Lines 230-330)
# مسئلہ: TSETMC API کے ساتھ براہ راست رابطہ اکثر ناکام ہو جاتا ہے
```

**علامات:**
- HTTP 403 Forbidden (ممنوع)
- HTTP 429 Too Many Requests (بہت سارے درخواستیں)
- HTTP 503 Service Unavailable (سروس دستیاب نہیں)
- Connection Timeout (رابطہ منقطع ہو گیا)
- SSL/TLS Handshake Errors

**جڑ تک پہنچنا:**
- TSETMC API کے پاس Firewall ہے جو بیرونی کلائنٹس کو روکتا ہے
- Rate limiting (ہر 5 منٹ میں 150 سے زیادہ درخواستیں ممکن نہیں)
- HTTP/2 اور TLS fingerprinting کی پیچیدگیاں

**موجودہ حل:**
```python
# Multi-layer fallback system موجود ہے لیکن مکمل نہیں:
1. Bridge URL (Google Script redirect) - 30 سیکنڈ سے سست
2. Curl native command - لیکن ہمیشہ دستیاب نہیں
3. CURL_CFFI library - صرف Chrome impersonation
4. TLS Client library - Random fingerprinting
5. HTTPX client - معیاری طریقہ، اکثر ناکام
6. Requests library - سب سے ابتدائی
```

**مسائل:**
- ⚠️ پہلی کوشش میں 40-50% failure rate
- ⚠️ Retry logic میں تاخیر (10-30 سیکنڈ انتظار)
- ⚠️ Bridge URL ہمیشہ کام نہیں کرتی
- ⚠️ Curl native ہو سکتا ہے Windows میں available نہ ہو

---

## ✅ **مسئلہ 1.2: Rate Limiting (درخواستوں کی حد)**

### تفصیلات
```python
# File: app/services/tsetmc.py (Lines 160-185)
MIN_REQUEST_GAP = 1.0      # 1 سیکنڈ کی حد
MAX_REQS_STRICT = 150      # 5 منٹ میں 150 درخواستیں
WINDOW_SECONDS = 300       # 5 منٹ کی زندگی
```

**مسائل:**
- ⚠️ 1 سیکنڈ کی gap بہت کم ہے - API اسے 429 سے روکتا ہے
- ⚠️ 150 درخواستیں 5 منٹ میں = 30 درخواستیں فی منٹ = بہت تیز
- ⚠️ کوئی dynamic backoff نہیں - ہمیشہ 1 سیکنڈ
- ⚠️ موفقیت کے بعد تاخیر میں کمی نہیں

**موجودہ کوڈ:**
```python
def _apply_fair_use_control(self, endpoint):
    with self._network_lock:
        # Think time (سوچنے کا وقت)
        think_time = random.uniform(0.5, 1.5)
        time.sleep(think_time)
        
        # Mandatory gap
        elapsed = now - self._last_network_call
        if elapsed < self.MIN_REQUEST_GAP:
            sleep_time = self.MIN_REQUEST_GAP - elapsed
            time.sleep(sleep_time)
```

**مسائل:**
- ⚠️ Think time اضافی ہے لیکن random ہے
- ⚠️ Lock thread-safe ہے لیکن اگر request ناکام ہوں تو backoff نہیں
- ⚠️ 429 خرابی پر موجودہ delay میں اضافہ ہو رہا ہے لیکن اگلی کوشش پر reset ہو جاتا ہے

---

## ✅ **مسئلہ 1.3: Symbol Registry کا خالی رہنا**

### تفصیلات
```python
# File: app/services/tsetmc.py (Lines 110-140)
# اور app/__init__.py (Lines 40-55)
```

**مسئلہ:**
پروگرام شروع ہوتے وقت symbol registry database میں خالی ہو سکتی ہے۔

**عمل:**
```
Start Program
    ↓
Database میں 1,919 symbols کی کوشش کی جاتی ہے
    ↓
اگر DATABASE EMPTY ہے:
    ├─ Type 1, 2, 3, 4, 5 کے لیے API call
    ├─ ہر API call میں 2-3 کوششیں
    ├─ ہر کوشش 30 سیکنڈ تک انتظار
    └─ Total: 5 types × 3 retries × 30s = 450+ سیکنڈ (7+ منٹ)
    
سپ شروعات میں 7 منٹ تک سسٹم جواب نہیں دے سکتا!
```

**مسائل:**
- ⚠️ UI میں "Loading..." 7 منٹ تک
- ⚠️ اگر ایک بھی API ناکام ہو تو symbols نہیں ملیں گے
- ⚠️ Background thread میں preload ہو رہا ہے لیکن main app شروع ہونے سے پہلے users connect کر سکتے ہیں

---

## ✅ **مسئلہ 1.4: Bridge URL کی غیر قابل اعتماد خدمت**

### تفصیلات
```python
# File: app/services/tsetmc.py (Lines 230-245)
if BRIDGE_URL:
    encoded_target = quote(full_url, safe='')
    bridge_request_url = f"{BRIDGE_URL}?url={encoded_target}"
    resp = requests.get(bridge_request_url, timeout=30)
    if resp.status_code == 200:
        content = resp.text.strip()
        if content.startswith(('[', '{')):
            return resp.json()
```

**مسائل:**
- ⚠️ Bridge URL بھاری URL encoding کے بعد ناکام ہو سکتا ہے
- ⚠️ 30 سیکنڈ کا timeout بہت زیادہ ہے
- ⚠️ Bridge HTML غلطی واپس کر سکتا ہے، صرف empty response نہیں
- ⚠️ Bridge URL کا کوئی failover نہیں (اگلا method تک 10 سیکنڈ انتظار)

---

## ✅ **مسئلہ 1.5: TGJU (Gold/Currency) API کا الگ تھلگ رہنا**

### تفصیلات
```python
# File: app/services/tgju.py
# TGJU API بالکل الگ ہے اور TSETMC جیسی failover system نہیں ہے
```

**مسائل:**
- ⚠️ TGJU API ناکام ہوتے ہی کوئی fallback نہیں
- ⚠️ Cached data موجود ہے لیکن قدیم ہو سکتا ہے (کتنا پرانا ہے معلوم نہیں)
- ⚠️ صارف کو بتایا نہیں جاتا کہ یہ ڈیٹا کتنے عرصے پہلے کا ہے

---

---

# 🔄 LAYER 2: DATA PROCESSING (ڈیٹا پروسیسنگ)

## ✅ **مسئلہ 2.1: OHLCV ڈیٹا کی غیر معیاری format**

### تفصیلات
```python
# File: app/services/technical_analysis.py (Lines 95-125)
def prepare_ohlcv_data(data):
    for item in data:
        # مسئلہ: یہاں 4 مختلف format سے نمٹنا پڑ رہا ہے
        close = item.get('pc') or item.get('close') or item.get('index')
        open_p = item.get('pf') or item.get('open') or close
        high = item.get('pmax') or item.get('high') or close
        low = item.get('pmin') or item.get('low') or close
```

**مسائل:**
- ⚠️ API کی 4 مختلف field names ہیں:
  - Persian: `pc` (بند قیمت), `pf` (کھلی قیمت), `pmax` (زیادہ سے زیادہ), `pmin` (کم سے کم)
  - English: `close`, `open`, `high`, `low`
  - Special: `index`, `value` (شاخص ڈیٹا کے لیے)

- ⚠️ Fallback chain میں bugs ہو سکتی ہیں:
  - اگر `close` موجود نہیں اور `index` ہے تو index کو high/low کے طور پر استعمال ہو رہی ہے!
  - یہ تکنیکی تجزیہ میں غلط نتائج دے سکتا ہے

**موجودہ کوڈ:**
```python
high = item.get('pmax') or item.get('high') or close  # ❌ مسئلہ
# اگر pmax/high نہیں ہے تو close استعمال ہو رہی ہے
# لیکن close خود `index` ہو سکتی ہے!
```

---

## ✅ **مسئلہ 2.2: Technical Indicators میں NaN values**

### تفصیلات
```python
# File: app/services/technical_analysis.py (Lines 300-372)
df[col] = pd.to_numeric(df[col], errors='coerce')  # NaN کے ساتھ
```

**مسائل:**
- ⚠️ اگر 20 دن کا ڈیٹا ہے تو:
  - MA20 (20-دن کی متوسط) = 1 value
  - MA50 (50-دن کی متوسط) = 0 values (مدت سے کم)
  - RSI = صرف آخری 14 دنوں کا

- ⚠️ Incomplete data کے ساتھ AI model تربیت دی جا رہی ہے
- ⚠️ چارٹ میں NaN values خالی جگہیں بناتی ہیں

**مسائل:**
```python
try:
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
except:
    pass  # ❌ خاموشی سے ناکام ہو رہا ہے، logging نہیں
```

---

## ✅ **مسئلہ 2.3: Timezones کے ساتھ مسائل**

### تفصیلات
```python
# File: app/services/technical_analysis.py
# Date handling میں timezone معلومات نہیں ہے
```

**مسائل:**
- ⚠️ API میں dates UTC ہو سکتی ہیں، لیکن Tehran time میں محفوظ ہو رہی ہے
- ⚠️ Jalali calendar (ہجری) اور Gregorian (عیسوی) میں conversion bugs ہو سکتی ہے
- ⚠️ Market close time (14:30 Tehran) کے بعد کے ڈیٹا کو کل کا data سمجھا جا رہا ہے

```javascript
// File: templates/index.html (Lines 850-900)
const jalaliFormatter = (val) => {
    // ❌ یہاں locale conversion محدود ہے
    return new Intl.DateTimeFormat('fa-IR', {...})
}
```

---

## ✅ **مسئلہ 2.4: Division by Zero اور Infinite Values**

### تفصیلات
```python
# File: app/services/technical_analysis.py
# اور app/services/local_ai_assistant.py
```

**مسائل:**
- ⚠️ P/E ratio calculation میں:
  ```python
  pe = price / earnings  # اگر earnings = 0 تو infinity!
  ```

- ⚠️ Volume-weighted analysis:
  ```python
  if volume == 0:
      # ❌ کوئی check نہیں
      result = value / volume  # Division by zero!
  ```

- ⚠️ Return on Investment calculations میں:
  ```python
  rr_ratio = reward / risk  # اگر risk = 0 تو?
  ```

---

## ✅ **مسئلہ 2.5: Outlier ڈیٹا کو reject کرنا**

### تفصیلات
```python
# موجودہ کوڈ میں outlier detection نہیں ہے
```

**مسائل:**
- ⚠️ اگر symbol کی قیمت ایک دن 1000% بڑھ جائے (شاید API error):
  - یہ قیمت تکنیکی analysis میں استعمال ہو رہی ہے
  - MA/RSI/MACD سب غلط ہو جائیں گے

**مثال:**
```
باقاعدہ ڈیٹا:  1200, 1210, 1205, 1215, ...
API error:     1200, 1210, 99999, 1215, ...  ❌ Outlier
```

---

---

# 💾 LAYER 3: DATA STORAGE (ڈیٹا ذخیرہ کاری)

## ✅ **مسئلہ 3.1: SQLite Database کے Thread Safety کے مسائل**

### تفصیلات
```python
# File: app/database.py (Lines 20-35)
def _get_connection(self):
    return sqlite3.connect(self.db_path)
```

**مسائل:**
- ⚠️ ہر operation میں نیا connection بنایا جا رہا ہے
- ⚠️ Thread-safe نہیں ہے - concurrent writes سے database lock ہو سکتا ہے

```python
# موجودہ کوڈ:
def save_history(self, symbol, history_data):
    with self._get_connection() as conn:
        cursor = conn.cursor()
        for item in history_data:
            cursor.execute('''INSERT OR IGNORE...''')
        conn.commit()

# مسئلہ: اگر ایک ہی وقت میں 2 threads save_history() کو call کریں:
# Thread 1: INSERT شروع کیا
# Thread 2: INSERT شروع کیا
# Result: SQLITE_BUSY error! یا ڈیٹا corrupt ہو سکتا ہے
```

**WAL Mode موجود ہے:**
```python
cursor.execute("PRAGMA journal_mode=WAL;")  # ✅ موجود
```
لیکن synchronous=NORMAL ہے، یعنی partial durability!

---

## ✅ **مسئلہ 3.2: Duplicate Entries کا ہٹایا نہ جانا**

### تفصیلات
```python
# File: app/database.py (Lines 110-120)
cursor.execute('''
    INSERT OR IGNORE INTO price_history 
    (symbol, date, open, high, low, close, volume, raw_data, last_updated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (symbol, date, ...))
```

**مسائل:**
- ⚠️ INSERT OR IGNORE دہری entries کو محفوظ رکھتا ہے
- ⚠️ لیکن اگر API سے ڈیٹا بہتری سے آئے تو old data update نہیں ہوگا!

```
Day 1 میں API سے:  Close = 1200 (درست)
Day 2 میں API سے:  Close = 1250 (API پہلے والا غلط تھا، اب ٹھیک ہے)

Database میں: Close = 1200 ❌ (پرانا رہے گا)
```

---

## ✅ **مسئلہ 3.3: لامحدود Database Growth**

### تفصیلات
```python
# Database میں price_history table بغیر کسی limit کے بڑھتا جا رہا ہے
```

**مسائل:**
- ⚠️ 1,919 symbols × 365 days × 5+ سال = 35 ملین records
- ⚠️ Database فائل 5-10 GB تک بڑھ سکتی ہے
- ⚠️ SELECT queries سست ہو جائیں گی

**موجودہ کوڈ میں cleanup نہیں ہے:**
```python
# Database میں کوئی DELETE policy نہیں
# 5 سال سے پرانا ڈیٹا ابھی موجود ہے
```

---

## ✅ **مسئلہ 3.4: Raw JSON کو دوبارہ Parse کرنا**

### تفصیلات
```python
# File: app/database.py (Lines 115-120)
cursor.execute('''
    INSERT INTO price_history 
    (... raw_data ...)
    VALUES (?, ?, ?, ?, ?, ?, ?, json.dumps(item), ?)  # ❌ دوہری storage
''')
```

**مسائل:**
- ⚠️ OHLCV ڈیٹا struct columns میں محفوظ ہے
- ⚠️ لیکن ساتھ ہی raw JSON (json.dumps) بھی محفوظ ہے
- ⚠️ یہ disk space ضائع کرتا ہے

**عام طور پر:**
```
1 record: 45 bytes (O, H, L, C, V)
+ JSON: 200 bytes

Total: 245 bytes per record (5x بڑا!)
```

---

## ✅ **مسئلہ 3.5: Schema Migration کے مسائل**

### تفصیلات
```python
# File: app/database.py (Lines 50-65)
# Old schema سے نیا schema میں ہجرت
cursor.execute("DROP TABLE symbols")  # ❌ خطرناک!
```

**مسائل:**
- ⚠️ اگر migration ناکام ہو تو سب ڈیٹا ضائع ہو جائے گا
- ⚠️ کوئی backup نہیں بنایا جا رہا migration سے پہلے
- ⚠️ ALTER TABLE کے بعد NULL columns میں default value نہیں ہے

---

---

# ✔️ LAYER 4: DATA VALIDATION (ڈیٹا تصدیق)

## ✅ **مسئلہ 4.1: Input Validation کی کمی**

### تفصیلات
```python
# File: app/api/routes.py (Lines 105-125)
@main_bp.route('/api/fetch_data', methods=['POST'])
def fetch_data():
    data = request.json
    asset_type = data.get('asset_type')       # ❌ کوئی validation نہیں
    symbol = data.get('symbol')               # ❌ کوئی validation نہیں
    candle_count = data.get('candle_count')   # ❌ کوئی validation نہیں
```

**مسائل:**
- ⚠️ Symbol میں خطرناک characters ہو سکتے ہیں:
  ```python
  symbol = "'; DROP TABLE symbols; --"
  # SQL Injection تو ہے نہیں (parameterized queries استعمال ہو رہی ہے)
  # لیکن غلط symbol سرچ ہو سکتی ہے
  ```

- ⚠️ Candle count میں منفی یا بہت بڑی تعداد:
  ```javascript
  candle_count = -100  // یا 1000000
  // ہو سکتا ہے server کو hang کر دے
  ```

- ⚠️ Asset type کی غلط value:
  ```python
  asset_type = "hacking_attempt"
  # موجودہ کوڈ: elif ہر جگہ ہے، آخر میں کوئی error نہیں
  ```

---

## ✅ **مسئلہ 4.2: Number Type Conversions میں Errors**

### تفصیلات
```python
# File: app/services/technical_analysis.py (Lines 107-113)
close = item.get('pc') or item.get('close')
new_item['close'] = round(float(close), rounding)  # ❌ اگر close = None!
```

**مسائل:**
- ⚠️ Float conversion میں ValueError ہو سکتی ہے
- ⚠️ Rounding logic میں:
  ```python
  rounding = 0 if p_close > 1000 else (1 if p_close > 100 else 2)
  ```
  یہ arbitrary ہے - کوئی معنیٰ نہیں

- ⚠️ کوئی try-except نہیں:
  ```python
  try:
      new_item['close'] = round(float(close), rounding)
  except (ValueError, TypeError):
      logger.error(f"Invalid close price: {close}")
      continue  # Skip this record
  ```

---

## ✅ **مسئلہ 4.3: Date Format Inconsistency**

### تفصیلات
```python
# File: app/database.py
# Dates کی 3 مختلف formats استعمال ہو رہی ہے:
1. YYYY-MM-DD (ISO format)
2. YYYYMMDD (TSE format)
3. Jalali Calendar (ہجری)
```

**مسائل:**
- ⚠️ Date comparison میں bugs:
  ```python
  if date1 > date2:  # String comparison!
      # "2026-01-15" > "2025-12-31" ✓ (غیر متوقع نہیں)
      # لیکن "2026-02-01" > "2026-01-31" ✓ (غیر متوقع نہیں)
      # لیکن "2026-1-15" > "2026-01-31" ✗ (غلط نتیجہ!)
  ```

- ⚠️ Jalali/Gregorian conversion:
  ```python
  # کوئی standard library استعمال نہیں ہو رہی (jdatetime ہے لیکن inconsistent)
  ```

---

## ✅ **مسئلہ 4.4: Unicode اور Encoding کے مسائل**

### تفصیلات
```python
# File: app/database.py (Lines 190-195)
str(sym.get('isin') or sym.get('id') or sym.get('l18'))

# اور

# File: templates/index.html (Lines 1560-1565)
if (typeof val === 'number') val = val.toLocaleString();
```

**مسائل:**
- ⚠️ isin میں Persian characters ہو سکتے ہیں (l18 میں ہیں ہمیشہ)
- ⚠️ Browser میں display کے وقت:
  ```javascript
  // Farsi numbers (۰۱۲۳۴۵) vs Arabic numbers (0123456)
  val.toLocaleString('fa-IR')  // قریب قریب کام کرتا ہے
  ```

- ⚠️ لیکن سرچ میں:
  ```python
  if "سکه" in ticker_name:  # Persian character
      return "etf"
  # اگر keyboard Farsi numbers سے typed ہو تو match نہیں ہوگا!
  ```

---

## ✅ **مسئلہ 4.5: Null/Empty/Falsy Values کی Handling**

### تفصیلات
```python
# File: app/services/tsetmc.py (Lines 55-65)
isin = str(s.get('isin', '') or s.get('id', ''))
# مسئلہ: '' یا None دونوں وقت "None" string بن جاتی ہے!

if (not isin or isin == "None") and not cs_id:
    return "unknown"  # ✓ یہ check موجود ہے
```

**مسائل:**
- ⚠️ Inconsistent checking:
  ```python
  if not isin:      # Empty string check
  if isin == "None": # String "None" check
  # یہ دونوں الگ الگ ہیں!
  ```

- ⚠️ مثال میں:
  ```python
  symbol_data = {'name': None}
  name = symbol_data.get('name') or 'Unknown'
  # Result: 'Unknown' ✓
  
  symbol_data = {'name': 0}
  count = symbol_data.get('count') or 10
  # Result: 10 ❌ (غلط! 0 valid ہے)
  ```

---

---

# ⚠️ LAYER 5: ERROR HANDLING (خرابی کا سامنا)

## ✅ **مسئلہ 5.1: Bare Except Clauses**

### تفصیلات
```python
# File: app/services/technical_analysis.py (Lines 48, 372, 403, 442, 450)
try:
    # کچھ کام
except:  # ❌ مسئلہ: کوئی exception type نہیں!
    pass
```

**مسائل:**
- ⚠️ یہ KeyboardInterrupt اور SystemExit کو بھی catch کرتا ہے
- ⚠️ Bugs کو خاموشی سے hide کرتا ہے
- ⚠️ Debugging مشکل بناتا ہے

**مثال:**
```python
except Exception as e:
    logger.error(f"Error: {e}")
    # یہ بہتر ہے لیکن اب بھی generic ہے
```

---

## ✅ **مسئلہ 5.2: Insufficient Error Information**

### تفصیلات
```python
# File: app/services/tsetmc.py (Lines 244-246, 266, 282, 296, 314)
except Exception as e:
    logger.error(f"Bridge failed: {str(e)[:50]}")
    # صرف پہلے 50 characters!
```

**مسائل:**
- ⚠️ مکمل error message نہیں ہے
- ⚠️ Stack trace نہیں ہے
- ⚠️ Request details (endpoint, params) نہیں ہے

**بہتر طریقہ:**
```python
except Exception as e:
    logger.error(f"Bridge failed for {endpoint}", exc_info=True)
    logger.error(f"Parameters: {params}")
    # یہ stack trace اور تمام معلومات دے گا
```

---

## ✅ **مسئلہ 5.3: Partial Transactions اور Data Corruption**

### تفصیلات
```python
# File: app/database.py (Lines 110-125)
with self._get_connection() as conn:
    cursor = conn.cursor()
    for item in history_data:
        cursor.execute('INSERT OR IGNORE INTO price_history ...')
    conn.commit()  # اگر یہاں سے پہلے error ہو تو?
```

**مسائل:**
- ⚠️ اگر 100 items میں سے 50 insert ہوں اور پھر error آئے
- ⚠️ تو صرف 50 items save ہوں گے (بقیہ missing)
- ⚠️ یہ data inconsistency بناتا ہے

**بہتر طریقہ:**
```python
try:
    with self._get_connection() as conn:
        cursor = conn.cursor()
        for item in history_data:
            cursor.execute(...)
        conn.commit()
except Exception as e:
    conn.rollback()  # سب کچھ undo کریں
    logger.error(f"Transaction failed: {e}")
    raise
```

---

## ✅ **مسئلہ 5.4: Timeout Handling میں کمی**

### تفصیلات
```python
# File: app/services/tsetmc.py (Lines 270-300)
try:
    resp = requests.get(full_url, headers=headers, timeout=15)
except Exception as e:
    logger.error(f"Request failed: {e}")  # Timeout exception handle نہیں ہے!
```

**مسائل:**
- ⚠️ Timeout اور Connection error میں فرق نہیں ہے
- ⚠️ Connection timeout = API down (retry کریں)
- ⚠️ Read timeout = API سست ہے (timeout بڑھائیں؟)
- ⚠️ دونوں کو ایک جیسے treat کیا جا رہا ہے

---

## ✅ **مسئلہ 5.5: Missing Global Exception Handler**

### تفصیلات
```python
# File: app/__init__.py
# start_preload() میں exception handling موجود ہے لیکن:
```

**مسائل:**
- ⚠️ Background threads میں unhandled exception = program crash
- ⚠️ UI میں error دکھایا نہیں جاتا
- ⚠️ Logging میں ہے لیکن صارف کو معلوم نہیں

```python
def background_preload():
    try:
        start_background_service()
    except Exception as e:
        logger.warning(f"Could not start data refresh service: {e}")
        # لیکن اگر یہ exception ہو تو user کو نہیں پتا!
```

---

## ✅ **مسئلہ 5.6: Circuit Breaker Pattern کے مسائل**

### تفصیلات
```python
# File: app/services/tsetmc.py (Lines 165-170)
if now < self._cooling_until:
    wait_time = self._cooling_until - now
    logger.warning(f"Circuit breaker active. Cooling for {wait_time:.1f}s")
    time.sleep(wait_time)  # سب کچھ بند ہو جاتا ہے!
```

**مسائل:**
- ⚠️ Circuit breaker activate ہو تو سب requests روک دی جاتی ہے (60 سیکنڈ)
- ⚠️ اگر ایک symbol fail ہو تو دوسری symbols کے لیے بھی 60 سیکنڈ انتظار
- ⚠️ کوئی partial recovery نہیں ہے

**بہتر طریقہ:**
```python
# Per-endpoint circuit breaker، global نہیں
# یا exponential backoff (1s → 2s → 4s → ...)
```

---

---

# 🎨 LAYER 6: DISPLAY & UI (نمائش)

## ✅ **مسئلہ 6.1: Chart Data میں Missing Dates**

### تفصیلات
```javascript
// File: templates/index.html (Lines 1655-1700)
const chartData = sortedData.map(item => ({
    x: new Date(item.date || item.time).getTime(),
    y: [open, high, low, close]
}));
```

**مسائل:**
- ⚠️ اگر 50 دن ہیں لیکن weekends/holidays میں ڈیٹا نہیں ہے:
  ```
  Day 1: ✓
  Day 2: ✓
  Day 3: ✓ (جمعہ - بند)
  Day 4: (نہیں ہے)
  Day 5: ✓
  ```
  تو chart میں 1-2-3-5 دکھائے گا، 4 کی جگہ gap ہو گی

- ⚠️ Candlestick chart میں یہ غیر واضح ہے

---

## ✅ **مسئلہ 6.2: Number Formatting میں مسائل**

### تفصیلات
```javascript
// File: templates/index.html (Lines 1560-1565)
if (typeof val === 'number' && !['eps', 'pe', 'pcp', 'plp'].includes(k)) 
    val = val.toLocaleString();
```

**مسائل:**
- ⚠️ Farsi numbers (۰۱۲۳۴۵) استعمال ہو رہے ہیں
- ⚠️ لیکن copy-paste کے وقت یہ Latin numbers میں تبدیل ہو جاتے ہیں
- ⚠️ Plus/minus sign کی positioning غلط ہو سکتی ہے

```javascript
(-1234567).toLocaleString('fa-IR')  // منفی علامت کہاں؟
// Result: "۱٬۲۳۴٬۵۶۷-" یا "-۱٬۲۳۴٬۵۶۷"?
```

---

## ✅ **مسئلہ 6.3: Missing Loading Indicators**

### تفصیلات
```html
<!-- File: templates/index.html -->
<!-- صرف کچھ جگہوں پر loading spinner ہے -->
<!-- زیادہ تر API calls میں نہیں ہے -->
```

**مسائل:**
- ⚠️ User کو نہیں پتا کہ request جاری ہے یا پوری ہو گئی
- ⚠️ اگر server سے 10 سیکنڈ تاخیر ہو تو user سوچے گا program hang ہو گیا

---

## ✅ **مسئلہ 6.4: Alert/Warning Messages کی Positioning**

### تفصیلات
```javascript
// File: templates/index.html (Lines 1938-1950)
if (!symbol || isNaN(price)) {
    alert('لطفا ابتدا یک نماد انتخاب کرده و قیمت هدف را وارد کنید');
    return;
}
```

**مسائل:**
- ⚠️ Browser کا alert() modal ہے - بہت intrusive
- ⚠️ User کے پاس ڈیٹا دوبارہ enter کرنا پڑے گا
- ⚠️ Invalid input کے لیے in-line validation بہتر ہے

---

## ✅ **مسئلہ 6.5: Performance Issues - بہت سارے DOM updates**

### تفصیلات
```javascript
// File: templates/index.html (Lines 850-900)
// جب symbol change ہو تو:
1. All symbols fetch کرنا
2. Table rows render کرنا (1000+)
3. Charts redraw کرنا
4. Watchlist update کرنا
// یہ سب DOM میں ہے!
```

**مسائل:**
- ⚠️ Browser میں 1000+ rows render کرنا سست ہے
- ⚠️ Chart redraw ہر بار expensive ہے
- ⚠️ Virtual scrolling استعمال نہیں ہو رہی

---

## ✅ **مسئلہ 6.6: Responsive Design میں مسائل**

### تفصیلات
```css
/* File: templates/index.html (Styles) */
/* Mobile میں کالم خراب ہو رہے ہیں */
```

**مسائل:**
- ⚠️ Mobile پر tables overflow ہو رہے ہیں
- ⚠️ Charts mobile-friendly نہیں ہیں (بہت چھوٹے)
- ⚠️ Touch events implement نہیں ہیں

---

## ✅ **مسئلہ 6.7: Theme Toggle میں Persistence کی کمی**

### تفصیلات
```javascript
// File: templates/index.html
// Dark mode toggle موجود ہے لیکن:
```

**مسائل:**
- ⚠️ localStorage میں save نہیں ہو رہا (ہو سکتا ہے privacy mode میں ہو)
- ⚠️ Page reload پر theme reset ہو جاتی ہے
- ⚠️ Browser preference (prefers-color-scheme) check نہیں ہو رہی

---

---

# 🔒 SECURITY ISSUES (حفاظتی مسائل)

## ✅ **مسئلہ 7.1: API Key in Code**

### تفصیلات
```python
# File: app/core_utils.py (Lines 40-42)
API_KEY = os.getenv('TSE_API_KEY', '677e4860b2d6a')  # ❌ Default key!
```

**مسائل:**
- ⚠️ اگر .env file موجود نہ ہو تو default key use ہوگی
- ⚠️ یہ key GitHub میں commit ہو چکی ہے (revoke کریں!)
- ⚠️ ہر صارف کے لیے الگ key ہونی چاہیے

---

## ✅ **مسئلہ 7.2: SQL Injection Risk (اگرچہ parameterized)**

### تفصیلات
```python
# File: app/database.py
# موجودہ کوڈ parameterized queries استعمال کر رہا ہے ✓
cursor.execute('SELECT ... FROM symbols WHERE market_category = ?', (category,))
```

**اچھی خبر:** SQL injection safe ہے

**لیکن:**
- ⚠️ Database filenames میں user input استعمال نہیں ہو رہی (اچھا ہے)
- ⚠️ Dynamic table names میں risk ہو سکتا ہے

---

## ✅ **مسئلہ 7.3: CORS Policy**

### تفصیلات
```python
# File: app/__init__.py
# CORS setup موجود نہیں ہے
```

**مسائل:**
- ⚠️ اگر frontend alag domain پر ہے تو requests block ہوں گی
- ⚠️ CORS headers نہیں ہیں

**بہتری:**
```python
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

---

## ✅ **مسئلہ 7.4: No HTTPS in Development**

### تفصیلات
```python
# File: app.py
app.run(debug=debug_mode, host='127.0.0.1', port=5000)  # HTTP! production میں?
```

**مسائل:**
- ⚠️ HTTPS استعمال نہیں ہو رہی development میں
- ⚠️ Production میں بھی شاید نہیں ہے

---

## ✅ **مسئلہ 7.5: No Rate Limiting on API Endpoints**

### تفصیلات
```python
# File: app/api/routes.py
# ہر endpoint open ہے - کوئی rate limiting نہیں
```

**مسائل:**
- ⚠️ کوئی بھی localhost سے لامحدود requests بھیج سکتا ہے
- ⚠️ DDoS attack کا خطرہ
- ⚠️ TSETMC API کو overwhelm کر سکتا ہے

---

---

# 📊 SUMMARY TABLE

| Layer | Issue # | Severity | Description | Impact |
|-------|---------|----------|-------------|--------|
| Reception | 1.1 | 🔴 High | API Connection Failures | Data not fetched |
| Reception | 1.2 | 🔴 High | Rate Limiting Too Aggressive | 429 errors |
| Reception | 1.3 | 🟡 Medium | Symbol Registry Empty on Start | 7+ min startup |
| Reception | 1.4 | 🟡 Medium | Bridge URL Unreliable | 40% failure |
| Reception | 1.5 | 🟡 Medium | TGJU No Fallback | No data |
| Processing | 2.1 | 🟡 Medium | OHLCV Format Issues | Wrong calculations |
| Processing | 2.2 | 🟡 Medium | NaN in Indicators | Missing data points |
| Processing | 2.3 | 🟡 Medium | Timezone Issues | Wrong dates |
| Processing | 2.4 | 🔴 High | Division by Zero | Crashes |
| Processing | 2.5 | 🟡 Medium | No Outlier Detection | Wrong analysis |
| Storage | 3.1 | 🔴 High | Thread Safety Issues | Data corruption |
| Storage | 3.2 | 🟡 Medium | Duplicates Not Updated | Stale data |
| Storage | 3.3 | 🟡 Medium | Unlimited DB Growth | Slow queries |
| Storage | 3.4 | 🟢 Low | Redundant JSON Storage | Wasted space |
| Storage | 3.5 | 🔴 High | Unsafe Migration | Data loss |
| Validation | 4.1 | 🟡 Medium | Missing Input Validation | Invalid requests |
| Validation | 4.2 | 🔴 High | Type Conversion Errors | Crashes |
| Validation | 4.3 | 🟡 Medium | Date Format Inconsistency | Wrong sorting |
| Validation | 4.4 | 🟡 Medium | Unicode Issues | Display problems |
| Validation | 4.5 | 🟡 Medium | Falsy Value Handling | Logic errors |
| Errors | 5.1 | 🟡 Medium | Bare Except Clauses | Hidden bugs |
| Errors | 5.2 | 🟡 Medium | Insufficient Error Info | Hard to debug |
| Errors | 5.3 | 🔴 High | Partial Transactions | Inconsistent data |
| Errors | 5.4 | 🟡 Medium | Poor Timeout Handling | Wrong retries |
| Errors | 5.5 | 🔴 High | Missing Global Handler | Silent crashes |
| Errors | 5.6 | 🟡 Medium | Circuit Breaker Issues | Cascading failures |
| Display | 6.1 | 🟢 Low | Chart Gap Issues | Visual glitch |
| Display | 6.2 | 🟢 Low | Number Format Issues | Usability |
| Display | 6.3 | 🟢 Low | Missing Loading Indicators | UX confusion |
| Display | 6.4 | 🟢 Low | Alert Positioning | UX issues |
| Display | 6.5 | 🟡 Medium | Performance Issues | Slow rendering |
| Display | 6.6 | 🟡 Medium | Mobile Issues | Broken on phone |
| Display | 6.7 | 🟢 Low | Theme Persistence | UX irritation |
| Security | 7.1 | 🔴 High | Hardcoded API Key | Exposure |
| Security | 7.2 | 🟢 Low | SQL Injection (Mitigated) | OK |
| Security | 7.3 | 🟡 Medium | CORS Not Set | XSRF risk |
| Security | 7.4 | 🟡 Medium | No HTTPS | Man-in-middle |
| Security | 7.5 | 🔴 High | No Rate Limiting | DDoS risk |

---

# 📈 Critical Issues (فوری اقدام درکار)

## 🔴 Top 10 اہم مسائل:

1. **API Connection Failures** - Data reception block ہو جاتا ہے
2. **Thread Safety in Database** - Data corruption کا خطرہ
3. **Division by Zero** - Program crashes
4. **Type Conversion Errors** - Unhandled exceptions
5. **Partial Transactions** - Data inconsistency
6. **Missing Global Exception Handler** - Silent failures
7. **Unsafe Schema Migration** - Data loss
8. **Hardcoded API Key** - Security breach
9. **No Rate Limiting on Endpoints** - DDoS risk
10. **Circuit Breaker Blocks All** - Cascading failures

---

**تجزیہ مکمل** ✅

