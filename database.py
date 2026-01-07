import sqlite3
import json
import os
from datetime import datetime

class SymbolDatabase:
    """
    Manages SQLite database for caching TSETMC symbols and price history.
    """
    def __init__(self, db_path="tse_data.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Symbol Master Registry (For offline search and firewall fallback)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS symbols (
                    isin TEXT PRIMARY KEY,
                    symbol_l18 TEXT,
                    name_l30 TEXT,
                    market_category TEXT,
                    raw_data TEXT,
                    last_updated TIMESTAMP
                )
            ''')
            
            # 2. Price history table for Technical Analysis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    symbol TEXT,
                    date TEXT,
                    open REAL,
                    high REAL, low REAL,
                    close REAL,
                    volume INTEGER,
                    raw_data TEXT,
                    last_updated TIMESTAMP,
                    PRIMARY KEY (symbol, date)
                )
            ''')
            
            # MIGRATION: Ensure all columns exist in symbols table
            try:
                cursor.execute("ALTER TABLE symbols ADD COLUMN market_category TEXT")
            except sqlite3.OperationalError:
                pass # Already exists
                
            conn.commit()

    def save_history(self, symbol, history_data):
        """Saves price history for a symbol. Uses INSERT OR IGNORE to avoid duplicates."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for item in history_data:
                # Map API field names to DB names if necessary
                # API usually gives: pc (close), pf (open), pmax (high), pmin (low), tvol (volume), date
                date = item.get('date')
                if not date: continue
                
                cursor.execute('''
                    INSERT OR IGNORE INTO price_history 
                    (symbol, date, open, high, low, close, volume, raw_data, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    date,
                    item.get('pf') or item.get('open'),
                    item.get('pmax') or item.get('high'),
                    item.get('pmin') or item.get('low'),
                    item.get('pc') or item.get('close'),
                    item.get('tvol') or item.get('volume'),
                    json.dumps(item, ensure_ascii=False),
                    now
                ))
            conn.commit()

    def get_history(self, symbol):
        """Retrieves ALL cached price history for a symbol, sorted by date."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT raw_data FROM price_history WHERE symbol = ? ORDER BY date ASC', (symbol,))
            rows = cursor.fetchall()
            return [json.loads(row['raw_data']) for row in rows]

    def get_latest_date(self, symbol):
        """Returns the latest date we have for a given symbol."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(date) FROM price_history WHERE symbol = ?', (symbol,))
            res = cursor.fetchone()
            return res[0] if res else None

    # --- Symbol Registry Methods ---
    
    def save_symbols(self, symbol_list, market_category):
        """Saves or updates symbols in the registry. Uses REPLACE to handle updates."""
        if not symbol_list or not isinstance(symbol_list, list):
            return
            
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for sym in symbol_list:
                # Use ISIN as primary key, fallback to ticker or id
                isin = sym.get('isin') or sym.get('id') or sym.get('l18')
                if not isin: continue
                
                cursor.execute('''
                    INSERT OR REPLACE INTO symbols 
                    (isin, symbol_l18, name_l30, market_category, raw_data, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    str(isin),
                    str(sym.get('l18', '')),
                    str(sym.get('l30', '')),
                    str(market_category),
                    json.dumps(sym, ensure_ascii=False),
                    now
                ))
            conn.commit()

    def get_symbols_by_market(self, market_category):
        """Retrieves symbols for a specific market from local storage."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT raw_data FROM symbols WHERE market_category = ?', (market_category,))
            rows = cursor.fetchall()
            return [json.loads(row['raw_data']) for row in rows]

    def clear_symbols(self, market_category):
        """Clears symbols for a specific market before a full refresh."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM symbols WHERE market_category = ?', (market_category,))
            conn.commit()

    def is_market_empty(self, market_category):
        """Checks if a specific market category has any symbols stored."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM symbols WHERE market_category = ?', (market_category,))
            count = cursor.fetchone()[0]
            return count == 0

    def get_total_symbols_count(self):
        """Returns the total number of symbols in the registry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM symbols')
            return cursor.fetchone()[0]

db = SymbolDatabase()
