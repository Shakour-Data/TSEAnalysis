
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.tsetmc import client
import json

symbols = client.get_all_symbols("1")
print(f"Total symbols for Bourse (market_type=1): {len(symbols)}")
if symbols:
    print("First 5 symbols summary:")
    for s in symbols[:5]:
        print(f"  - {s.get('lVal18AF')} ({s.get('isin')}) -> Market: {s.get('market_name')}")
else:
    print("No symbols found!")
