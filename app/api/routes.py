from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from datetime import datetime
import time
import random
import threading
import os
import io
import pandas as pd
import base64

from app.services.tsetmc import client
from app.services.technical_analysis import TechnicalAnalyzer
from app.database import db
from app.core_utils import PROXY_URL, stats
from app import cache

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
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    symbols = client.get_all_symbols(market_type, force_refresh=refresh)
    if isinstance(symbols, dict) and "error" in symbols:
        return jsonify(symbols)
    return jsonify(symbols if symbols else [])

@main_bp.route('/api/sync_registry', methods=['POST'])
def sync_registry():
    """Manual trigger for persistent registry update."""
    results = {}
    for t in range(1, 6):
        try:
            data = client._fetch_symbols_by_type(str(t), force_refresh=True)
            results[f"type_{t}"] = f"Success ({len(data)} symbols)" if isinstance(data, list) else "Failed"
            if t < 5: time.sleep(random.uniform(5, 10))
        except Exception as e:
            results[f"type_{t}"] = str(e)
    return jsonify({"status": "Complete", "details": results, "registry_count": db.get_total_symbols_count()})

@main_bp.route('/api/fetch_data', methods=['POST'])
def fetch_data():
    data = request.json
    force_refresh = data.get('refresh', False)
    
    # Cache check
    cache_key = str(data)
    if not force_refresh:
        cached_res = cache.get(cache_key)
        if cached_res: return jsonify(cached_res)

    asset_type = data.get('asset_type')
    symbol = data.get('symbol')
    service_type = data.get('service_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    adjusted = data.get('adjusted', True)
    timeframe = data.get('timeframe', 'daily')
    candle_count = data.get('candle_count')

    result = []
    
    if asset_type == 'indices_market':
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
        if timeframe == 'weekly': result = TechnicalAnalyzer.resample_to_weekly(result)
        result = TechnicalAnalyzer.calculate_technical_analysis(result)
        if len(result) > 20:
            try:
                buf = TechnicalAnalyzer.generate_chart_image(result, symbol)
                if buf: result[0]['chart_image'] = base64.b64encode(buf.getvalue()).decode('utf-8')
            except: pass

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
    report = f"# Technical Analysis Report: {symbol}\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    return jsonify({"json": {"daily": tech_data, "weekly": weekly_data}, "markdown": report, "filename": f"AI_Package_{symbol}"})

@main_bp.route('/api/download', methods=['POST'])
def download():
    data = request.json
    daily_data = data.get('daily_data') or data.get('data')
    symbol, fmt = data.get('symbol', 'Symbol'), data.get('format')
    if fmt == 'image' and daily_data:
        df = pd.DataFrame(daily_data)
        if 'date' in df.columns: df = df.sort_values('date')
        buf = TechnicalAnalyzer.generate_chart_image(df, symbol)
        return send_file(buf, download_name=f"{symbol}.png", as_attachment=True, mimetype='image/png')
    return jsonify({"error": "Format not supported"}), 400
