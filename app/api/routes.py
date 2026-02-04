from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import datetime
import jdatetime
import time
import random
import threading
import io
import pandas as pd
import base64
import zipfile
import logging
import json
import hashlib
from functools import wraps

from app.services.tsetmc import client
from app.services.tgju import tgju_client
from app.services.technical_analysis import TechnicalAnalyzer
from app.services.local_ai_assistant import ai_assistant
from app.services.enhanced_ai import enhanced_ai, EnhancedAIAssistant
from app.services.technical_analysis_enhanced import TechnicalAnalyzer as EnhancedTechnicalAnalyzer
from app.services.autonomous_ai import content_generator, continuous_learning
from app.database import db
from app.utils.core_utils import PROXY_URL, stats
from app import cache
from app.utils.circuit_breaker import get_circuit_status, circuit_breaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

# API Rate Limiting (سادہ لیکن مؤثر)
_rate_limit_store = {}  # IP: [timestamps]

def rate_limit(max_requests=100, window_seconds=60):
    """
    سادہ rate limiter decorator
    - ہر IP کے لیے max_requests سے زیادہ نہیں
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr or 'unknown'
            now = time.time()
            
            # IP کے timestamps کو صاف کریں
            if client_ip not in _rate_limit_store:
                _rate_limit_store[client_ip] = []
            
            # پرانے timestamps کو ہٹائیں
            _rate_limit_store[client_ip] = [
                t for t in _rate_limit_store[client_ip]
                if (now - t) < window_seconds
            ]
            
            # Limit check
            if len(_rate_limit_store[client_ip]) >= max_requests:
                logger.warning(f"⚠️ Rate limit exceeded for {client_ip}")
                return jsonify({
                    "error": "درخواستیں بہت زیادہ ہیں - براہ مہربانی کچھ دیر میں دوبارہ کوشش کریں",
                    "retry_after": window_seconds
                }), 429
            
            # Request record کریں
            _rate_limit_store[client_ip].append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Import updates routes

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/api_test')
def api_test():
    return render_template('api_test.html')

@main_bp.route('/management')
def management():
    return render_template('management.html')

@main_bp.route('/api/clear_cache', methods=['POST'])
def clear_cache():
    cache.clear()
    return jsonify({"status": "success", "message": "حافظه موقت با موفقیت پاکسازی شد."})

@main_bp.route('/api/market_status')
def get_market_status():
    """Returns the current status of the market."""
    return jsonify({
        "status": "در حال فعالیت",
        "time": datetime.now().strftime("%H:%M:%S"),
        "stats": {
            "global": stats["global"],
            "services": stats["services"],
            "history": stats["history"]
        }
    })

@main_bp.route('/api/market/overview')
def get_market_overview():
    """Returns comprehensive market overview."""
    try:
        # Get market indices
        indices = []
        for idx_type in ["1", "2"]:  # bourse and farabourse
            try:
                data = client.get_indices(idx_type)
                if isinstance(data, list) and data:
                    item = data[0]
                    indices.append({
                        "name": "شاخص کل" if idx_type == "1" else "شاخص کل فرابورس",
                        "value": item.get('value') or item.get('index'),
                        "change": item.get('change'),
                        "change_percent": item.get('change_percent')
                    })
            except Exception as e:
                logger.warning(f"Failed to get index {idx_type}: {e}")

        # Get market statistics
        total_symbols = db.get_total_symbols_count()
        
        return jsonify({
            "indices": indices,
            "total_symbols": total_symbols,
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "market_status": "open" if 9 <= datetime.now().hour <= 12 else "closed"
        })
    except Exception as e:
        return jsonify({"error": f"Failed to get market overview: {str(e)}"}), 500

@main_bp.route('/api/health')
def health_check():
    """Diagnostic endpoint to check connectivity status with circuit breaker info."""
    try:
        # Check circuit breaker status
        circuit_status = get_circuit_status()
        
        # Safe request test with circuit breaker protection
        test_res = None
        try:
            from app.utils.circuit_breaker import TSETMC_CIRCUIT, get_circuit_breaker
            cb = get_circuit_breaker(TSETMC_CIRCUIT)
            if cb.allow_request():
                test_res = client._make_request("Api/Tsetmc/Index.php", {"type": "1"})
        except Exception as e:
            logger.warning(f"Health check API call failed: {e}")
        
        # Determine status safely
        status = "OK"
        if test_res is None:
            status = "WARNING"
        elif isinstance(test_res, dict) and "error" in test_res:
            status = "FAILED"
        elif not isinstance(test_res, (dict, list)):
            status = "WARNING"
        
        return jsonify({
            "status": status,
            "proxy": PROXY_URL,
            "active_client": client.client_name,
            "circuit_breakers": circuit_status,
            "test_response": str(test_res)[:200] if test_res else "None"
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "ERROR",
            "error": str(e),
            "proxy": PROXY_URL
        }), 500


@main_bp.route('/api/circuit-status')
def circuit_status():
    """Get circuit breaker status for all services."""
    try:
        return jsonify({
            "status": "success",
            "circuits": get_circuit_status()
        })
    except Exception as e:
        logger.error(f"Circuit status error: {e}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/symbols/<market_type>')
def get_symbols(market_type):
    if market_type == 'tgju':
        return jsonify(tgju_client.get_all_symbols())
        
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    symbols = client.get_all_symbols(market_type, force_refresh=refresh)
    if isinstance(symbols, dict) and "error" in symbols:
        return jsonify(symbols)
    return jsonify(symbols if symbols else [])

@main_bp.route('/api/symbols')
def get_all_symbols():
    """Get all symbols from all markets."""
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    all_symbols = []
    
    # Get symbols from all markets
    markets = ['1', '2', '4', '5']  # bourse, farabourse, base, etf
    for market in markets:
        try:
            symbols = client.get_all_symbols(market, force_refresh=refresh)
            if isinstance(symbols, list):
                all_symbols.extend(symbols)
        except Exception as e:
            logger.warning(f"Failed to get symbols for market {market}: {e}")
    
    return jsonify(all_symbols)

@main_bp.route('/api/sync_registry', methods=['POST'])
def sync_registry():
    """Manual trigger for persistent registry update. Runs in background."""
    def run_sync():
        logger.info("Starting manual registry synchronization...")
        for t in range(1, 6):
            try:
                client._fetch_symbols_by_type(str(t), force_refresh=True)
                logger.info(f"Sync complete for market type {t}")
                if t < 5: time.sleep(random.uniform(5, 10))
            except Exception as e:
                logger.error(f"Sync failed for type {t}: {e}")
        logger.info("Manual registry synchronization finished.")

    threading.Thread(target=run_sync, daemon=True).start()
    return jsonify({
        "status": "Started", 
        "message": "Registry synchronization started in the background.",
        "registry_count": db.get_total_symbols_count()
    })

@main_bp.route('/api/fetch_data', methods=['POST'])
@rate_limit(max_requests=50, window_seconds=60)  # ہر منٹ میں 50 requests
def fetch_data():
    """
    Input validation شامل کریں
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON data"}), 400
    
    # Input validation
    try:
        asset_type = data.get('asset_type', 'tse').strip()
        if not asset_type: asset_type = 'tse'
        
        symbol = data.get('symbol', '').strip()
        candle_count = int(data.get('candle_count', 100))
        force_refresh = bool(data.get('refresh', False))
        
        if candle_count < 1 or candle_count > 5000:
            return jsonify({"error": "candle_count 1 سے 5000 کے درمیان ہونی چاہیے"}), 400
        
        if symbol and len(symbol) > 50:
            return jsonify({"error": "symbol بہت لمبی ہے"}), 400
        
    except (ValueError, TypeError) as e:
        logger.error(f"Input validation error: {e}")
        return jsonify({"error": f"غلط input: {str(e)[:50]}"}), 400
    
    # Stable Cache key using MD5 hash of sorted JSON
    data_str = json.dumps(data, sort_keys=True)
    cache_key = hashlib.md5(data_str.encode()).hexdigest()
    
    if not force_refresh:
        cached_res = cache.get(cache_key)
        if cached_res: 
            logger.debug(f"Cache hit for {symbol}")
            return jsonify(cached_res)

    asset_type = data.get('asset_type')
    symbol = data.get('symbol')
    service_type = data.get('service_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    adjusted = data.get('adjusted', True)
    timeframe = data.get('timeframe', 'daily')
    candle_count = data.get('candle_count')

    result = []
    
    if asset_type == 'tgju':
        result = tgju_client.get_history(symbol)
    elif asset_type == 'indices_market':
        if service_type == 'realtime':
            res1 = client.get_indices(1, force_refresh=force_refresh)
            res2 = client.get_indices(2, force_refresh=force_refresh)
            result = []
            if isinstance(res1, list) and res1: 
                item = res1[0]
                result.append({'l18': 'شاخص کل', 'pc': item.get('value') or item.get('index')})
            if isinstance(res2, list) and res2: 
                item = res2[0]
                result.append({'l18': 'شاخص کل فرابورس', 'pc': item.get('value') or item.get('index')})
        elif service_type in ['history', 'technical']:
            result = client.get_price_history(symbol, adjusted=False, force_refresh=force_refresh)
    else: # Default normal symbol
        if service_type == 'realtime':
            res = client.get_symbol_info(symbol)
            result = [res] if res else []
        elif service_type in ['history', 'technical']:
            result = client.get_price_history(symbol, adjusted=adjusted, force_refresh=force_refresh)
        elif service_type == 'client_type':
            result = client.get_client_type(symbol, force_refresh=force_refresh)
        elif service_type == 'transactions':
            result = client.get_transactions(symbol)
        elif service_type == 'shareholders':
            result = client.get_shareholders(symbol)
        elif service_type == 'codal':
            category = data.get('codal_category')
            result = client.get_codal_announcements(symbol=symbol, category=category)

    # Handle error response (but don't error if it's mock data)
    if isinstance(result, dict) and "error" in result and not force_refresh:
        # If real API failed, try mock fallback once
        logger.info(f"Primary fetch failed for {symbol}, attempting mock fallback...")
        result = client._generate_mock_history(symbol)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result)

    if service_type == 'technical' and isinstance(result, list) and len(result) > 0:
        result = TechnicalAnalyzer.prepare_ohlcv_data(result)
        
        # 1. Fetch Index Data for Beta calculation
        index_data = None
        if asset_type != 'indices_market':
            try:
                # Use "شاخص کل" which is the handled keyword in TSETMCClient
                index_symbol = "شاخص کل"
                index_data = client.get_price_history(index_symbol, adjusted=False)
                if not isinstance(index_data, list): index_data = None
            except Exception as e:
                logger.debug(f"Index fetch failed for beta: {e}")
                pass

        # 2. Resample if weekly
        if timeframe == 'weekly': 
            result = TechnicalAnalyzer.resample_to_weekly(result)
        
        # 3. Calculate Technical Analysis (ON FULL HISTORY)
        result = TechnicalAnalyzer.calculate_technical_analysis(result, index_data=index_data)
        
        # 4. NOW Apply Date Range Filtering for display
        if (start_date or end_date) and result:
            try:
                filtered = []
                for item in result:
                    item_date = item.get('date', '')[:10]
                    if start_date and item_date < start_date: continue
                    if end_date and item_date > end_date: continue
                    filtered.append(item)
                
                # If everything was filtered out, keep at least one record to avoid error UI
                if not filtered and result:
                    filtered = [result[0]]
                result = filtered
            except Exception as e:
                logger.error(f"Date Filter Error: {e}")
        
        # 5. Generate Chart
        if len(result) > 0:
            try:
                buf = TechnicalAnalyzer.generate_chart_image(result, symbol, timeframe=timeframe)
                if buf: result[0]['chart_image'] = base64.b64encode(buf.getvalue()).decode('utf-8')
            except Exception as e:
                logger.error(f"Chart Generation Error: {e}")

    if result and isinstance(result, list) and candle_count:
        try: result = result[:int(candle_count)]
        except: pass

    cache.set(cache_key, result if result else [], timeout=600)
    return jsonify(result if result else [])

