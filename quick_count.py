
import sqlite3
import json

db_path = "tse_data.db"

def check_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT raw_data FROM symbols")
    rows = cursor.fetchall()
    
    counts = {}
    samples = {}
    
    for row in rows:
        sym = json.loads(row[0])
        market = sym.get('market_name') or sym.get('flowTitle') or sym.get('market')
        counts[market] = counts.get(market, 0) + 1
        if market not in samples:
            samples[market] = sym.get('l18')
            
    print("Markets found in DB Registry:")
    for m, c in counts.items():
        print(f"  {m}: {c} symbols (Sample: {samples[m]})")
    
    conn.close()

check_db()
