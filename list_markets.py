
import sqlite3
import json

def list_markets():
    conn = sqlite3.connect("tse_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT raw_data FROM symbols")
    rows = cursor.fetchall()
    
    markets = {}
    for row in rows:
        sym = json.loads(row[0])
        m = sym.get('market_name') or sym.get('flowTitle') or sym.get('market') or "Unknown"
        markets[m] = markets.get(m, 0) + 1
        
    print("Markets and counts in Registry:")
    for m, c in markets.items():
        print(f"  {m}: {c}")
    
    conn.close()

list_markets()