@main_bp.route('/api/technical-analysis/<symbol>')
def get_technical_analysis(symbol):
    """Get technical analysis for a specific symbol."""
    try:
        # Get price history
        history = client.get_price_history(symbol, adjusted=True)
        if not isinstance(history, list) or not history:
            return jsonify({"error": "No historical data available"}), 404

        # Prepare data for technical analysis
        prepared_data = TechnicalAnalyzer.prepare_ohlcv_data(history)
        if not prepared_data:
            return jsonify({"error": "Failed to prepare data for analysis"}), 500

        # Get technical indicators
        analysis = {
            "symbol": symbol,
            "data_points": len(prepared_data),
            "indicators": {},
            "signals": {}
        }

        # Calculate basic indicators
        if len(prepared_data) > 14:
            # RSI
            try:
                rsi = TechnicalAnalyzer.calculate_rsi(prepared_data['close'])
                analysis["indicators"]["rsi"] = rsi.iloc[-1] if not rsi.empty else None
            except:
                analysis["indicators"]["rsi"] = None

            # MACD
            try:
                macd, signal, hist = TechnicalAnalyzer.calculate_macd(prepared_data['close'])
                analysis["indicators"]["macd"] = {
                    "macd": macd.iloc[-1] if not macd.empty else None,
                    "signal": signal.iloc[-1] if not signal.empty else None,
                    "histogram": hist.iloc[-1] if not hist.empty else None
                }
            except:
                analysis["indicators"]["macd"] = None

            # Bollinger Bands
            try:
                upper, middle, lower = TechnicalAnalyzer.calculate_bollinger_bands(prepared_data['close'])
                analysis["indicators"]["bollinger"] = {
                    "upper": upper.iloc[-1] if not upper.empty else None,
                    "middle": middle.iloc[-1] if not middle.empty else None,
                    "lower": lower.iloc[-1] if not lower.empty else None
                }
            except:
                analysis["indicators"]["bollinger"] = None

        # Generate signals
        analysis["signals"] = TechnicalAnalyzer.generate_signals(prepared_data)

        return jsonify(analysis)

    except Exception as e:
        logger.error(f"Technical analysis error for {symbol}: {e}")
        return jsonify({"error": f"Failed to analyze {symbol}: {str(e)}"}), 500

