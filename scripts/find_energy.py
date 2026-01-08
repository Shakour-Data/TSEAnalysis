
import sys
import os
from app.services.tsetmc import client

def find_energy_type():
    print("Searching for energy symbols in types 6-15...")
    for t in range(6, 16):
        try:
            data = client._make_request("Api/Tsetmc/AllSymbols.php", {"type": str(t)}, service="discovery")
            if isinstance(data, list) and len(data) > 0:
                print(f"Type {t} has {len(data)} symbols.")
                for s in data[:10]: # Check first 10
                    cat = client._classify_equity_market(s)
                    if cat == "energy" or "انرژی" in str(s.get('market_name', '')):
                        print(f"  FOUND ENERGY in type {t}!")
                        return t
            else:
                print(f"Type {t}: No data")
        except Exception as e:
            print(f"Type {t}: Error {e}")
    return None

if __name__ == "__main__":
    find_energy_type()
