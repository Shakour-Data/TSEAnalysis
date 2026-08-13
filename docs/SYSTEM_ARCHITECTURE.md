# 🗺️ سیستم آپدیت - نقشه معماری و جریان داده

## معماری کلی

```
┌─────────────────────────────────────────────────────────────┐
│                      Flask Application                      │
│                   (app/__init__.py)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│  API Endpoints   │    │  Incremental Updater │
│ (routes.py)      │    │ (incremental_updater │
│                  │    │   .py)               │
│ /status          │    │                      │
│ /progress        │    │  - Daily loop        │
│ /failed          │    │  - Progress tracking │
│ /start   (POST)  │    │  - Retry logic       │
│ /stop    (POST)  │    │  - Health scoring    │
│ /resume  (POST)  │    │                      │
└──────────────────┘    └──────────┬───────────┘
        ▲                          │
        │                          │
        │              ┌───────────┴──────────┐
        │              │                      │
        │              ▼                      ▼
        │       ┌──────────────┐    ┌──────────────┐
        │       │Rate Limiter  │    │   Database   │
        │       │(rate_limiter │    │   Service    │
        │       │  .py)        │    │ (database.py)│
        │       │              │    │              │
        │       │- Backoff     │    │- SQLite      │
        │       │- Delay mgmt  │    │- 1,919 symbols
        │       │- Error handle│    │- ~96k records│
        │       └──────────────┘    └──────────────┘
        │                                    ▲
        │                                    │
        └────────────────────────────────────┘
                    Progress JSON
            (data/update_progress.json)
```

---

## جریان داده در هر روز

```
🌅 صبح
│
├─ 1️⃣ Load Progress
│      └─ data/update_progress.json
│         ├─ Previous: 900/1919 symbols
│         └─ Failed: [list of 10 symbols]
│
├─ 2️⃣ Calculate Quota
│      └─ Daily: 100 symbols
│         ├─ Pending: 1019 symbols
│         ├─ Failed: 10 symbols
│         └─ Today: 100 new + retry failures
│
├─ 3️⃣ Update Loop Starts
│      └─ For each symbol:
│         ├─ Check rate limit
│         ├─ Call TSETMC API
│         ├─ Save to DB
│         └─ Log progress
│
├─ 4️⃣ Handle Errors
│      ├─ 429 (Rate Limited)?
│      │  └─ Increase delay (2s → 4s → 8s)
│      │
│      ├─ 503 (Service Unavailable)?
│      │  └─ Retry with backoff
│      │
│      └─ Other error?
│         └─ Save to failed list, retry tomorrow
│
├─ 5️⃣ Save Progress
│      └─ data/update_progress.json
│         ├─ Updated: 1000/1919 (52%)
│         ├─ Failed: 15
│         ├─ Daily quota: 100/100
│         └─ Days left: 10
│
└─ 🌆 شام
   └─ Continue tomorrow same process
      OR manual stop via API
```

---

## حالت‌های سیستم

```
┌─────────────┐
│   IDLE      │ (منتظر) - شروع نشده
└────┬────────┘
     │ /api/updates/start (POST)
     ▼
┌──────────────┐
│   RUNNING    │ (در حال اجرا) - آپدیت جاری
└────┬─────────┘
     │ /api/updates/stop (POST)
     ▼
┌──────────────┐
│   STOPPED    │ (متوقف) - قابل ادامه
└────┬─────────┘
     │ /api/updates/resume (POST)
     ▼
    back to RUNNING

┌─────────────┐
│  COMPLETED  │ (تکمیل) - تمام 1919 نماد آپدیت شد!
└─────────────┘
```

---

## جریان Retry برای Failures

```
Symbol: عیار

❌ Try 1 (Day 1, 20:05:00)
   └─ API Error: 503 Service Unavailable
   └─ Delay: 2s
   └─ Save to failed list
   
⏳ Waiting...

❌ Try 2 (Day 2, 20:01:00)
   └─ API Error: 403 Forbidden
   └─ Delay: 4s
   └─ Still failed
   
⏳ Waiting...

❌ Try 3 (Day 3, 20:02:00)
   └─ API Error: Connection timeout
   └─ Delay: 8s
   └─ Max retries reached
   
📝 Permanent Failure?
   └─ Log and skip
   └─ Manual review required

✅ Success (Alternate: Day 2 or 3)
   └─ 100 new records saved
   └─ Move to successful
   └─ Remove from failed list
```

