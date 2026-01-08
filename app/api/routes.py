from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from datetime import datetime
import time
import random
import threading
import os
import io
import pandas as pd
import base64
import zipfile
import logging
import json
import hashlib

from app.services.tsetmc import client
from app.services.tgju import tgju_client
from app.services.technical_analysis import TechnicalAnalyzer
from app.database import db
from app.core_utils import PROXY_URL, stats
from app import cache

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/api_test')
def api_test():
    return render_template('api_test.html')

@main_bp.route('/api/market_status')
def get_market_status():
    """Returns the current status of the market."""
    return jsonify({
        "status": "در حال فعالیت",
        "time": datetime.now().strftime("%H:%M:%S"),
        "stats": {
            "global": stats["global"],
            "services": stats["services"]
        }
    })

@main_bp.route('/api/health')
def health_check():
    """Diagnostic endpoint to check connectivity status."""
    test_res = client._make_request("Api/Tsetmc/Index.php", {"type": "1"})
    status = "OK" if "error" not in test_res else "FAILED"
    return jsonify({
        "status": status,
        "proxy": PROXY_URL,
        "active_client": client.client_name,
        "test_response": str(test_res)[:200]
    })

@main_bp.route('/api/symbols/<market_type>')
def get_symbols(market_type):
    if market_type == 'tgju':
        return jsonify(tgju_client.get_all_symbols())
        
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    symbols = client.get_all_symbols(market_type, force_refresh=refresh)
    if isinstance(symbols, dict) and "error" in symbols:
        return jsonify(symbols)
    return jsonify(symbols if symbols else [])

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
def fetch_data():
    data = request.json
    force_refresh = data.get('refresh', False)
    
    # Stable Cache key using MD5 hash of sorted JSON
    data_str = json.dumps(data, sort_keys=True)
    cache_key = hashlib.md5(data_str.encode()).hexdigest()
    
    if not force_refresh:
        cached_res = cache.get(cache_key)
        if cached_res: 
            logger.debug(f"Cache hit for {data.get('symbol')}")
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
    else:
        if service_type == 'realtime':
            result = client.get_realtime_data(symbol)
        elif service_type == 'history':
            result = client.get_history(symbol, adjusted=adjusted, count=candle_count)

    if isinstance(result, list) and not ("error" in str(result)[:50]):
        cache.set(cache_key, result)
        
    return jsonify(result)
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
    elif service_type == 'realtime':
        res = client.get_symbol_info(symbol)
        if res: result = [res]
    elif service_type in ['history', 'technical']:
        result = client.get_price_history(symbol, adjusted=adjusted, force_refresh=force_refresh)

    # Handle error response (but don't error if it's mock data)
    if isinstance(result, dict) and "error" in result and not force_refresh:
        # If real API failed, try mock fallback once
        print(f"DEBUG: Primary fetch failed for {symbol}, attempting mock fallback...")
        result = client._generate_mock_history(symbol)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result)

    if service_type == 'technical' and isinstance(result, list) and len(result) > 0:
        result = TechnicalAnalyzer.prepare_ohlcv_data(result)
        
        # Apply Date Range Filtering
        if (start_date or end_date) and result:
            try:
                # If weekly, expand the range 5x backwards as per user requirement
                final_start = start_date
                if timeframe == 'weekly' and start_date and end_date:
                    s_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    e_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    diff = e_dt - s_dt
                    expanded_start = e_dt - (diff * 5)
                    final_start = expanded_start.strftime('%Y-%m-%d')
                
                filtered = []
                for item in result:
                    item_date = item.get('date', '')[:10]
                    if final_start and item_date < final_start: continue
                    if end_date and item_date > end_date: continue
                    filtered.append(item)
                result = filtered
            except Exception as e:
                print(f"Date Filter Error: {e}")

        if timeframe == 'weekly': 
            result = TechnicalAnalyzer.resample_to_weekly(result)
            
        result = TechnicalAnalyzer.calculate_technical_analysis(result)
        
        if len(result) > 5: # Reduced minimum for better visibility
            try:
                buf = TechnicalAnalyzer.generate_chart_image(result, symbol, timeframe=timeframe)
                if buf: result[0]['chart_image'] = base64.b64encode(buf.getvalue()).decode('utf-8')
            except Exception as e:
                print(f"Chart Generation Error: {e}")

    if result and isinstance(result, list) and candle_count:
        try: result = result[:int(candle_count)]
        except: pass

    cache.set(cache_key, result if result else [], timeout=600)
    return jsonify(result if result else [])

@main_bp.route('/api/ai_package', methods=['POST'])
def generate_ai_package():
    data = request.json
    symbol = data.get('symbol', 'Unknown')
    tech_data = data.get('data', [])
    weekly_data = data.get('weekly_data', [])
    if not tech_data: return jsonify({"error": "داده‌ای یافت نشد."})
    latest = tech_data[0]
    
    # Generate Strategy Matrix
    supports = latest.get('supports', [])
    resistances = latest.get('resistances', [])
    current_price = latest.get('close', 0)
    
    strategies = []
    strategy_table = ""
    try:
        strategies = TechnicalAnalyzer.generate_strategy_matrix(current_price, supports, resistances)
        strategy_table = "\n### 📊 ماتریس استراتژی معاملاتی (۴ بعدی)\n"
        strategy_table += "| ابعاد (شخصیت-ریسک-بازده-افق) | شیوه معاملاتی | نقطه ورود و تریگر | حد سود | حد ضرر | توضیحات فنی |\n"
        strategy_table += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
        for s in strategies:
            strategy_table += f"| {s['dimension']} | {s['style']} | {s['entry']} | {s['target']} | {s['stop_loss']} | {s['trigger']} |\n"
    except Exception as e:
        print(f"Strategy Matrix Error: {e}")

    report = f"# گزارش تحلیل تکنیکال هوشمند: {symbol}\n"
    report += f"**تاریخ گزارش:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    report += f"### 🔍 وضعیت فعلی\n- **قیمت آخرین معامله:** {int(current_price):,}\n"
    report += f"- **سیگنال اندیکاتورها:** {latest.get('Signal', 'Neutral')}\n"
    report += f"- **الگوی شمعی:** {latest.get('Pattern', 'None')}\n\n"
    
    report += strategy_table
    
    return jsonify({
        "json": {
            "daily": tech_data, 
            "weekly": weekly_data,
            "strategies": strategies
        }, 
        "markdown": report, 
        "filename": f"AI_Package_{symbol}"
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
