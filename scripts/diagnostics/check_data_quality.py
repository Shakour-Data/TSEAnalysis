import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import db
from app.services.tsetmc import client

print("[1] Checking database for existing real data...")
symbols = db.get_all_symbols()[:20]

real_data_count = 0
mock_data_count = 0

for sym_data in symbols:
    symbol = sym_data['l18']
    history = db.get_history(symbol)
    
    if history and len(history) > 0:
        # Check the fields in the record
        first_record = history[0]
        fields = set(first_record.keys()) if isinstance(first_record, dict) else []
        
        # Real data should have OHLCV or similar
        if any(f in fields for f in ['open', 'high', 'low', 'close', 'volume', 'tvol']):
            real_data_count += 1
            print(f"  ✅ {symbol}: {len(history)} records, fields: {list(fields)}")
        else:
            mock_data_count += 1
            print(f"  ⚠️  {symbol}: {len(history)} records, fields: {list(fields)}")

print(f"\n[2] Summary:")
print(f"    Real data symbols: {real_data_count}")
print(f"    Unclear symbols: {mock_data_count}")
print(f"    Total symbols in DB: {len(symbols)}")

# Show a sample of real data
if real_data_count > 0:
    for sym_data in symbols:
        symbol = sym_data['l18']
        history = db.get_history(symbol)
        if history and any(f in history[0] for f in ['open', 'high', 'low', 'close', 'volume']):
            print(f"\n[3] Sample real data from {symbol}:")
            print(f"    First record: {history[0]}")
            break
