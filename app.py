import os
import pandas as pd
import numpy as np
import ta
from flask import Flask, render_template, request, jsonify, send_file
import requests
from datetime import datetime
import io
import random
from flask_caching import Cache

app = Flask(__name__)

# Configure Caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"
BASE_URL = "https://brsapi.ir"
REQUEST_USAGE_LIMIT = 0.1  # Limit to 10% of requests

class TSETMCClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = BASE_URL
        self.session = requests.Session()
        # Updated headers to match 6G Firewall requirements exactly
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,fa;q=0.8",
            "DNT": "1",
            "Connection": "keep-alive",
        })
        self._symbols_cache = {} # Simple cache for symbols

    def _make_request(self, endpoint, params=None):
        # Exempt symbol lists from the 10% limit to ensure UI stability
        is_critical = "AllSymbols.php" in endpoint or "Index.php" in endpoint
        
        if not is_critical and random.random() > REQUEST_USAGE_LIMIT:
            print(f"DEBUG: Request to {endpoint} blocked by 10% usage limit.")
            return {"error": "محدودیت موقت: در حال حاضر تنها ۱۰٪ از درخواست‌ها پردازش می‌شوند. لطفاً دوباره تلاش کنید."}

        url = f"{self.base_url}/{endpoint}"
        request_params = {"key": self.api_key}
        if params:
            request_params.update(params)
        
        print(f"DEBUG: Requesting {url} with params {request_params}")
        try:
            response = self.session.get(url, params=request_params, timeout=20)
            
            # Check if response is empty
            if not response.text.strip():
                print("DEBUG: Empty response received")
                return {"error": "پاسخ وب‌سرویس خالی است. ممکن است نماد اشتباه باشد یا داده‌ای وجود نداشته باشد."}

            if response.status_code != 200:
                print(f"DEBUG: HTTP Error {response.status_code}: {response.text[:200]}")
                try:
                    err_data = response.json()
                    return {"error": err_data.get('message_error', response.text)}
                except:
                    return {"error": f"HTTP {response.status_code}: {response.text[:100]}"}
            
            try:
                data = response.json()
                print(f"DEBUG: Success! Received {len(data) if isinstance(data, list) else 'dict'} items")
                return data
            except Exception as e:
                print(f"DEBUG: JSON Decode Error in {endpoint}: {e}")
                print(f"DEBUG: Response content: {response.text[:200]}")
                return {"error": f"خطا در پردازش پاسخ (JSON Error)."}

        except requests.exceptions.Timeout:
            print("DEBUG: Request timed out")
            return {"error": "زمان پاسخگویی وب‌سرویس به پایان رسید (Timeout)."}
        except Exception as e:
            print(f"DEBUG: Error in {endpoint}: {e}")
            return {"error": str(e)}

    def get_all_symbols(self, market_type):
        # Cache symbols for 1 hour to avoid excessive API calls
        cache_key = f"symbols_{market_type}"
        now = datetime.now()
        if cache_key in self._symbols_cache:
            data, timestamp = self._symbols_cache[cache_key]
            if (now - timestamp).total_seconds() < 3600:
                return data
        
        # Mapping and Filtering logic to fix "mixed up" assets
        result_symbols = []
        
        if market_type in ["1", "2", "5"]: # Bourse, Farabourse, ETF
            data = self._make_request("Api/Tsetmc/AllSymbols.php", {"type": "1"})
            if data and isinstance(data, list):
                if market_type == "1": # Bourse
                    result_symbols = [s for s in data if str(s.get('cs_id')) != '68' and s.get('isin', '').startswith(('IRO1', 'IRT1', 'IRR1'))]
                elif market_type == "2": # Farabourse
                    result_symbols = [s for s in data if str(s.get('cs_id')) != '68' and s.get('isin', '').startswith(('IRO3', 'IRT3', 'IRR3', 'IRO7', 'IRR7'))]
                elif market_type == "5": # ETF
                    result_symbols = [s for s in data if str(s.get('cs_id')) == '68']
        
        elif market_type == "3": # Kala (Commodity)
            # Fetch both Type 2 and 3 for Kala/Futures
            d2 = self._make_request("Api/Tsetmc/AllSymbols.php", {"type": "2"})
            d3 = self._make_request("Api/Tsetmc/AllSymbols.php", {"type": "3"})
            if isinstance(d2, list): result_symbols.extend(d2)
            if isinstance(d3, list): result_symbols.extend(d3)
            
        elif market_type == "fixed_income": # Fixed Income (Debt)
            data = self._make_request("Api/Tsetmc/AllSymbols.php", {"type": "4"})
            if isinstance(data, list): result_symbols = data

        elif market_type == "tashilat": # Housing Loans
            data = self._make_request("Api/Tsetmc/AllSymbols.php", {"type": "5"})
            if isinstance(data, list): result_symbols = data
            
        elif market_type == "indices_market":
            data = self._make_request("Api/Tsetmc/Index.php", {"type": "3"})
            if data and isinstance(data, list):
                # Map index data to symbol format for the dropdown
                result_symbols = [{"id": f"idx_{i}", "l18": item['name'], "l30": item['name']} for i, item in enumerate(data)]
            
            # Add Bourse and Farabourse main indices if not already there
            # Note: "شاخص کل" is usually in type=3, but we add explicit ones for clarity
            if not any(s['l18'] == "شاخص کل بورس" for s in result_symbols):
                result_symbols.insert(0, {"id": "idx_b", "l18": "شاخص کل بورس", "l30": "شاخص کل بورس"})
            if not any(s['l18'] == "شاخص کل فرابورس" for s in result_symbols):
                result_symbols.insert(1, {"id": "idx_f", "l18": "شاخص کل فرابورس", "l30": "شاخص کل فرابورس"})

        elif market_type == "indices_industry":
            # Industry indices are not directly available as symbols in AllSymbols.
            # We use the sectors list as a proxy.
            data = self._make_request("Api/Tsetmc/AllSymbols.php", {"type": "1"})
            if data and isinstance(data, list):
                sectors = sorted(list(set(s.get('cs') for s in data if s.get('cs'))))
                result_symbols = [{"id": f"ind_{i}", "l18": s, "l30": f"شاخص صنعت {s}"} for i, s in enumerate(sectors)]
            
            # Fallback to common sectors if API fails or returns empty
            if not result_symbols:
                common_sectors = ["خودرو", "بانک", "فلزات اساسی", "شیمیایی", "فرآورده های نفتی", "سرمایه گذاری", "سیمان", "غذایی", "دارویی"]
                result_symbols = [{"id": f"ind_f_{i}", "l18": s, "l30": f"شاخص صنعت {s}"} for i, s in enumerate(common_sectors)]

        if result_symbols:
            self._symbols_cache[cache_key] = (result_symbols, now)
            return result_symbols
        
        return {"error": "داده‌ای یافت نشد یا خطای ارتباط با سرور"}

    def get_symbol_info(self, symbol):
        return self._make_request("Api/Tsetmc/Symbol.php", {"l18": symbol})

    def get_price_history(self, symbol, data_type=0, adjusted=True):
        return self._make_request("Api/Tsetmc/History.php", {
            "l18": symbol, 
            "type": data_type,
            "adjusted": str(adjusted).lower()
        })

    def get_candlestick(self, symbol, adjusted=True, type=1):
        # Candlestick API requires 'type' parameter and returns a dict
        # type=1: intraday, type=2: daily, type=3: daily adjusted
        res = self._make_request("Api/Tsetmc/Candlestick.php", {
            "l18": symbol, 
            "adjusted": str(adjusted).lower(),
            "type": type
        })
        key_map = {1: 'candle_intraday', 2: 'candle_daily', 3: 'candle_daily_adjusted'}
        key = key_map.get(type, 'candle_intraday')
        
        if res and isinstance(res, dict) and key in res:
            return res[key]
        return res

    def get_transactions(self, symbol):
        return self._make_request("Api/Tsetmc/Transaction.php", {"l18": symbol})

    def get_shareholders(self, symbol):
        return self._make_request("Api/Tsetmc/Shareholder.php", {"l18": symbol})

    def get_indices(self, index_type):
        return self._make_request("Api/Tsetmc/Index.php", {"type": index_type})

    def get_nav(self, symbol):
        return self._make_request("Api/Tsetmc/Nav.php", {"l18": symbol})

    def get_codal_announcements(self, symbol=None, category=None, date_start=None, date_end=None):
        params = {}
        if symbol and symbol != "all":
            params["symbol"] = symbol  # Changed from l18 to symbol as per standard Codal API naming
        if category:
            params["category"] = category
        if date_start:
            params["date_start"] = date_start.replace('/', '-')
        if date_end:
            params["date_end"] = date_end.replace('/', '-')
        
        res = self._make_request("Api/Codal/Announcement.php", params)
        # If symbol search fails, try with l18 as fallback
        if (not res or (isinstance(res, dict) and "error" in res)) and symbol and symbol != "all":
            params["l18"] = symbol
            if "symbol" in params: del params["symbol"]
            res = self._make_request("Api/Codal/Announcement.php", params)

        if res and isinstance(res, dict) and 'announcement' in res:
            return res['announcement']
        return res

