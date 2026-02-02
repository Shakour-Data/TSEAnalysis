"""
Start the automatic database update process
دیتابیس خودکار آپدیت شروع کنید
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from app.services.incremental_updater import start_updater
from app.database import db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_update.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

print("="*70)
print("🚀 STARTING AUTOMATIC DATABASE UPDATE")
print("="*70)

# Get database status
total_symbols = db.get_total_symbols_count()
print(f"\n📊 Database Status:")
print(f"   Total symbols: {total_symbols}")

# Start updater
symbols_per_day = 100  # customizable
print(f"\n⚙️ Configuration:")
print(f"   Symbols per day: {symbols_per_day}")
print(f"   API delay: 2.0 seconds")
print(f"   Max retries: 3")
print(f"   Estimated duration: {(total_symbols + symbols_per_day - 1) // symbols_per_day} days")

print(f"\n🔄 Starting updater...")
updater = start_updater(symbols_per_day=symbols_per_day)

print(f"\n✅ Database update started!")
print(f"\n📝 Progress tracking:")
print(f"   Log file: database_update.log")
print(f"   Progress file: data/update_progress.json")
print(f"   Status file: data/update_status.json")

print(f"\n🌐 Monitor via API:")
print(f"   Status: http://localhost:5000/api/updates/status")
print(f"   Progress: http://localhost:5000/api/updates/progress")
print(f"   Failed: http://localhost:5000/api/updates/failed")

print(f"\n📋 Commands:")
print(f"   Stop: POST http://localhost:5000/api/updates/stop")
print(f"   Resume: POST http://localhost:5000/api/updates/resume")

print(f"\n" + "="*70)
print("💾 The update process will continue in the background.")
print("You can close this script - the updater will keep running.")
print("="*70)

# Keep the script running
try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\n⏸️  Update paused. Progress saved.")
    print(f"Resume later with: python scripts/start_database_update.py")
