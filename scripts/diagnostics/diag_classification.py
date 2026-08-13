
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import db
from app.services.tsetmc import client

def diagnose():
    print(f"Checking database at: {db.db_path}")
    
    for api_type in ["1", "2"]:
        db_category = f"symbols_type_{api_type}"
        symbols = db.get_symbols_by_market(db_category)
        print(f"\nType {api_type}: {len(symbols)} symbols in DB")
        
        if not symbols:
            continue
            
        stats = {}
        examples = {}
        for s in symbols:
            cat = client._classify_equity_market(s)
            stats[cat] = stats.get(cat, 0) + 1
            if cat not in examples:
                examples[cat] = s
            
        print(f"Classification stats for Type {api_type}:")
        for cat, count in stats.items():
            print(f"  - {cat}: {count} (Example: {examples[cat].get('lVal18AF', 'N/A')})")

if __name__ == "__main__":
    diagnose()