@main_bp.route('/api/ai_package', methods=['POST'])
def generate_ai_package():
    data = request.json
    symbol = data.get('symbol', 'Unknown')
    tech_data = data.get('data', [])
    weekly_data = data.get('weekly_data', [])
    if not tech_data: return jsonify({"error": "داده‌ای یافت نشد."})
    
    # 0. Preparation
    latest = tech_data[0]
    curr_price = latest.get('close', 0)
    supports = latest.get('supports', [])
    resistances = latest.get('resistances', [])
    rsi = latest.get('RSI', 50)
    signal = latest.get('Signal', 'Neutral')
    date_str = datetime.now().strftime('%Y-%m-%d')
    jalali_today = jdatetime.date.fromgregorian(date=datetime.now().date()).strftime('%Y/%m/%d')
    
    # 1. Strategy Calculation
    strategies = TechnicalAnalyzer.generate_strategy_matrix(curr_price, supports, resistances)
    
    # 2. Level Extraction (Ensure 5 levels)
    def _get_lvl(l, i):
        if i >= len(l): return "---"
        item = l[i]
        val = item.get('value', 0) if isinstance(item, dict) else item
        return str(int(val)) if val else "---"

    s_list = [_get_lvl(supports, i) for i in range(5)]
    r_list = [_get_lvl(resistances, i) for i in range(5)]
    
    # 3. Wave & Scenario Guessing (Logic-based)
    scenario_weights = {"continuation": 40, "correction": 30, "reversal": 30}
    if "Bullish" in signal: 
        scenario_weights = {"continuation": 60, "correction": 25, "reversal": 15}
        wave_str = "موج ۳ از ۵ صعودی"
    elif "Bearish" in signal:
        scenario_weights = {"continuation": 55, "correction": 30, "reversal": 15}
        wave_str = "موج C از اصلاح بزرگ"
    else:
        wave_str = "موج ۴ رنج"

    # --- START 7-SLIDE MARKDOWN GENERATION ---
    report = f"""# **📊 پروتکل تحلیل تکنیکال پیشرفته ۷ اسلایدی (نسخه ۴.۰)**

---

## **🖥️ اسلاید ۱: شناسنامه تحلیلی و وضعیت کلی**

### **اطلاعات تحلیلگر:**
```
👤 تحلیلگر: شکور علیشاهی
📞 تماس: 09124467903
📅 تاریخ تحلیل: {jalali_today}
📊 نماد: {symbol}
⏰ بازه تحلیلی: کوتاه‌مدت (۱ هفته) | میان‌مدت (۱ ماه) | بلندمدت (۳ ماه)
```

### **وضعیت کلی بازار:**
```
🎯 قیمت فعلی: {int(curr_price):,} تومان
📈 سیگنال: {signal}
💰 حجم معاملات: {int(latest.get('volume', 0)):,}
📊 الگوی شمعی: {latest.get('Pattern', 'نامشخص')}
🔼 سقف/کف روز: {int(latest.get('high', 0)):,} / {int(latest.get('low', 0)):,}
```

### **توصیه اولیه:**
«بر اساس تحلیل اولیه، وضعیت **{signal}** در نمودار {symbol} مشاهده می‌شود.»

---

## **📈 اسلاید ۲: تحلیل سه‌بعدی تایم‌فریم‌ها**

### **الف) نمودار روزانه کوتاه‌مدت (۱۵ روز):**
* روند فعلی: {"صعودی" if rsi > 50 else "نزولی"}
* میانگین متحرک ۲۰ روزه: {int(latest.get('SMA20', 0)):,}
* قدرت روند (ADX): {latest.get('ADX', '---')}

### **ب) نمودار روزانه بلندمدت (۳ سال):**
* موج فعلی: {wave_str}
* اهداف میان‌مدت: {int(curr_price * 1.1):,}, {int(curr_price * 1.25):,}

### **ج) نمودار هفتگی:**
* وضعیت روند اصلی: {"قدرتمند" if abs(rsi-50) > 10 else "رنج"}
* پیش‌بینی بازه آتی: {int(curr_price * 0.95):,} تا {int(curr_price * 1.05):,}

---

## **🎭 اسلاید ۳: تحلیل امواج و الگوهای هارمونیک**

### **موج‌شمار الیوت جامع:**
- **موج اصلی:** {wave_str}
- **نسبت فیبوناچی کلیدی:** {latest.get('fibonacci', {}).get('61.8%', '---')}
- **تعداد زیرموج‌ها:** تکمیل شده

### **الگوهای هارمونیک و PRZ:**
- **الگوی شناسایی شده:** {latest.get('Pattern') or "شناسایی نشده"}
- **منطقه PRZ خرید:** {s_list[0]} تا {s_list[1]}
- **منطقه PRZ فروش:** {r_list[0]} تا {r_list[1]}

---

## **📍 اسلاید ۴: سطوح قیمتی حیاتی و واکنش به شکست**

### **🔺 ۵ سطح مقاومت بالایی:**
1. **{r_list[0]}** (مقاومت روانی اول)
2. **{r_list[1]}** (هدف نوسانی)
3. **{r_list[2]}** (سد اصلی روند)
4. **{r_list[3]}** (هدف میان‌مدت)
5. **{r_list[4]}** (سقف تاریخی/تحلیلی)

### **🔻 ۵ سطح حمایت پایینی:**
1. **{s_list[0]}** (حمایت معتبر اول)
2. **{s_list[1]}** (نقطه بازگشت احتمالی)
3. **{s_list[2]}** (کف کانال فعلی)
4. **{s_list[3]}** (حمایت روانی سنگین)
5. **{s_list[4]}** (کف امن سرمایه‌گذاری)

---

## **📊 اسلاید ۵: ماتریس عملیاتی ۶ پروفایل**"""

    # Add Matrix Table
    report += "\n| پروفایل | تیپ شخصیتی | افق زمانی | ورود | حد سود | حد ضرر | R/R |\n"
    report += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for s in strategies:
        entry = s['نقطه ورود']
        if isinstance(entry, (int, float)): entry = f"{int(entry):,}"
        report += f"| {s['پروفایل سرمایه‌گذار']} | {s['تیپ شخصیتی']} | {s['افق زمانی']} | {entry} | {int(s['حد سود (TP)']):,} | {int(s['حد ضرر (SL)']):,} | {s['R/R']} |\n"

    report += f"""
---

## **🎲 اسلاید ۶: سناریوهای محتمل با وزن‌دهی عددی**

### **سناریوی ۱: ادامه روند (وزن: {scenario_weights['continuation']}%)**
- تریگر فعال‌ساز: تثبیت بالای {r_list[0]}
- هدف اول: {r_list[1]}

### **سناریوی ۲: اصلاح سالم (وزن: {scenario_weights['correction']}%)**
- محدوده اصلاح: {s_list[0]}
- دلیل: اشباع خرید موقت در اندیکاتورها

### **سناریوی ۳: بازگشت روند (وزن: {scenario_weights['reversal']}%)**
- هشدار شکست: زیر {s_list[1]}
- هدف نزولی: {s_list[2]}

---

## **✅ اسلاید ۷: جمع‌بندی و توصیه نهایی**

### **خلاصه تراز:**
- امتیاز کلی: **{round(rsi/10, 1)} / ۱۰**
- برآیند سیگنال‌ها: **{signal}**

### **توصیه اختصاصی:**
- **محافظه‌کار:** صبر در نقاط حمایتی {s_list[1]}
- **تهاجمی:** ورود پله‌ای در محدوده {curr_price}

### **نقطه ابطال تحلیل:**
⛔ شکست قیمت **{s_list[2]}** به سمت پایین یا حجم مشکوک در مقاومت **{r_list[0]}**.

**تحلیلگر: شکور علیشاهی | 09124467903**
"""

    return jsonify({
        "json": {
            "daily": tech_data, 
            "weekly": weekly_data,
            "strategies": strategies
        }, 
        "markdown": report, 
        "filename": f"ATAP_Pro_7Slide_{symbol}"
    })

