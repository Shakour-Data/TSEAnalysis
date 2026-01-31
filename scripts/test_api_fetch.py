import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tsetmc import client
from app.database import db

print("[1] Testing API connection...")
result = client.get_all_symbols('1', force_refresh=True)

if result and len(result) > 0:
    print(f"✅ SUCCESS: Fetched {len(result)} symbols from API")
    print(f"Sample symbol: {result[0]}")
    
    # Check database
    count = db.get_total_symbols_count()
    print(f"✅ Database now has {count} total symbols")
else:
    print("❌ FAILED: Could not fetch symbols from API")
    print("Checking what's in the database...")
    count = db.get_total_symbols_count()
    print(f"Database has {count} symbols cached")
