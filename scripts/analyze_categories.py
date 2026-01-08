
import sys
import os
from app.database import db
from app.services.tsetmc import client

def analyze_categories():
    print("--- Distribution of Categories across API Types in DB ---")
    for t in range(1, 6):
        symbols = db.get_symbols_by_market(f"symbols_type_{t}")
        if not symbols:
            print(f"Type {t}: Empty")
            continue
            
        cats = {}
        for s in symbols:
            cat = client._classify_equity_market(s)
            cats[cat] = cats.get(cat, 0) + 1
            
        print(f"Type {t} ({len(symbols)} total):")
        for cat, count in cats.items():
            print(f"  - {cat}: {count}")

if __name__ == "__main__":
    analyze_categories()
