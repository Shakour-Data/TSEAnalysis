
import sqlite3
import json
import os

DB_PATH = r"c:\Users\Administrator\Documents\Analysis\TSEAnalysis\data\tse_data.db"

def diag():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT isin, symbol_l18, market_category, raw_data FROM symbols")
    rows = cursor.fetchall()
    
    total = len(rows)
    print(f"Total symbols in DB: {total}")
    
    # Check for energy
    energy_keywords = ["انرژی", "energy", "بورس انرژی"]
    found_energy = []
    
    for isin, l18, m_cat, data_json in rows:
        data = json.loads(data_json)
        market_name = str(data.get('market_name', '')).lower()
        cs_name = str(data.get('cs_name', '')).lower()
        l18_str = str(l18).lower()
        
        if any(k in market_name for k in energy_keywords) or \
           any(k in cs_name for k in energy_keywords) or \
           any(k in l18_str for k in ["انرژی", "نفت"]):
            found_energy.append((l18, market_name, cs_name, m_cat))
            
    print(f"Potential Energy symbols found: {len(found_energy)}")
    for item in found_energy[:10]:
        print(item)
    
    # Let's check the raw data for one energy symbol
    if found_energy:
        sample_l18 = found_energy[0][0]
        for isin, l18, m_cat, data_json in rows:
            if l18 == sample_l18:
                data = json.loads(data_json)
                print(f"\nSample energy symbol raw data for {l18}:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                break

    # Check some other categories
    categories = {}
    from app.services.tsetmc import TSETMCClient
    client = TSETMCClient("dummy")
    
    for isin, l18, m_cat, data_json in rows:
        data = json.loads(data_json)
        cat = client._classify_equity_market(data)
        categories[cat] = categories.get(cat, 0) + 1
        
    print("\nClassification counts:")
    for cat, count in categories.items():
        print(f" - {cat}: {count}")

    conn.close()

if __name__ == "__main__":
    diag()
