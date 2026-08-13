# 📅 Automatic Database Update System

## خلاصه

سیستم **آپدیت خودکار و تدریجی** برای به‌روز کردن تمام 1,919 نماد TSE بر اساس:
- ✅ برنامه‌ریزی هوشمند (100 نماد/روز)
- ✅ مدیریت مذکر Rate Limiting
- ✅ خود ترمیم برای failures
- ✅ پایمون پیشرفت Real-time
- ✅ استمرار خودکار بعد از توقف

---

## 📊 نقشه و جدول زمانی

```
Total Symbols: 1,919
Daily Quota: 100 symbols
Duration: ~20 days

Day 1:    Symbols 1-100      (5% progress)
Day 2:    Symbols 101-200    (10% progress)
...
Day 20:   Symbols 1819-1919  (100% complete!)
```

---

## 🚀 شروع آپدیت

### بر روی سرور (خودکار)

```bash
# اپلیکیشن Flask را شروع کنید
python app.py

# آپدیت خودکار شروع خواهد شد!
```

### بر روی Terminal (دستی)

```bash
# تنظیم و کنفیگریشن
python scripts/configure_database_update.py

# شروع آپدیت
python scripts/start_database_update.py
```

---

## 🔍 نظارت بر پیشرفت

### 1. **بر روی Terminal**

```bash
# نمایش لاگ‌های زنده
tail -f database_update.log

# یا در PowerShell
Get-Content database_update.log -Tail 50 -Wait
```

### 2. **بر روی API**

```bash
# وضعیت کلی
curl http://localhost:5000/api/updates/status

# پیشرفت دقیق
curl http://localhost:5000/api/updates/progress

# نمادهای ناموفق (retry)
curl http://localhost:5000/api/updates/failed
```

### 3. **فایل‌های Progress**

```
data/update_progress.json    → وضعیت دقیق
data/update_status.json      → پیام فعلی
database_update.log          → لاگ‌های کامل
```

---

## 📋 مثال‌های واقعی

### نمایش Progress

```json
{
  "percentage": 45.5,
  "updated": 873,
  "failed": 12,
  "total": 1919,
  "pending": 1046,
  "days_left": 11,
  "daily_quota": 100,
  "daily_progress": {
    "2026-01-31": {
      "date": "2026-01-31",
      "target": 100,
      "actual": 95,
      "failed": 5,
      "updated_symbols": ["وبملت", "عیار", ...]
    }
  }
}
```

### لاگ‌های نمونه

```
2026-01-31 20:00:00 [INFO] Starting daily update cycle: 2026-01-31
2026-01-31 20:00:00 [INFO] Total symbols: 1919
2026-01-31 20:00:00 [INFO] Pending updates: 1919
2026-01-31 20:00:05 [INFO] [1/100] 1.0% - Updating: وبملت
2026-01-31 20:00:05 [DEBUG]     ✅ وبملت: 100 records saved
2026-01-31 20:00:07 [INFO] [2/100] 2.0% - Updating: عیار
...
2026-01-31 20:05:00 [INFO] 📊 Daily Summary: 2026-01-31
2026-01-31 20:05:00 [INFO]   Updated today: 95/100
2026-01-31 20:05:00 [INFO]   Failed today: 5
2026-01-31 20:05:00 [INFO]   Total progress: 95/1919
2026-01-31 20:05:00 [INFO]   Estimated days left: 19
```

---

## ⚙️ کنترل آپدیت

### متوقف کردن

```bash
# بر روی API
curl -X POST http://localhost:5000/api/updates/stop

# یا
Ctrl+C بر روی terminal
```

### ادامه دادن

```bash
# بر روی API
curl -X POST http://localhost:5000/api/updates/resume

# یا
python scripts/start_database_update.py
```

### شروع دوباره (تازه‌سازی کامل)

```bash
# حذف progress فایل
rm data/update_progress.json

# شروع دوباره
python scripts/start_database_update.py
```

---

## 🛡️ مدیریت خطاها

### آیا API fail شود؟

✅ سیستم:
1. تا 3 بار دوباره تلاش می‌کند
2. تاخیر بین درخواست‌ها را افزایش می‌دهد
3. نماد ناموفق را ثبت می‌کند
4. در روز بعد دوباره تلاش می‌کند

### آیا سرور restart شود؟

✅ سیستم:
1. پیشرفت را از فایل بارگذاری می‌کند
2. از جایی که متوقف شده ادامه می‌دهد
3. failures را دوباره تلاش می‌کند

---

## 🔧 تنظیمات (اختیاری)

فایل: `data/update_config.json`

```json
{
  "strategy": {
    "symbols_per_day": 100,        // تعداد نمادها در روز
    "days_needed": 20,             // روز‌های تخمینی
    "total_symbols": 1919
  },
  "rate_limiting": {
    "base_delay": 2.0,             // تاخیر پایه (ثانیه)
    "max_attempts": 3,             // تلاش‌های مجدد
    "backoff_factor": 2.0          // ضریب افزایش
  }
}
```

### تغییر سرعت آپدیت

```python
# در app/__init__.py
symbols_per_day = 150  # 150 نماد/روز = 13 روز
updater = start_updater(symbols_per_day=symbols_per_day)
```

---

## 📊 نتایج مورد انتظار

### روز 1
```
✅ Symbols updated: 95-100
⏱️  Time: ~5 minutes
```

### روز 10
```
✅ Total updated: 950-1000 (50% complete)
📈 Speed: ~100 symbols/day
```

### روز 20
```
✅ Total updated: 1919 (100% complete!)
🎉 Database fully updated!
```

---

## 🐛 رفع مسائل

### لاگ‌ها نشان نمی‌دهد که آپدیت اجرا می‌شود

```bash
# بررسی اینکه thread در حال اجرا است
python -c "from app.services.incremental_updater import get_updater; print(get_updater().is_running)"
```

### بعضی نمادها آپدیت نمی‌شوند

```bash
# بررسی failed symbols
curl http://localhost:5000/api/updates/failed
```

### API 403 Forbidden بر می‌گرداند

✅ طبیعی است! سیستم:
- از cache استفاده می‌کند
- تاخیر را افزایش می‌دهد
- بعداً دوباره تلاش می‌کند

---

## 📝 فایل‌های مرتبط

```
📂 app/services/
  ├── incremental_updater.py    → اپدیتر اصلی
  └── rate_limiter.py           → مدیریت Rate Limiting

📂 app/api/
  └── updates_routes.py         → API endpoints

📂 scripts/
  ├── configure_database_update.py
  └── start_database_update.py

📂 data/
  ├── update_progress.json      → پیشرفت
  ├── update_status.json        → وضعیت فعلی
  └── update_config.json        → کنفیگریشن
```

---

## ✅ Checklist

- [ ] کنفیگریشن انجام شد
- [ ] آپدیت شروع شد
- [ ] لاگ‌ها را می‌توانید مشاهده کنید
- [ ] API endpoints جواب می‌دهند
- [ ] Progress به‌تدریج افزایش می‌یابد
- [ ] بعد از 20 روز: 100% آپدیت!

---

**آخرین بروزرسانی**: 2026-01-31  
**وضعیت**: ✅ Production Ready
