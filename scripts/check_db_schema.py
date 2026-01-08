
import sqlite3
import os

db_path = "data/tse_data.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

for (table_name,) in tables:
    cursor.execute(f"PRAGMA table_info({table_name})")
    print(f"\nSchema for {table_name}:")
    for col in cursor.fetchall():
        print(f"  - {col}")
