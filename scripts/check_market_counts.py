
import sys
import os
import time
from app.services.tsetmc import client

def check_counts():
    markets = [
        "1", "2", "4", "5", "fixed_income", "tashilat", "commodity", "energy"
    ]
    
    results = {}
    print("Checking symbol counts for different market types...")
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
    print("Waiting 30 seconds for the sync to finish...")
    time.sleep(30)
    check_counts()
