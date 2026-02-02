"""
Database Update Configuration and Testing Script
دیتابیس آپدیت کافیگریشن و تست
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
from datetime import datetime
from app.services.incremental_updater import IncrementalDatabaseUpdater
from app.database import db

print("="*70)
print("🔧 DATABASE UPDATE CONFIGURATION")
print("="*70)

# دریافت تعداد نمادها
total_symbols = db.get_total_symbols_count()
print(f"\n📊 Database Status:")
print(f"   Total symbols: {total_symbols}")

# پیکربندی
symbols_per_day_options = [50, 100, 150, 200]

print(f"\n⚙️ Update Strategy Options:")
for i, quota in enumerate(symbols_per_day_options, 1):
    days_needed = (total_symbols + quota - 1) // quota
    print(f"   {i}. {quota} symbols/day → {days_needed} days to complete")

# پیشنهاد
recommended = 100
days_needed = (total_symbols + recommended - 1) // recommended
print(f"\n✅ Recommended: {recommended} symbols/day (~{days_needed} days)")

# ایجاد updater
print(f"\n🚀 Creating updater...")
updater = IncrementalDatabaseUpdater(symbols_per_day=recommended)

# نمایش پیشرفت
progress = updater.progress
print(f"\n📈 Current Progress:")
print(f"   Updated: {progress.get('symbols_updated', 0)}")
print(f"   Failed: {progress.get('symbols_failed', 0)}")
print(f"   Total: {progress.get('total_symbols', 0)}")
print(f"   Completed symbols: {len(progress.get('completed_symbols', []))}")

# نمایش جزئیات
if progress.get('daily_progress'):
    print(f"\n📅 Daily Progress:")
    for date, stat in sorted(progress['daily_progress'].items()):
        print(f"   {date}: {stat.get('actual', 0)} updated, {stat.get('failed', 0)} failed")

print(f"\n" + "="*70)
print("💡 Usage:")
print("="*70)
print("""
1. Start automatic updates:
   python scripts/start_database_update.py

2. Check status:
   curl http://localhost:5000/api/updates/status
   curl http://localhost:5000/api/updates/progress

3. View failed symbols:
   curl http://localhost:5000/api/updates/failed

4. View logs:
   tail -f database_update.log

Configuration saved to: data/update_progress.json
""")
print("="*70)

# ذخیره کافیگریشن
config = {
    "strategy": {
        "symbols_per_day": recommended,
        "days_needed": days_needed,
        "total_symbols": total_symbols
    },
    "rate_limiting": {
        "base_delay": 2.0,
        "max_attempts": 3,
        "backoff_factor": 2.0
    },
    "created_at": datetime.now().isoformat()
}

config_file = "data/update_config.json"
with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, ensure_ascii=False, indent=2)

print(f"\n✅ Configuration saved to: {config_file}")
