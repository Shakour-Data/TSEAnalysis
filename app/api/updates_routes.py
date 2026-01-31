"""
API endpoints for monitoring database update progress
"""

from flask import jsonify, Blueprint
from app.services.incremental_updater import get_updater
from pathlib import Path
import json

update_bp = Blueprint('updates', __name__, url_prefix='/api/updates')

@update_bp.route('/status', methods=['GET'])
def get_update_status():
    """دریافت وضعیت آپدیت فعلی."""
    updater = get_updater()
    status = updater.get_status()
    
    # بارگیری پیشرفت تفصیلی
    progress = updater.progress
    
    return jsonify({
        "status": "running" if updater.is_running else "stopped",
        "current_message": status.get("message"),
        "progress": {
            "symbols_updated": progress.get("symbols_updated", 0),
            "symbols_failed": progress.get("symbols_failed", 0),
            "total_symbols": progress.get("total_symbols", 0),
            "completed_count": len(progress.get("completed_symbols", []))
        },
        "last_update": progress.get("last_update"),
        "start_date": progress.get("start_date"),
        "daily_progress": progress.get("daily_progress", {})
    })

@update_bp.route('/progress', methods=['GET'])
def get_detailed_progress():
    """دریافت پیشرفت تفصیلی."""
    updater = get_updater()
    progress = updater.progress
    
    # محاسبه درصد
    total = progress.get("total_symbols", 1)
    updated = progress.get("symbols_updated", 0)
    percentage = (updated / total * 100) if total > 0 else 0
    
    # محاسبه روز‌های باقی
    pending = total - updated
    symbols_per_day = 100
    days_left = (pending + symbols_per_day - 1) // symbols_per_day if pending > 0 else 0
    
    return jsonify({
        "percentage": round(percentage, 1),
        "updated": updated,
        "failed": progress.get("symbols_failed", 0),
        "total": total,
        "pending": pending,
        "days_left": days_left,
        "daily_quota": symbols_per_day,
        "daily_progress": progress.get("daily_progress", {})
    })

@update_bp.route('/failed', methods=['GET'])
def get_failed_symbols():
    """دریافت نمادهایی که آپدیت نشدند."""
    updater = get_updater()
    failed = updater.progress.get("failed_symbols", [])
    
    return jsonify({
        "count": len(failed),
        "symbols": failed
    })

@update_bp.route('/start', methods=['POST'])
def start_update():
    """شروع آپدیت از صفر."""
    updater = get_updater()
    updater.progress["completed_symbols"] = []
    updater.progress["failed_symbols"] = []
    updater.start()
    
    return jsonify({
        "message": "Database update started",
        "daily_quota": updater.symbols_per_day
    })

@update_bp.route('/stop', methods=['POST'])
def stop_update():
    """توقف آپدیت."""
    updater = get_updater()
    updater.stop()
    
    return jsonify({
        "message": "Database update stopped",
        "progress": updater.progress
    })

@update_bp.route('/resume', methods=['POST'])
def resume_update():
    """ادامه آپدیت از جایی که متوقف شده."""
    updater = get_updater()
    updater.start()
    
    return jsonify({
        "message": "Database update resumed",
        "completed": len(updater.progress.get("completed_symbols", [])),
        "pending": updater.progress.get("total_symbols", 0) - len(updater.progress.get("completed_symbols", []))
    })