@main_bp.route('/api/download_comprehensive', methods=['POST'])
def download_comprehensive():
    try:
        data = request.json
        symbol = data.get('symbol', 'Unknown')
        daily_data = data.get('daily_data', [])
        weekly_data = data.get('weekly_data', [])
        report_md = data.get('markdown', '')

        if not daily_data:
            return jsonify({"error": "داده‌ای برای دانلود وجود ندارد."}), 400

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            # 1. Daily Data Excel
            df_daily = pd.DataFrame(daily_data)
            # Ensure proper sort for excel
            if 'date' in df_daily.columns:
                df_daily = df_daily.sort_values('date', ascending=False)
            
            excel_daily = io.BytesIO()
            with pd.ExcelWriter(excel_daily, engine='xlsxwriter') as writer:
                df_daily.to_excel(writer, index=False, sheet_name='Daily Analysis')
                # Add basic formatting
                workbook = writer.book
                worksheet = writer.sheets['Daily Analysis']
                header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
                for col_num, value in enumerate(df_daily.columns.values):
                    worksheet.write(0, col_num, value, header_format)
            
            zip_file.writestr(f"1-Daily_Data_{symbol}.xlsx", excel_daily.getvalue())

            # 2. Weekly Data Excel
            if weekly_data:
                df_weekly = pd.DataFrame(weekly_data)
                if 'date' in df_weekly.columns:
                    df_weekly = df_weekly.sort_values('date', ascending=False)
                
                excel_weekly = io.BytesIO()
                with pd.ExcelWriter(excel_weekly, engine='xlsxwriter') as writer:
                    df_weekly.to_excel(writer, index=False, sheet_name='Weekly Analysis')
                zip_file.writestr(f"2-Weekly_Data_{symbol}.xlsx", excel_weekly.getvalue())

            # 3. Daily Chart
            chart_daily = TechnicalAnalyzer.generate_chart_image(daily_data, symbol, timeframe='daily')
            if chart_daily:
                zip_file.writestr(f"3-Chart_Daily_{symbol}.png", chart_daily.getvalue())

            # 4. Weekly Chart
            if weekly_data:
                # Need to calculate technical if not already there, or just use the data
                chart_weekly = TechnicalAnalyzer.generate_chart_image(weekly_data, symbol, timeframe='weekly')
                if chart_weekly:
                    zip_file.writestr(f"4-Chart_Weekly_{symbol}.png", chart_weekly.getvalue())

            # 5. Markdown Report
            if report_md:
                # Add a UTF-8 BOM for Windows compatibility if needed, or just plain text
                zip_file.writestr(f"5-Full_Analysis_Report_{symbol}.md", report_md.encode('utf-8'))

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"AI_Package_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        )
    except Exception as e:
        print(f"Comprehensive Download Error: {e}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/download', methods=['POST'])
def download():
    data = request.json
    daily_data = data.get('daily_data') or data.get('data')
    symbol, fmt = data.get('symbol', 'Symbol'), data.get('format')
    timeframe = data.get('timeframe', 'daily')
    if fmt == 'image' and daily_data:
        df = pd.DataFrame(daily_data)
        if 'date' in df.columns: df = df.sort_values('date')
        buf = TechnicalAnalyzer.generate_chart_image(df, symbol, timeframe=timeframe)
        return send_file(buf, download_name=f"{symbol}.png", as_attachment=True, mimetype='image/png')
    return jsonify({"error": "Format not supported"}), 400

@main_bp.route('/api/ai/analyze/<symbol>', methods=['GET'])
def ai_analyze_symbol(symbol):
    """AI-powered technical analysis for a symbol."""
    try:
        result = ai_assistant.analyze_symbol(symbol)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/ai/report', methods=['POST'])
def ai_generate_report():
    """Generate a professional report based on user query."""
    try:
        data = request.json
        query = data.get('query', 'گزارش کلی بازار را ارائه دهید')
        result = ai_assistant.generate_report(query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/ai/update_model', methods=['POST'])
def ai_update_model():
    """Update the AI model with new data."""
    try:
        ai_assistant.update_model()
        return jsonify({"message": "AI model updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/ai/status', methods=['GET'])
def ai_status():
    """Get AI learning status."""
    try:
        status = {
            "model_loaded": ai_assistant.model is not None,
            "last_update": ai_assistant.last_update.isoformat(),
            "continuous_learning_active": ai_assistant.learning_thread.is_alive(),
            "model_path": ai_assistant.model_path
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ Enhanced AI Endpoints ============

@main_bp.route('/api/ai/enhanced/analyze/<symbol>', methods=['GET'])
def enhanced_ai_analyze(symbol):
    """Enhanced AI-powered technical analysis with 20+ features."""
    try:
        # Get price history
        history = client.get_price_history(symbol, adjusted=True)
        if not history or len(history) < 50:
            return jsonify({"error": f"داده کافی برای نماد {symbol} یافت نشد"}), 404
        
        # Run enhanced analysis
        result = enhanced_ai.analyze_symbol(symbol, history)
        
        if result:
            return jsonify(result.to_dict())
        else:
            return jsonify({"error": "خطا در تحلیل"}), 500
            
    except Exception as e:
        logger.error(f"Enhanced AI analysis error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/ai/enhanced/report/<symbol>', methods=['GET'])
def enhanced_ai_report(symbol):
    """Generate comprehensive markdown report."""
    try:
        # Get price history
        history = client.get_price_history(symbol, adjusted=True)
        if not history or len(history) < 50:
            return jsonify({"error": f"داده کافی برای نماد {symbol} یافت نشد"}), 404
        
        # Run enhanced analysis
        result = enhanced_ai.analyze_symbol(symbol, history)
        
        if result:
            # Generate markdown report
            report = enhanced_ai.generate_report(result)
            return jsonify({
                "symbol": symbol,
                "report": report,
                "analysis": result.to_dict()
            })
        else:
            return jsonify({"error": "خطا در تولید گزارش"}), 500
            
    except Exception as e:
        logger.error(f"Enhanced AI report error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/ai/enhanced/status', methods=['GET'])
def enhanced_ai_status():
    """Get enhanced AI model status."""
    try:
        status = {
            "model_loaded": enhanced_ai.model_loaded,
            "model_exists": enhanced_ai.model is not None,
            "accuracy": enhanced_ai.accuracy,
            "last_update": enhanced_ai.last_update.isoformat(),
            "feature_count": len(enhanced_ai.feature_names),
            "feature_names": enhanced_ai.feature_names,
            "ensemble_models": list(enhanced_ai.ensemble_models.keys())
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/ai/advanced/indicators/<symbol>', methods=['GET'])
def advanced_indicators(symbol):
    """Get advanced technical indicators for a symbol."""
    try:
        # Get price history
        history = client.get_price_history(symbol, adjusted=True)
        if not history:
            return jsonify({"error": "داده‌ای یافت نشد"}), 404
        
        # Prepare data
        df = EnhancedTechnicalAnalyzer.prepare_ohlcv_data(history)
        if df.empty:
            return jsonify({"error": "خطا در پردازش داده"}), 500
        
        close = df['close']
        
        # Calculate all indicators
        indicators = {
            "symbol": symbol,
            "sma": {
                "sma_20": float(EnhancedTechnicalAnalyzer.calculate_sma(close, 20).iloc[-1]),
                "sma_50": float(EnhancedTechnicalAnalyzer.calculate_sma(close, 50).iloc[-1]),
                "sma_200": float(EnhancedTechnicalAnalyzer.calculate_sma(close, 200).iloc[-1])
            },
            "ema": {
                "ema_12": float(EnhancedTechnicalAnalyzer.calculate_ema(close, 12).iloc[-1]),
                "ema_26": float(EnhancedTechnicalAnalyzer.calculate_ema(close, 26).iloc[-1])
            },
            "rsi": float(EnhancedTechnicalAnalyzer.calculate_rsi(close).iloc[-1]),
        }
        
        macd, signal, hist = EnhancedTechnicalAnalyzer.calculate_macd(close)
        indicators["macd"] = {
            "macd": float(macd.iloc[-1]),
            "signal": float(signal.iloc[-1]),
            "histogram": float(hist.iloc[-1])
        }
        
        upper, middle, lower = EnhancedTechnicalAnalyzer.calculate_bollinger_bands(close)
        indicators["bollinger_bands"] = {
            "upper": float(upper.iloc[-1]),
            "middle": float(middle.iloc[-1]),
            "lower": float(lower.iloc[-1])
        }
        
        # ADX and ATR require high/low data
        if 'high' in df.columns and 'low' in df.columns:
            indicators["atr"] = float(EnhancedTechnicalAnalyzer.calculate_atr(df).iloc[-1])
            indicators["adx"] = float(EnhancedTechnicalAnalyzer.calculate_adx(df).iloc[-1])
        
        indicators["obv"] = float(EnhancedTechnicalAnalyzer.calculate_obv(df).iloc[-1])
        
        # Generate signals
        signals = EnhancedTechnicalAnalyzer.generate_signals(df)
        indicators["signals"] = signals
        
        # Support/Resistance
        sr_levels = EnhancedTechnicalAnalyzer.find_support_resistance(df)
        indicators["support_resistance"] = sr_levels
        
        # Candlestick patterns
        patterns = EnhancedTechnicalAnalyzer.detect_candlestick_patterns(df)
        indicators["patterns"] = patterns
        
        return jsonify(indicators)
        
    except Exception as e:
        logger.error(f"Advanced indicators error: {e}")
        return jsonify({"error": str(e)}), 500


# ============ Autonomous AI Content Generation Endpoints ============

@main_bp.route('/api/ai/content/generate/analysis', methods=['POST'])
def generate_analysis_content():
    """Generate autonomous AI analysis content."""
    try:
        data = request.json
        
        symbol = data.get('symbol')
        trend = data.get('trend', 'neutral')
        indicators = data.get('indicators', {})
        supports = data.get('supports', [])
        resistances = data.get('resistances', [])
        recommendation = data.get('recommendation', 'نگهداری')
        analysis_text = data.get('analysis_text', '')
        
        if not symbol:
            return jsonify({"error": "نماد الزامی است"}), 400
        
        # Generate content
        content = content_generator.generate_analysis(
            symbol=symbol,
            trend=trend,
            indicators=indicators,
            supports=supports,
            resistances=resistances,
            recommendation=recommendation,
            analysis_text=analysis_text
        )
        
        return jsonify({
            "content_id": content.content_id,
            "title": content.title,
            "body": content.body,
            "keywords": content.keywords,
            "generated_at": content.generated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/ai/content/generate/summary', methods=['POST'])
def generate_summary_content():
    """Generate market summary content."""
    try:
        data = request.json or {}
        
        stats = {
            'total_symbols': data.get('total_symbols', db.get_total_symbols_count()),
            'bullish_count': data.get('bullish_count', 0),
            'bearish_count': data.get('bearish_count', 0),
            'neutral_count': data.get('neutral_count', 0),
            'top_gainers': data.get('top_gainers', ''),
            'top_losers': data.get('top_losers', '')
        }
        
        content = content_generator.generate_market_summary(stats)
        
        return jsonify({
            "content_id": content.content_id,
            "title": content.title,
            "body": content.body,
            "keywords": content.keywords,
            "generated_at": content.generated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/ai/content/generate/educational', methods=['POST'])
def generate_educational_content():
    """Generate educational content."""
    try:
        data = request.json
        
        title = data.get('title')
        topic = data.get('topic')
        content_text = data.get('content')
        
        if not title or not content_text:
            return jsonify({"error": "عنوان و محتوا الزامی هستند"}), 400
        
        content = content_generator.generate_educational(
            title=title,
            topic=topic or title,
            content=content_text
        )
        
        return jsonify({
            "content_id": content.content_id,
            "title": content.title,
            "body": content.body,
            "keywords": content.keywords,
            "generated_at": content.generated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Educational content error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/ai/content/feedback', methods=['POST'])
def submit_content_feedback():
    """Submit feedback for content to improve learning."""
    try:
        data = request.json
        
        content_id = data.get('content_id')
        content_type = data.get('content_type')
        rating = data.get('rating', 0)
        was_helpful = data.get('was_helpful', False)
        comment = data.get('comment')
        
        if not content_id or not content_type:
            return jsonify({"error": "شناسه و نوع محتوا الزامی هستند"}), 400
        
        # Record feedback
        continuous_learning.record_feedback(
            content_id=content_id,
            content_type=content_type,
            rating=rating,
            was_helpful=was_helpful,
            user_comment=comment
        )
        
        # Rate content in generator
        content_generator.rate_content(content_id, rating, was_helpful)
        
        return jsonify({"message": "بازخورد شما ثبت شد. متشکریم!"})
        
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/ai/content/popular', methods=['GET'])
def get_popular_content():
    """Get most popular content."""
    try:
        content_type = request.args.get('type')
        limit = int(request.args.get('limit', 10))
        
        # Parse content type
        ct = None
        if content_type:
            from app.services.autonomous_ai import ContentType
            try:
                ct = ContentType(content_type)
            except ValueError:
                pass
        
        contents = content_generator.get_popular_content(content_type=ct, limit=limit)
        
        return jsonify({
            "contents": [
                {
                    "content_id": c.content_id,
                    "title": c.title,
                    "type": c.content_type.value,
                    "view_count": c.view_count,
                    "rating": c.rating
                }
                for c in contents
            ]
        })
        
    except Exception as e:
        logger.error(f"Popular content error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/ai/content/best', methods=['GET'])
def get_best_rated_content():
    """Get highest rated content."""
    try:
        content_type = request.args.get('type')
        limit = int(request.args.get('limit', 10))
        
        ct = None
        if content_type:
            from app.services.autonomous_ai import ContentType
            try:
                ct = ContentType(content_type)
            except ValueError:
                pass
        
        contents = content_generator.get_best_rated_content(content_type=ct, limit=limit)
        
        return jsonify({
            "contents": [
                {
                    "content_id": c.content_id,
                    "title": c.title,
                    "type": c.content_type.value,
                    "rating": c.rating,
                    "body": c.body[:500] + "..." if len(c.body) > 500 else c.body
                }
                for c in contents
            ]
        })
        
    except Exception as e:
        logger.error(f"Best content error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/ai/learning/stats', methods=['GET'])
def get_learning_stats():
    """Get continuous learning statistics."""
    try:
        stats = continuous_learning.get_learning_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Learning stats error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/nlp/analyze', methods=['POST'])
def nlp_analyze():
    """NLP text analysis endpoint."""
    from app.services.autonomous_ai import PersianNLP
    
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "متن الزامی است"}), 400
        
        nlp = PersianNLP()
        
        # Normalize
        normalized = nlp.normalize(text)
        
        # Sentiment
        sentiment = nlp.analyze_sentiment(text)
        
        # Keywords
        keywords = nlp.extract_keywords(text)
        
        # Summary
        summary = nlp.generate_summary(text)
        
        return jsonify({
            "original": text,
            "normalized": normalized,
            "sentiment": sentiment,
            "keywords": keywords,
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"NLP analysis error: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== Training Data API ====================

@main_bp.route('/api/training/build', methods=['POST'])
def build_knowledge_base():
    """Build knowledge base from documents."""
    from app.services.training_data_extractor import TrainingDataExtractor
    
    try:
        data = request.json or {}
        docs_dir = data.get('docs_dir', 'docs')
        
        extractor = TrainingDataExtractor(docs_dir=docs_dir)
        result = extractor.build_knowledge_base()
        
        return jsonify({
            "success": True,
            "result": result,
            "message": f"Built knowledge base with {result.get('total_chunks', 0)} chunks"
        })
        
    except Exception as e:
        logger.error(f"Knowledge base build error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/training/status', methods=['GET'])
def get_extraction_status():
    """Get training data extraction status."""
    from app.services.training_data_extractor import TrainingDataExtractor
    
    try:
        extractor = TrainingDataExtractor()
        status = extractor.get_status()
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Extraction status error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/training/search', methods=['POST'])
def search_knowledge_base():
    """Search knowledge base."""
    from app.services.autonomous_ai import KnowledgeBase
    
    try:
        data = request.json
        query = data.get('query', '')
        top_k = data.get('top_k', 3)
        
        if not query:
            return jsonify({"error": "Query الزامی است"}), 400
        
        kb = KnowledgeBase()
        results = kb.search(query, top_k)
        
        return jsonify({
            "query": query,
            "results": results,
            "count": len(results)
        })
        
    except Exception as e:
        logger.error(f"Knowledge search error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/training/stats', methods=['GET'])
def get_knowledge_stats():
    """Get knowledge base statistics."""
    from app.services.autonomous_ai import KnowledgeBase
    
    try:
        kb = KnowledgeBase()
        stats = kb.get_stats()
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Knowledge stats error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/training/sources', methods=['GET'])
def list_training_sources():
    """List available training data sources."""
    from app.services.training_data_extractor import TrainingDataExtractor
    
    try:
        extractor = TrainingDataExtractor()
        sources = extractor.list_sources()
        
        return jsonify({
            "sources": sources,
            "total": len(sources)
        })
        
    except Exception as e:
        logger.error(f"Sources list error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/training/extract/pdf', methods=['POST'])
def extract_from_pdf():
    """Extract text from a PDF file."""
    from app.services.training_data_extractor import TrainingDataExtractor
    
    try:
        data = request.json
        pdf_path = data.get('pdf_path', '')
        
        if not pdf_path:
            return jsonify({"error": "PDF path الزامی است"}), 400
        
        extractor = TrainingDataExtractor()
        result = extractor.extract_from_pdf(pdf_path)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/training/scrape', methods=['POST'])
def scrape_educational_content():
    """Scrape educational content from websites."""
    from app.services.training_data_extractor import WebScraper
    
    try:
        data = request.json
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({"error": "URLs الزامی است"}), 400
        
        scraper = WebScraper()
        results = []
        
        for url in urls:
            try:
                content = scraper.scrape_article(url)
                results.append({"url": url, "content": content})
            except Exception as url_e:
                results.append({"url": url, "error": str(url_e)})
        
        return jsonify({
            "results": results,
            "success_count": sum(1 for r in results if 'content' in r)
        })
        
    except Exception as e:
        logger.error(f"Web scraping error: {e}")
        return jsonify({"error": str(e)}), 500


@main_bp.route('/api/nlp/format/number', methods=['POST'])
def nlp_format_number():
    """Format number in Persian style."""
    from app.services.autonomous_ai import PersianNLP
    
    try:
        data = request.json
        number = float(data.get('number', 0))
        currency = data.get('currency', True)
        
        nlp = PersianNLP()
        formatted = nlp.format_number(number, currency=currency)
        
        return jsonify({"formatted": formatted})
        
    except Exception as e:
        logger.error(f"Number formatting error: {e}")
        return jsonify({"error": str(e)}), 500