---

## نقاط اتصال API

```
1. Get Status
   ┌─────────────────────────────────────┐
   │ GET /api/updates/status             │
   ├─────────────────────────────────────┤
   │ Response: {                         │
   │   "status": "RUNNING",              │
   │   "message": "Updating...",         │
   │   "current_symbol": "عیار",        │
   │   "current_count": 50,              │
   │   "daily_quota": 100                │
   │ }                                   │
   └─────────────────────────────────────┘

2. Get Progress
   ┌─────────────────────────────────────┐
   │ GET /api/updates/progress           │
   ├─────────────────────────────────────┤
   │ Response: {                         │
   │   "percentage": 52.5,               │
   │   "updated": 1009,                  │
   │   "failed": 15,                     │
   │   "total": 1919,                    │
   │   "pending": 910,                   │
   │   "days_left": 10,                  │
   │   "daily_quota": 100                │
   │ }                                   │
   └─────────────────────────────────────┘

3. Get Failed Symbols
   ┌─────────────────────────────────────┐
   │ GET /api/updates/failed             │
   ├─────────────────────────────────────┤
   │ Response: {                         │
   │   "failed": [                       │
   │     {"symbol": "عیار", "tries": 2}, │
   │     {"symbol": "وبملت", "tries": 1} │
   │   ],                                │
   │   "total_failed": 15                │
   │ }                                   │
   └─────────────────────────────────────┘

4. Start Update
   ┌─────────────────────────────────────┐
   │ POST /api/updates/start             │
   ├─────────────────────────────────────┤
   │ Response: {                         │
   │   "status": "STARTED",              │
   │   "message": "Update cycle started" │
   │ }                                   │
   └─────────────────────────────────────┘

5. Stop Update
   ┌─────────────────────────────────────┐
   │ POST /api/updates/stop              │
   ├─────────────────────────────────────┤
   │ Response: {                         │
   │   "status": "STOPPED",              │
   │   "message": "Update paused"        │
   │ }                                   │
   └─────────────────────────────────────┘

6. Resume Update
   ┌─────────────────────────────────────┐
   │ POST /api/updates/resume            │
   ├─────────────────────────────────────┤
   │ Response: {                         │
   │   "status": "RUNNING",              │
   │   "message": "Update resumed"       │
   │ }                                   │
   └─────────────────────────────────────┘
```

---

## فلوچارت سیستم کامل

```
START
  │
  ├─ Load Configuration
  │  └─ symbols_per_day: 100
  │  └─ max_retries: 3
  │  └─ base_delay: 2s
  │
  ├─ Initialize Database
  │  └─ Get all 1,919 symbols
  │  └─ Load update_progress.json
  │
  ├─ Start Background Thread
  │  └─ Daily loop at 20:00 (configurable)
  │
  ├─ Listen for API Requests
  │  ├─ /status → Return current state
  │  ├─ /progress → Calculate and return %
  │  ├─ /failed → List failed symbols
  │  ├─ /start → Trigger update
  │  ├─ /stop → Pause update
  │  └─ /resume → Resume update
  │
  └─ Main Loop (runs daily)
     │
     ├─ [20:00] Check if RUNNING?
     │  └─ NO → Wait
     │  └─ YES → Continue
     │
     ├─ Load previous progress
     │  └─ Updated: 900
     │  └─ Failed: [list]
     │  └─ Pending: 1019
     │
     ├─ Calculate today's batch
     │  ├─ Take 100 pending symbols
     │  └─ + retry failed symbols
     │
     ├─ For each symbol: UPDATE_SYMBOL()
     │  ├─ Check rate limit
     │  ├─ Call API
     │  ├─ Save result
     │  └─ Update counter
     │
     ├─ Handle Errors
     │  ├─ Retry? (< max_retries)
     │  │  └─ Add to failed list
     │  │  └─ Increase delay
     │  │
     │  └─ Skip? (>= max_retries)
     │     └─ Log permanent failure
     │
     ├─ Save Progress
     │  └─ Write update_progress.json
     │
     ├─ Check if Complete?
     │  ├─ updated + pending == 0?
     │  │  └─ YES → Mark COMPLETED
     │  │  └─ NO → Continue tomorrow
     │  │
     │  └─ Wait 24 hours
     │
     └─ Loop back to [20:00]

END (when all symbols updated OR manually stopped)
```