client = TSETMCClient(API_KEY)

def calculate_technical_analysis(data):
    if not data or not isinstance(data, list) or len(data) < 30:
        return data

    df = pd.DataFrame(data)
    # Ensure numeric columns
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Sort by date to ensure correct calculation
    if 'date' in df.columns:
        df = df.sort_values('date')

    try:
        # Dimension 1: Trend (روند)
        df['SMA20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['SMA50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['EMA20'] = ta.trend.ema_indicator(df['close'], window=20)
        df['EMA50'] = ta.trend.ema_indicator(df['close'], window=50)
        df['MACD'] = ta.trend.macd(df['close'])
        df['MACD_Sig'] = ta.trend.macd_signal(df['close'])
        df['ADX'] = ta.trend.adx(df['high'], df['low'], df['close'])

        # Dimension 2: Momentum (شتاب)
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)
        df['STOCHk'] = ta.momentum.stoch(df['high'], df['low'], df['close'])
        df['STOCHd'] = ta.momentum.stoch_signal(df['high'], df['low'], df['close'])
        df['WILLR'] = ta.momentum.williams_r(df['high'], df['low'], df['close'])
        df['ROC'] = ta.momentum.roc(df['close'], window=10)
        df['MFI'] = ta.volume.money_flow_index(df['high'], df['low'], df['close'], df['volume'])

        # Dimension 3: Volatility (نوسان)
        df['BBU'] = ta.volatility.bollinger_hband(df['close'], window=20)
        df['BBL'] = ta.volatility.bollinger_lband(df['close'], window=20)
        df['ATR'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
        df['STDDEV'] = df['close'].rolling(window=20).std()
        df['KC_Upper'] = ta.volatility.keltner_channel_hband(df['high'], df['low'], df['close'], window=20)
        df['DC_Upper'] = ta.volatility.donchian_channel_hband(df['high'], df['low'], df['close'], window=20)

        # Round values for display
        df = df.round(2)
        
        # Dimension 4: Signals (سیگنال‌ها)
        df['Signal'] = 'Neutral'
        # Simple SMA Crossover
        df.loc[(df['SMA20'] > df['SMA50']), 'Signal'] = 'Bullish (SMA)'
        df.loc[(df['SMA20'] < df['SMA50']), 'Signal'] = 'Bearish (SMA)'
        # RSI Overbought/Oversold
        df.loc[(df['RSI'] < 30), 'Signal'] = 'Oversold (Buy?)'
        df.loc[(df['RSI'] > 70), 'Signal'] = 'Overbought (Sell?)'
        
        # Dimension 5: Candlestick Patterns (الگوهای شمعی)
        df['Pattern'] = None
        body = (df['close'] - df['open']).abs()
        avg_body = body.rolling(window=10).mean()
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        
        # Doji
        df.loc[body <= (df['high'] - df['low']) * 0.1, 'Pattern'] = 'Doji'
        # Hammer
        df.loc[(lower_shadow >= 2 * body) & (upper_shadow <= 0.1 * body) & (body > 0), 'Pattern'] = 'Hammer'
        # Bullish Engulfing
        df.loc[(df['close'] > df['open']) & (df['close'].shift(1) < df['open'].shift(1)) & 
               (df['close'] > df['open'].shift(1)) & (df['open'] < df['close'].shift(1)), 'Pattern'] = 'Bullish Engulfing'
        # Bearish Engulfing
        df.loc[(df['close'] < df['open']) & (df['close'].shift(1) > df['open'].shift(1)) & 
               (df['close'] < df['open'].shift(1)) & (df['open'] > df['close'].shift(1)), 'Pattern'] = 'Bearish Engulfing'

        # Ensure 'date' is the first column for better readability
        if 'date' in df.columns:
            cols = ['date', 'Signal', 'Pattern'] + [c for c in df.columns if c not in ['date', 'Signal', 'Pattern']]
            df = df[cols]
        
        # Replace NaN with None for JSON compatibility
        df = df.replace({np.nan: None})
        
        return df.to_dict('records')
    except Exception as e:
        print(f"Error in technical analysis: {e}")
        return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/symbols/<market_type>')
@cache.memoize(timeout=3600)
def get_symbols(market_type):
    print(f"DEBUG: Received request for symbols of type: {market_type}")
    symbols = client.get_all_symbols(market_type)
    if isinstance(symbols, dict) and "error" in symbols:
        return jsonify(symbols)
    return jsonify(symbols if symbols else [])

@app.route('/api/heatmap/<market_type>')
@cache.memoize(timeout=1800)
def get_heatmap(market_type):
    # Fetch all symbols for the market to build heatmap
    data = client.get_all_symbols(market_type)
    if isinstance(data, list):
        heatmap_data = []
        for s in data:
            try:
                pcp = float(s.get('pcp', 0))
                vol = float(s.get('v', 0))
                val = float(s.get('z', 0)) # Value of transactions
                if val > 0:
                    heatmap_data.append({
                        'name': s.get('l18'),
                        'sector': s.get('cs', 'سایر'),
                        'value': val,
                        'pcp': pcp
                    })
            except: continue
        return jsonify(heatmap_data)
    return jsonify([])

@app.route('/api/fetch_data', methods=['POST'])
def fetch_data():
    data = request.json
    # Create a cache key based on the request body
    cache_key = str(data)
    cached_res = cache.get(cache_key)
    if cached_res:
        print("DEBUG: Returning cached data")
        return jsonify(cached_res)

    asset_type = data.get('asset_type')
    symbol = data.get('symbol')
    service_type = data.get('service_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    adjusted = data.get('adjusted', True)
    codal_category = data.get('codal_category')

    print(f"Fetching: {service_type} for {symbol} (Dates: {start_date} to {end_date}, Adjusted: {adjusted}, Category: {codal_category})")

    result = []
    # ... (rest of the logic)
    # At the end of fetch_data, before return:
    # cache.set(cache_key, result_to_return, timeout=600)

    if asset_type == 'indices_market':
        if service_type == 'realtime':
            if symbol == "all":
                # Fetch all market indices
                res1 = client.get_indices(1)
                res2 = client.get_indices(2)
                res3 = client.get_indices(3)
                
                result = []
                if res1:
                    result.append({
                        'l18': "شاخص کل بورس",
                        'l30': "شاخص کل بورس",
                        'pc': res1.get('index'),
                        'pcc': res1.get('index_change'),
                        'pcp': round((res1.get('index_change', 0) / (res1.get('index', 1) - res1.get('index_change', 0))) * 100, 2) if res1.get('index') else 0,
                        'time': res1.get('time')
                    })
                if res2:
                    result.append({
                        'l18': "شاخص کل فرابورس",
                        'l30': "شاخص کل فرابورس",
                        'pc': res2.get('index'),
                        'pcc': res2.get('index_change'),
                        'pcp': round((res2.get('index_change', 0) / (res2.get('index', 1) - res2.get('index_change', 0))) * 100, 2) if res2.get('index') else 0,
                        'time': res2.get('time')
                    })
                if isinstance(res3, list):
                    for match in res3:
                        result.append({
                            'l18': match['name'],
                            'l30': match['name'],
                            'pc': match['index'],
                            'pcc': match['index_change'],
                            'pcp': match['index_change_percent'],
                            'pmin': match['min'],
                            'pmax': match['max'],
                            'time': match['time']
                        })
            elif symbol == "شاخص کل بورس":
                res = client.get_indices(1)
                if res:
                    result = [{
                        'l18': "شاخص کل بورس",
                        'l30': "شاخص کل بورس",
                        'pc': res.get('index'),
                        'pcc': res.get('index_change'),
                        'pcp': round((res.get('index_change', 0) / (res.get('index', 1) - res.get('index_change', 0))) * 100, 2) if res.get('index') else 0,
                        'time': res.get('time')
                    }]
            elif symbol == "شاخص کل فرابورس":
                res = client.get_indices(2)
                if res:
                    result = [{
                        'l18': "شاخص کل فرابورس",
                        'l30': "شاخص کل فرابورس",
                        'pc': res.get('index'),
                        'pcc': res.get('index_change'),
                        'pcp': round((res.get('index_change', 0) / (res.get('index', 1) - res.get('index_change', 0))) * 100, 2) if res.get('index') else 0,
                        'time': res.get('time')
                    }]
            else:
                res = client.get_indices(3)
                if isinstance(res, list):
                    # Find the specific index by name (symbol)
                    match = next((item for item in res if item['name'] == symbol), None)
                    if match:
                        # Format it to look like symbol info for the table
                        result = [{
                            'l18': match['name'],
                            'l30': match['name'],
                            'pc': match['index'],
                            'pcc': match['index_change'],
                            'pcp': match['index_change_percent'],
                            'pmin': match['min'],
                            'pmax': match['max'],
                            'time': match['time']
                        }]
    
    elif asset_type == 'indices_industry':
        if service_type == 'realtime':
            # ... (existing realtime logic)
            data = client.get_all_symbols("1")
            if isinstance(data, list):
                if symbol == "all":
                    # Calculate for all sectors
                    sectors = sorted(list(set(s.get('cs') for s in data if s.get('cs'))))
                    result = []
                    for sec in sectors:
                        sector_symbols = [s for s in data if s.get('cs') == sec]
                        if sector_symbols:
                            avg_pcp = sum(float(s.get('pcp', 0)) for s in sector_symbols) / len(sector_symbols)
                            result.append({
                                'l18': sec,
                                'l30': f"شاخص صنعت {sec}",
                                'pc': '-',
                                'pcc': '-',
                                'pcp': round(avg_pcp, 2),
                                'time': datetime.now().strftime("%H:%M:%S"),
                                'count': len(sector_symbols)
                            })
                else:
                    # Calculate for specific sector
                    sector_symbols = [s for s in data if s.get('cs') == symbol]
                    if sector_symbols:
                        avg_pcp = sum(float(s.get('pcp', 0)) for s in sector_symbols) / len(sector_symbols)
                        result = [{
                            'l18': symbol,
                            'l30': f"شاخص صنعت {symbol} (میانگین تغییرات)",
                            'pc': '-',
                            'pcc': '-',
                            'pcp': round(avg_pcp, 2),
                            'time': datetime.now().strftime("%H:%M:%S"),
                            'count': len(sector_symbols)
                        }]
                    else:
                        result = {"error": "نمادی در این صنعت یافت نشد."}
            else:
                result = {"error": "خطا در دریافت داده‌های صنعت."}
        elif service_type in ['history', 'technical']:
            # For industry indices, we calculate a proxy index by averaging top symbols in that sector
            data = client.get_all_symbols("1")
            if isinstance(data, list):
                sector_symbols = [s for s in data if s.get('cs') == symbol]
                if sector_symbols:
                    # Take top 5 symbols by volume to avoid hitting limits too hard
                    top_symbols = sorted(sector_symbols, key=lambda x: float(x.get('v', 0)), reverse=True)[:5]
                    all_histories = []
                    for ts in top_symbols:
                        h = client.get_price_history(ts.get('l18'), adjusted=adjusted)
                        if isinstance(h, list):
                            all_histories.append(pd.DataFrame(h))
                    
                    if all_histories:
                        combined = pd.concat(all_histories)
                        # Average by date
                        if 'date' in combined.columns:
                            combined['date'] = combined['date'].str[:10]
                            # Ensure numeric
                            for col in ['pc', 'pf', 'pmax', 'pmin', 'tvol']:
                                if col in combined.columns:
                                    combined[col] = pd.to_numeric(combined[col], errors='coerce')
                            
                            avg_hist = combined.groupby('date').mean().reset_index()
                            avg_hist = avg_hist.sort_values('date', ascending=False)
                            result = avg_hist.to_dict('records')
                            
                            # Map for technical analysis if needed
                            if service_type == 'technical':
                                for item in result:
                                    item['close'] = item.get('pc')
                                    item['open'] = item.get('pf')
                                    item['high'] = item.get('pmax')
                                    item['low'] = item.get('pmin')
                                    item['volume'] = item.get('tvol')
                                result = calculate_technical_analysis(result)
                        else:
                            result = {"error": "داده‌های تاریخی برای این صنعت یافت نشد."}
                    else:
                        result = {"error": "خطا در دریافت تاریخچه نمادهای صنعت."}
                else:
                    result = {"error": "نمادی در این صنعت یافت نشد."}
            else:
                result = {"error": "خطا در دریافت لیست نمادها."}

    elif service_type == 'realtime':
        res = client.get_symbol_info(symbol)
        if res: result = [res]
    elif service_type == 'history':
        result = client.get_price_history(symbol, adjusted=adjusted)
    elif service_type == 'technical':
        # For indices, we might need to use history instead of candlestick
        if asset_type.startswith('indices'):
            result = client.get_price_history(symbol, adjusted=False)
            # Map history format to candlestick format (open, high, low, close)
            if isinstance(result, list) and len(result) > 0:
                for item in result:
                    if 'pc' in item and 'close' not in item: item['close'] = item['pc']
                    if 'pf' in item and 'open' not in item: item['open'] = item['pf']
                    if 'pmax' in item and 'high' not in item: item['high'] = item['pmax']
                    if 'pmin' in item and 'low' not in item: item['low'] = item['pmin']
                    if 'tvol' in item and 'volume' not in item: item['volume'] = item['tvol']
        else:
            # Use daily adjusted candles (type 3) for technical analysis
            result = client.get_candlestick(symbol, adjusted=True, type=3)
            
        if isinstance(result, dict) and "error" in result:
            return jsonify(result)
        if result and isinstance(result, list):
            result = calculate_technical_analysis(result)
        else:
            return jsonify({"error": "داده‌های مورد نیاز برای تحلیل تکنیکال یافت نشد."})
    elif service_type == 'client_type':
        result = client.get_price_history(symbol, data_type=1, adjusted=adjusted)
    elif service_type == 'candlestick':
        result = client.get_candlestick(symbol, adjusted=adjusted)
    elif service_type == 'transactions':
        result = client.get_transactions(symbol)
    elif service_type == 'shareholders':
        result = client.get_shareholders(symbol)
    elif service_type == 'nav':
        res = client.get_nav(symbol)
        if res: result = [res]
    elif service_type == 'codal':
        result = client.get_codal_announcements(symbol=symbol, category=codal_category, date_start=start_date, date_end=end_date)
    elif service_type == 'indices':
        result = client.get_indices(asset_type)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result)

    print(f"Raw result count: {len(result) if isinstance(result, list) else 'N/A'}")

    # Filter by date if applicable
    if result and isinstance(result, list) and start_date and end_date:
        # Normalize separators to - for consistent comparison
        start_date = start_date.replace('/', '-')
        end_date = end_date.replace('/', '-')
        
        filtered_result = []
        mismatch_detected = False
        
        for item in result:
            # Check multiple possible date keys
            item_date = item.get('date') or item.get('time') or item.get('date_publish') or item.get('date_send')
            if item_date and len(item_date) >= 10:
                # Normalize item date separator as well
                item_date_norm = item_date[:10].replace('/', '-')
                
                # Check for Jalali (13xx or 14xx) vs Gregorian (20xx) mismatch
                if item_date_norm.startswith(('13', '14')) and start_date.startswith('20'):
                    mismatch_detected = True
                    break
                
                if start_date <= item_date_norm <= end_date:
                    filtered_result.append(item)
            elif item_date: # Just time or short format
                filtered_result.append(item)
        
        if mismatch_detected:
            print("Mismatched date formats detected (Jalali vs Gregorian). Skipping filter.")
            # If mismatch, we return all data instead of empty list
        else:
            result = filtered_result

    # Cache the final result for 10 minutes
    cache.set(str(request.json), result if result else [], timeout=600)

    return jsonify(result if result else [])

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    table_data = data.get('data')
    format = data.get('format')
    filename = data.get('filename', 'export')

    df = pd.DataFrame(table_data)
    
    if format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        return send_file(output, download_name=f"{filename}.xlsx", as_attachment=True)
    
    elif format == 'csv':
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        return send_file(output, download_name=f"{filename}.csv", as_attachment=True)

    return "Invalid format", 400

@app.route('/api/market_status')
@cache.cached(timeout=60)
def get_market_status():
    return jsonify({'status': 'در حال فعالیت', 'time': datetime.now().strftime('%H:%M:%S')})

if __name__ == '__main__':
    print("Starting Flask server on http://0.0.0.0:5000 ...")
    app.run(debug=False, host='0.0.0.0', port=5000)
