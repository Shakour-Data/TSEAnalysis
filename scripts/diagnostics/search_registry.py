
import sqlite3
import json

def search_indices():
    conn = sqlite3.connect("tse_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT raw_data FROM symbols")
    rows = cursor.fetchall()
    
    found = []
    for row in rows:
        sym = json.loads(row[0])
        name = sym.get('l18', '')
        full_name = sym.get('l30', '')
        if "شاخص" in name or "شاخص" in full_name:
            found.append(sym)
            
    print(f"Found {len(found)} items containing 'شاخص' in symbols registry.")
    for f in found[:20]:
        print(f"  {f.get('l18')} ({f.get('l30')}) - Flow: {f.get('flow')} - Market: {f.get('market_name') or f.get('market')}")
    
    conn.close()

search_indices()