---

## فلوچارت تک‌نماد

```
UPDATE_SYMBOL(symbol_code):
  │
  ├─ 1. Get last update date
  │  └─ Query database
  │  └─ Calculate days since last update
  │
  ├─ 2. Check if needs update
  │  ├─ Never updated? → YES
  │  ├─ < 7 days ago? → NO
  │  └─ >= 7 days ago? → YES
  │
  ├─ 3. Call API
  │  ├─ Wait rate limit (2s, 4s, 8s, ...)
  │  │
  │  ├─ Try to fetch
  │  │  ├─ Success (200) → Save data, return TRUE
  │  │  │
  │  │  ├─ Not Found (404) → Log, return FALSE
  │  │  │
  │  │  ├─ Rate Limited (429) → Increase delay, retry
  │  │  │
  │  │  ├─ Service Error (503) → Exponential backoff, retry
  │  │  │
  │  │  ├─ Forbidden (403) → Use cache, retry later
  │  │  │
  │  │  └─ Other error → Add to failed list
  │
  ├─ 4. Save to Database
  │  ├─ DELETE old records
  │  ├─ INSERT new records (50-100)
  │  └─ UPDATE last_update timestamp
  │
  ├─ 5. Log Result
  │  └─ [✓] Symbol: 100 records
  │  └─ OR [✗] Symbol: Error
  │
  └─ RETURN success status
```

---

## جدول تغییرات Delay

```
Attempt 1: Delay = 2.0s
Attempt 2: Delay = 2.0 × 2 = 4.0s
Attempt 3: Delay = 4.0 × 2 = 8.0s
Attempt 4: Delay = 8.0 × 2 = 16.0s (max)

نمونه تایم‌لاین:
20:00:00 - Try 1 (delay 2s before)
20:00:02 - Try 2 (delay 4s before)
20:00:06 - Try 3 (delay 8s before)
20:00:14 - Finally success OR failed
```

---

## کنترل پیشرفت

```
update_progress.json
│
├─ percentage: 52.5%
├─ updated: 1009 symbols
├─ failed: 15 symbols
├─ total: 1919 symbols
├─ pending: 910 symbols
├─ days_left: 10 days
├─ daily_quota: 100 symbols
│
├─ daily_progress:
│  ├─ 2026-01-31:
│  │  ├─ target: 100
│  │  ├─ actual: 95
│  │  ├─ failed: 5
│  │  └─ updated_symbols: [وبملت, عیار, ...]
│  │
│  └─ 2026-02-01:
│     ├─ target: 100
│     ├─ actual: 0 (still running)
│     ├─ failed: 0
│     └─ updated_symbols: []
│
├─ failed_symbols:
│  ├─ {symbol: عیار, tries: 2, last_error: 503}
│  ├─ {symbol: وبملت, tries: 1, last_error: timeout}
│  └─ ...
│
└─ metadata:
   ├─ started_at: 2026-01-31T20:00:00
   ├─ last_updated: 2026-01-31T20:05:00
   └─ status: RUNNING
```

---

## مثال: Timeline 3 روزه

```
📅 روز 1 (پنج‌شنبه)
─────────────────────
20:00 → Update starts
20:05 → 100/1919 (5%)

📅 روز 2 (جمعه)
─────────────────────
(خودکار ادامه می‌یابد)
20:00 → Resume from day 1
20:05 → 200/1919 (10%)

📅 روز 3 (شنبه)
─────────────────────
(خودکار ادامه می‌یابد)
20:00 → Resume from day 2
20:05 → 300/1919 (15%)

...

📅 روز 20 (شنبه بعد)
─────────────────────
20:00 → Resume from day 19
20:05 → 1919/1919 (100%) ✅ COMPLETE!
```

---

