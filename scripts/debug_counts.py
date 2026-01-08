
import sys
import os
from app.database import db
from app.services.tsetmc import client

def check_db_and_api():
    print("--- Database Raw Counts ---")
    for t in range(1, 6):
        count = len(db.get_symbols_by_market(f"symbols_type_{t}"))
        print(f"symbols_type_{t} in DB: {count}")
    
    markets = [
        "1", "2", "4", "5", "fixed_income", "tashilat", "commodity", "energy"
    ]
    
    print("\n--- API/Filtered Counts ---")
    results = {}
    for market in markets:
        try:
            symbols = client.get_all_symbols(market, force_refresh=False)
            if isinstance(symbols, list):
                results[market] = len(symbols)
            else:
                results[market] = "Error or None"
        except Exception as e:
            results[market] = f"Exception: {e}"
            
    for market, count in results.items():
        print(f"Market type {market}: {count} symbols")

if __name__ == "__main__":
    check_db_and_api()
