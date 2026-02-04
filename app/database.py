import sqlite3
import json
import os
import logging
import threading
from datetime import datetime, timedelta
import hashlib
import time

logger = logging.getLogger(__name__)

# Import validators (the module exists, so direct import is safe)
from app.utils.validators import DataValidator

class SymbolDatabase:
    """
    Thread-safe SQLite database manager for TSETMC symbols and price history.
    """
    def __init__(self, db_path=None):
        if db_path is None:
            # Detect project root (parent of app/ folder)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.path.join(base_dir, "data", "tse_data.db")
            print(f"DEBUG: Database path is {self.db_path}")
        else:
            self.db_path = db_path
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Thread safety lock
        self._db_lock = threading.RLock()
        
        # Query result caching (memory cache with TTL)
        self._query_cache = {}  # key: query_hash, value: (result, timestamp)
        self._cache_ttl = 300  # 5 منٹ cache TTL
        self._cache_lock = threading.RLock()
        
        self._init_db()
        self._init_test_tables()

    def _get_connection(self):
        """Thread-safe connection retrieval"""
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_cache_key(self, query, params=None):
        """Query کے لیے cache key بنائیں"""
        cache_str = f"{query}:{json.dumps(params or [])}"
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key):
        """Cache سے نتیجہ حاصل کریں (اگر expired نہیں)"""
        with self._cache_lock:
            if cache_key in self._query_cache:
                result, timestamp = self._query_cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    logger.debug(f"✅ Cache hit for {cache_key[:8]}")
                    return result
                else:
                    # Expired cache کو ہٹائیں
                    del self._query_cache[cache_key]
        return None
    
    def _set_cache(self, cache_key, result):
        """نتیجہ کو cache میں ڈالیں"""
        with self._cache_lock:
            self._query_cache[cache_key] = (result, time.time())
    
    def _clear_cache_for_query(self, query_pattern=None):
        """Cache کو صاف کریں (optional pattern match)"""
        with self._cache_lock:
            if query_pattern is None:
                self._query_cache.clear()
                logger.info("✅ پوری query cache صاف کی گئی")
            else:
                keys_to_delete = [k for k in self._query_cache.keys() if query_pattern in k]
                for k in keys_to_delete:
                    del self._query_cache[k]
                logger.info(f"✅ {len(keys_to_delete)} cache entries صاف کیے گئے")

    def _init_db(self):
        """Database initialization with proper error handling"""
        with self._db_lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA synchronous=FULL;")  # FULL for durability
                    cursor.execute("PRAGMA cache_size=2000;")
                    cursor.execute("PRAGMA temp_store=memory;")
                    cursor.execute("PRAGMA busy_timeout=10000;")  # 10 سیکنڈ انتظار
                
                    # محفوظ Schema migration
                    self._safe_schema_migration(conn)
                    conn.commit()
            
            except Exception as e:
                logger.error(f"Database initialization failed: {e}")
                raise
    
    def _safe_schema_migration(self, conn):
        """
        محفوظ طریقے سے database schema کو upgrade کریں
        - پہلے backup بنائیں
        - پھر migration کریں
        """
        cursor = conn.cursor()
        
        try:
            # 1. پہلے check کریں کہ ٹیبل موجود ہے یا نہیں
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='symbols'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # 2. Old schema check
                try:
                    cursor.execute("PRAGMA table_info(symbols)")
                    cols = cursor.fetchall()
                    
                    # اگر پرانی schema ہے (id as primary key)
                    if cols and cols[0][1] == 'id' and cols[0][5] == 1:
                        logger.warning("⚠️ پرانی database schema detected۔ Backup بنا رہے ہیں...")
                        
                        # Backup بنائیں
                        import shutil
                        backup_path = self.db_path + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                        try:
                            shutil.copy2(self.db_path, backup_path)
                            logger.info(f"✅ Backup بنایا گیا: {backup_path}")
                        except Exception as e:
                            logger.error(f"Backup failed: {e}")
                            raise
                        
                        # اب migration کریں
                        logger.info("Migration شروع کر رہے ہیں...")
                        cursor.execute("DROP TABLE symbols")
                        conn.commit()
                        logger.info("✅ پرانی table ہٹائی گئی")
                except Exception as e:
                    logger.error(f"Schema check failed: {e}")
                    raise
            
            # 3. نئی schema بنائیں
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
            columns = {
                "symbol_l18": "TEXT",
                "name_l30": "TEXT",
                "market_category": "TEXT",
                "raw_data": "TEXT",
                "last_updated": "TIMESTAMP"
            }
            for col_name, col_type in columns.items():
                try:
                    cursor.execute(f"ALTER TABLE symbols ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass # Already exists
            
            # Create index برای تیز queries
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON price_history(symbol)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON price_history(date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_market ON symbols(market_category)")
            except sqlite3.OperationalError:
                pass
                
            conn.commit()
        
        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            raise

    def _init_test_tables(self):
        """Build tables for web-based test runner and scheduler"""
        with self._db_lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS test_results (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            test_suite TEXT,
                            status TEXT,
                            start_time TIMESTAMP,
                            end_time TIMESTAMP,
                            logs TEXT,
                            exit_code INTEGER,
                            ai_analysis TEXT
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS test_schedules (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            test_name TEXT,
                            cron_pattern TEXT,
                            is_active INTEGER DEFAULT 1,
                            last_run TIMESTAMP,
                            next_run TIMESTAMP
                        )
                    ''')
                    conn.commit()
            except Exception as e:
                logger.error(f"Test tables initialization failed: {e}")

    def cleanup_old_data(self, days=365):
        """
        پرانے ڈیٹا کو صاف کریں تاکہ DB سائز کنٹرول میں رہے
        - پہلے 1 سال سے پرانا ڈیٹا
        - فیصد کے حساب سے حذف کریں
        """
        with self._db_lock:
            try:
                cutoff_date = datetime.now() - timedelta(days=days)
                cutoff_str = cutoff_date.strftime('%Y-%m-%d')
                
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # پہلے check کریں کتنا ڈیٹا حذف ہوگا
                    cursor.execute(
                        "SELECT COUNT(*) FROM price_history WHERE date < ?",
                        (cutoff_str,)
                    )
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        logger.info(f"صفائی: {count} قدیم ریکارڈ حذف ہو رہے ہیں...")
                        
                        # حذف کریں
                        cursor.execute(
                            "DELETE FROM price_history WHERE date < ?",
                            (cutoff_str,)
                        )
                        
                        conn.commit()
                        logger.info(f"✅ {count} ریکارڈ حذف ہوئے")
                        
                        return count
                    
                    return 0
                    
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")
                return 0

    def save_history(self, symbol, history_data):
        """Thread-safe price history saving with atomic transactions اور validation"""
        if not history_data or not DataValidator.is_valid_symbol(symbol):
            logger.warning(f"Invalid symbol or empty history: {symbol}")
            return
        
        # پہلے data کو filter کریں
        history_data = DataValidator.ensure_non_empty_list(history_data)
        if not history_data:
            return
            
        now = datetime.now().isoformat()
        
        with self._db_lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # شروع: Transaction
                    cursor.execute("BEGIN IMMEDIATE")
                    
                    saved_count = 0
                    skipped_count = 0
                    
                    for item in history_data:
                        date = item.get('date')
                        if not date:
                            skipped_count += 1
                            continue
                        
                        # تاریخ validate کریں
                        if not DataValidator.is_valid_date(date):
                            logger.warning(f"Invalid date for {symbol}: {date}")
                            skipped_count += 1
                            continue
                        
                        try:
                            # قیمتیں حاصل کریں (fallback keys سے)
                            open_price = item.get('pf') or item.get('open') or 0
                            high_price = item.get('pmax') or item.get('high') or 0
                            low_price = item.get('pmin') or item.get('low') or 0
                            close_price = item.get('pc') or item.get('close') or 0
                            volume = item.get('tvol') or item.get('volume') or 0
                            
                            # سب قیمتوں کو validate کریں
                            if not (DataValidator.is_valid_price(open_price) and
                                    DataValidator.is_valid_price(high_price) and
                                    DataValidator.is_valid_price(low_price) and
                                    DataValidator.is_valid_price(close_price) and
                                    DataValidator.is_valid_volume(volume)):
                                logger.debug(f"Skipping invalid price data for {symbol} on {date}")
                                skipped_count += 1
                                continue
                            
                            cursor.execute('''
                                INSERT OR REPLACE INTO price_history 
                                (symbol, date, open, high, low, close, volume, raw_data, last_updated)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                symbol,
                                date,
                                float(open_price),
                                float(high_price),
                                float(low_price),
                                float(close_price),
                                int(volume),
                                json.dumps(item, ensure_ascii=False),
                                now
                            ))
                            saved_count += 1
                        except (ValueError, TypeError) as e:
                            logger.error(f"Invalid data for {symbol} on {date}: {e}")
                            skipped_count += 1
                            continue
                    
                    # Commit: سب کچھ ایک ساتھ
                    conn.commit()
                    logger.info(f"✅ {saved_count} records saved for {symbol} ({skipped_count} skipped)")
                    
            except sqlite3.DatabaseError as e:
                logger.error(f"❌ Database error saving history for {symbol}: {e}")
                # Automatic rollback by context manager
                raise
            except Exception as e:
                logger.error(f"❌ Unexpected error saving history for {symbol}: {e}")
                raise

    def get_history(self, symbol):
        """Retrieves ALL cached price history for a symbol, sorted by date (with caching)."""
        # Cache key بنائیں
        cache_key = self._get_cache_key("get_history", [symbol])
        
        # پہلے cache سے چیک کریں
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # اگر cache میں نہیں ہے تو database سے حاصل کریں
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT raw_data FROM price_history WHERE symbol = ? ORDER BY date ASC', (symbol,))
            rows = cursor.fetchall()
            result = [json.loads(row['raw_data']) for row in rows]
        
        # Cache میں ڈالیں
        self._set_cache(cache_key, result)
        return result

    def get_latest_date(self, symbol):
        """Returns the latest date we have for a given symbol (with caching)."""
        # Cache key بنائیں
        cache_key = self._get_cache_key("get_latest_date", [symbol])
        
        # پہلے cache سے چیک کریں
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Database سے حاصل کریں
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(date) FROM price_history WHERE symbol = ?', (symbol,))
            res = cursor.fetchone()
            result = res[0] if res else None
        
        # Cache میں ڈالیں
        self._set_cache(cache_key, result)
        return result

    # --- Symbol Registry Methods ---
    
    def save_symbols(self, symbol_list, market_category):
        """Saves or updates symbols in the registry. Uses REPLACE to handle updates."""
        if not symbol_list or not isinstance(symbol_list, list):
            return
        
        # Save کرتے وقت cache کو صاف کریں تاکہ fresh data ملے
        self._clear_cache_for_query("get_symbols_by_market")
        self._clear_cache_for_query("get_all_symbols")
            
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
        """Retrieves symbols for a specific market from local storage (with caching)."""
        # Cache key بنائیں
        cache_key = self._get_cache_key("get_symbols_by_market", [market_category])
        
        # پہلے cache سے چیک کریں
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Database سے حاصل کریں
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT raw_data FROM symbols WHERE market_category = ?', (market_category,))
            rows = cursor.fetchall()
            result = [json.loads(row['raw_data']) for row in rows]
        
        # Cache میں ڈالیں
        self._set_cache(cache_key, result)
        return result

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

    def get_all_symbols(self):
        """Retrieves all symbols from local storage (with caching)."""
        # Cache key بنائیں
        cache_key = self._get_cache_key("get_all_symbols", [])
        
        # پہلے cache سے چیک کریں
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Database سے حاصل کریں
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT raw_data FROM symbols')
            rows = cursor.fetchall()
            result = [json.loads(row['raw_data']) for row in rows]
        
        # Cache میں ڈالیں
        self._set_cache(cache_key, result)
        return result

db = SymbolDatabase()
