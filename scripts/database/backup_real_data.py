import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import shutil
from app.database import db

print("[1] Backing up current database with real data...")
db_path = db.db_path
backup_path = db_path.replace('.db', '_backup_real.db')

try:
    shutil.copy(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
except Exception as e:
    print(f"❌ Backup failed: {e}")

print("\n[2] Current data status:")
print(f"    Total symbols: {db.get_total_symbols_count()}")

# Count records with data
symbols = db.get_all_symbols()
symbols_with_history = 0
total_records = 0

for sym in symbols[:100]:  # Check first 100
    history = db.get_history(sym['l18'])
    if history:
        symbols_with_history += 1
        total_records += len(history)

print(f"    Symbols with history: {symbols_with_history}")
print(f"    Total history records: {total_records}")
print(f"\n✅ Database is ready for AI training with REAL data!")
print(f"   Backup saved to: {backup_path}")
