# Optimization Endpoints
# ═════════════════════════════════════════════════════════════════

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_optimizer_blueprint():
    """Create blueprint for optimization endpoints"""
    optimizer_bp = Blueprint('optimizer', __name__, url_prefix='/api/optimizer')
    
    from app.services.feature_optimizer import (
        realtime_optimizer, ai_optimizer, db_optimizer, 
        ta_optimizer, api_optimizer, update_optimizer, fallback_optimizer
    )
    
    # ═════════════════════════════════════════════════════════════════
    # Feature 1: Real-time Data Optimization
    # ═════════════════════════════════════════════════════════════════
    
    @optimizer_bp.route('/realtime/batch-fetch', methods=['POST'])
    def batch_fetch_optimization():
        """Optimize batch fetching of symbols"""
        try:
            data = request.json
            symbols = data.get('symbols', [])
            
            if not symbols or not isinstance(symbols, list):
                return jsonify({"error": "symbols list required"}), 400
            
            # Use the optimizer's batch fetch with delays
            results, failed = realtime_optimizer.batch_fetch_with_delays(
                symbols=symbols,
                fetch_func=lambda s: {'symbol': s, 'status': 'success'},  # Placeholder
                min_delay=1.0
            )
            
            return jsonify({
                "success_count": len(results),
                "failed_count": len(failed),
                "failed_symbols": failed,
                "results": results
            })
        except Exception as e:
            logger.error(f"Batch fetch error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @optimizer_bp.route('/realtime/cache-stats', methods=['GET'])
    def cache_statistics():
        """Get cache statistics"""
        try:
            cache_keys = len(realtime_optimizer._cache)
            cache_size_kb = sum(
                len(str(v).encode()) / 1024 
                for v in realtime_optimizer._cache.values()
            )
            
            return jsonify({
                "cached_keys": cache_keys,
                "cache_size_kb": cache_size_kb,
                "ttl_seconds": realtime_optimizer.max_cache_age,
                "batch_size": realtime_optimizer.batch_size
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # ═════════════════════════════════════════════════════════════════
    # Feature 2: AI Prediction Optimization
    # ═════════════════════════════════════════════════════════════════
    
    @optimizer_bp.route('/ai/prediction-confidence', methods=['POST'])
    def calculate_confidence():
        """Calculate confidence score for predictions"""
        try:
            data = request.json
            predictions = data.get('predictions', [])
            actual = data.get('actual')
            
            confidence = ai_optimizer.calculate_prediction_confidence(predictions, actual)
            
            return jsonify({
                "confidence": confidence,
                "confidence_percent": round(confidence * 100, 2),
                "level": "عالی" if confidence > 0.8 else "خوب" if confidence > 0.6 else "متوسط" if confidence > 0.4 else "پایین"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @optimizer_bp.route('/ai/feature-selection', methods=['POST'])
    def feature_selection():
        """Optimize feature selection for AI model"""
        try:
            import pandas as pd
            import numpy as np
            
            data = request.json
            features_data = data.get('features', [])
            target = data.get('target', [])
            max_features = data.get('max_features', 20)
            
            if not features_data or not target:
                return jsonify({"error": "features and target required"}), 400
            
            df = pd.DataFrame(features_data)
            target_array = np.array(target)
            
            selected = ai_optimizer.select_best_features(df, target_array, max_features)
            
            return jsonify({
                "selected_features": [f[0] for f in selected],
                "feature_scores": [f[1] for f in selected],
                "total_features_selected": len(selected)
            })
        except Exception as e:
            logger.error(f"Feature selection error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @optimizer_bp.route('/ai/should-retrain', methods=['POST'])
    def should_retrain():
        """Determine if model should be retrained"""
        try:
            from datetime import datetime
            
            data = request.json
            last_trained = datetime.fromisoformat(data.get('last_trained', datetime.now().isoformat()))
            accuracy = float(data.get('accuracy', 0.7))
            data_size = int(data.get('data_size', 100))
            
            needs_retrain = ai_optimizer.should_retrain_model(last_trained, accuracy, data_size)
            
            return jsonify({
                "should_retrain": needs_retrain,
                "reason": "قدیمی‌تر از 30 روز" if (datetime.now() - last_trained).days > 30 else 
                         "دقت کم" if accuracy < 0.60 else "نیاز نیست"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # ═════════════════════════════════════════════════════════════════
    # Feature 3: Database Optimization
    # ═════════════════════════════════════════════════════════════════
    
    @optimizer_bp.route('/database/optimize', methods=['POST'])
    def optimize_database():
        """Get database optimization commands"""
        try:
            optimizations = db_optimizer.optimize_table_structure()
            
            return jsonify({
                "optimizations": optimizations,
                "description": "این دستورات برای بهینه‌سازی بانک اطلاعات اجرا شوند"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @optimizer_bp.route('/database/size-estimate', methods=['POST'])
    def estimate_size():
        """Estimate database size"""
        try:
            data = request.json
            record_count = int(data.get('record_count', 100000))
            
            size_info = db_optimizer.estimate_database_size(record_count)
            
            return jsonify(size_info)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # ═════════════════════════════════════════════════════════════════
    # Feature 4: Technical Analysis Optimization
    # ═════════════════════════════════════════════════════════════════
    
    @optimizer_bp.route('/technical/detect-patterns', methods=['POST'])
    def detect_patterns():
        """Detect candlestick patterns"""
        try:
            import pandas as pd
            
            data = request.json
            ohlcv_data = data.get('data', [])
            
            if not ohlcv_data:
                return jsonify({"error": "OHLCV data required"}), 400
            
            df = pd.DataFrame(ohlcv_data)
            
            patterns = ta_optimizer.detect_candlestick_patterns(df)
            
            return jsonify({
                "patterns_found": patterns,
                "total_patterns": sum(len(v) for v in patterns.values()),
                "pattern_types": list(patterns.keys())
            })
        except Exception as e:
            logger.error(f"Pattern detection error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @optimizer_bp.route('/technical/trading-signals', methods=['POST'])
    def get_signals():
        """Generate trading signals"""
        try:
            import pandas as pd
            
            data = request.json
            ohlcv_data = data.get('data', [])
            
            if not ohlcv_data:
                return jsonify({"error": "OHLCV data required"}), 400
            
            df = pd.DataFrame(ohlcv_data)
            
            signals = ta_optimizer.generate_trading_signals(df)
            
            return jsonify({
                "signals": signals,
                "signal_count": len(signals),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return jsonify({"error": str(e)}), 500
    
    # ═════════════════════════════════════════════════════════════════
    # Feature 5: REST API Optimization
    # ═════════════════════════════════════════════════════════════════
    
    @optimizer_bp.route('/api/paginate', methods=['POST'])
    def paginate_response():
        """Generate paginated response"""
        try:
            data = request.json
            items = data.get('items', [])
            page = int(data.get('page', 1))
            per_page = int(data.get('per_page', 50))
            
            response = api_optimizer.generate_paginated_response(items, page, per_page)
            
            return jsonify(response)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @optimizer_bp.route('/api/response-size', methods=['POST'])
    def calculate_response_size():
        """Calculate response size and compression"""
        try:
            data = request.json
            response_data = data.get('data', {})
            
            size_info = api_optimizer.calculate_response_size(response_data)
            
            return jsonify(size_info)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # ═════════════════════════════════════════════════════════════════
    # Feature 6: Update System Optimization
    # ═════════════════════════════════════════════════════════════════
    
    @optimizer_bp.route('/update/schedule', methods=['POST'])
    def calculate_schedule():
        """Calculate optimal update schedule"""
        try:
            data = request.json
            total_symbols = int(data.get('total_symbols', 2000))
            updates_per_day = int(data.get('updates_per_day', 100))
            
            schedule = update_optimizer.calculate_update_schedule(total_symbols, updates_per_day)
            
            return jsonify(schedule)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @optimizer_bp.route('/update/batch-plan', methods=['POST'])
    def plan_batches():
        """Plan update batches"""
        try:
            data = request.json
            symbols = data.get('symbols', [])
            batch_size = int(data.get('batch_size', 50))
            
            batches = update_optimizer.generate_update_batches(symbols, batch_size)
            
            return jsonify({
                "total_batches": len(batches),
                "batch_size": batch_size,
                "total_symbols": len(symbols),
                "batch_schedule": [
                    {"batch_number": i+1, "symbols_count": len(b)} 
                    for i, b in enumerate(batches)
                ]
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # ═════════════════════════════════════════════════════════════════
    # Feature 7: Fallback System Optimization
    # ═════════════════════════════════════════════════════════════════
    
    @optimizer_bp.route('/fallback/generate-synthetic', methods=['POST'])
    def generate_synthetic():
        """Generate synthetic OHLCV data"""
        try:
            data = request.json
            symbol = data.get('symbol', 'UNKNOWN')
            days = int(data.get('days', 100))
            
            synthetic = fallback_optimizer.generate_synthetic_ohlcv(symbol, days)
            
            return jsonify({
                "symbol": symbol,
                "generated_candles": len(synthetic),
                "data": synthetic
            })
        except Exception as e:
            logger.error(f"Synthetic data generation error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @optimizer_bp.route('/fallback/monitor', methods=['POST'])
    def monitor_fallback():
        """Monitor fallback system usage"""
        try:
            data = request.json
            fallback_stats = data.get('stats', {})
            
            analysis = fallback_optimizer.monitor_fallback_usage(fallback_stats)
            
            return jsonify({
                "usage_analysis": analysis,
                "total_uses": sum(fallback_stats.values())
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # ═════════════════════════════════════════════════════════════════
    # General Optimization Status
    # ═════════════════════════════════════════════════════════════════
    
    @optimizer_bp.route('/status', methods=['GET'])
    def optimizer_status():
        """Get overall optimizer status"""
        try:
            return jsonify({
                "status": "فعال",
                "modules": {
                    "realtime": "آمادگی برای بهینه‌سازی داده‌های زنده",
                    "ai": "آمادگی برای بهینه‌سازی AI و پیش‌بینی",
                    "database": "آمادگی برای بهینه‌سازی بانک اطلاعات",
                    "technical": "آمادگی برای بهینه‌سازی تحلیل تکنیکال",
                    "api": "آمادگی برای بهینه‌سازی REST API",
                    "update": "آمادگی برای بهینه‌سازی سیستم بروزرسانی",
                    "fallback": "آمادگی برای بهینه‌سازی سیستم Fallback"
                },
                "version": "4.0"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return optimizer_bp


# Register optimizer blueprint with Flask app
def register_optimizer_routes(app):
    """Register optimizer blueprint with the Flask app"""
    optimizer_bp = create_optimizer_blueprint()
    app.register_blueprint(optimizer_bp)
    logger.info("✅ Optimizer blueprint registered")
