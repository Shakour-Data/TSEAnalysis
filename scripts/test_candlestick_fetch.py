import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tsetmc import client
from app.database import db

print("[1] Getting symbols...")
symbols = db.get_all_symbols()[:3]  # First 3 symbols

for sym_data in symbols:
    symbol = sym_data['l18']
    print(f"\n[2] Testing symbol: {symbol}")
    
    # Try to get history
    history = db.get_history(symbol)
    print(f"    History in DB: {len(history)} records")
    
    # Try to fetch from API using correct method
    print(f"    Fetching price history from API...")
    price_history = client.get_price_history(symbol)
    print(f"    Price history from API: {len(price_history) if price_history else 0}")
    
    if price_history and len(price_history) > 0:
        print(f"    First candle: {price_history[0]}")

