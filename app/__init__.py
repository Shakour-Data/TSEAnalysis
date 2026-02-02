from flask import Flask, jsonify, request
from flask_caching import Cache
import os
import threading
import time
import random
import logging
import traceback
import sys

# CORS - safe import
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS = None
    CORS_AVAILABLE = False

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

from app.database import db

cache = Cache()

def create_app():
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')
    
    # Configure CORS - Allow cross-origin requests from all sources with credentials
    # In production, restrict to specific domains
    if CORS_AVAILABLE:
        CORS(app, 
             resources={
                 r"/api/*": {
                     "origins": ["*"],  # آپ یہ خاص domains سے بدل سکتے ہیں
                     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                     "allow_headers": ["Content-Type", "Authorization"],
                     "expose_headers": ["Content-Type", "X-Total-Count"],
                     "supports_credentials": True,
                     "max_age": 3600
                 }
             },
             supports_credentials=True
        )
        logger.info("✅ CORS configured")
    else:
        logger.warning("⚠️ Flask-CORS not available")
    
    # Configure Caching
    app.config['CACHE_TYPE'] = 'FileSystemCache'
    app.config['CACHE_DIR'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
    cache.init_app(app)
    
    # HTTPS Enforcement Middleware (production میں)
    # Environment variable 'ENVIRONMENT' = 'production' ہو تو HTTPS enforce کریں
    if os.getenv('ENVIRONMENT') == 'production' or os.getenv('ENFORCE_HTTPS') == 'true':
        @app.before_request
        def enforce_https():
            """HTTP سے HTTPS میں redirect کریں"""
            # X-Forwarded-Proto ہیڈر چیک کریں (reverse proxy کے لیے)
            if request.headers.get('X-Forwarded-Proto') == 'http':
                logger.warning(f"HTTP request blocked: {request.url}")
                return jsonify({
                    "error": "HTTPS required",
                    "message": "براہ کرم HTTPS استعمال کریں"
                }), 403
            
            # براہ راست HTTP چیک کریں
            if not request.is_secure and not os.getenv('DEBUG'):
                logger.warning(f"Non-secure request blocked: {request.url}")
                return jsonify({
                    "error": "HTTPS required",
                    "message": "براہ کرم محفوظ کنکشن استعمال کریں"
                }), 403
        
        logger.info("🔒 HTTPS enforcement فعال ہے (Production mode)")
    else:
        logger.info("⚠️ HTTPS enforcement غیر فعال (Development mode)")
    
    # Security Headers شامل کریں
    @app.after_request
    def add_security_headers(response):
        """تمام جوابات میں security headers شامل کریں"""
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response
    
    # Register Blueprints
    from app.api.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Optional: Register update_bp if it exists
    try:
        from app.api.routes import update_bp
        app.register_blueprint(update_bp)
    except ImportError:
        try:
            from app.api.updates_routes import update_bp
            app.register_blueprint(update_bp)
        except ImportError:
            logger.debug("update_bp not found - skipping")
    
    # Global Exception Handlers
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 Not Found: {error}")
        return jsonify({"error": "صفحہ نہیں ملا"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Internal Error: {error}\n{traceback.format_exc()}")
        return jsonify({
            "error": "سرور میں خرابی - براہ مہربانی دوبارہ کوشش کریں",
            "details": str(error)[:100]
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        from werkzeug.exceptions import HTTPException
        if isinstance(error, HTTPException):
            return jsonify({
                "error": error.name,
                "message": error.description
            }), error.code
        
        logger.error(f"Unhandled Exception: {error}", exc_info=True)
        return jsonify({
            "error": "غیر متوقع خرابی",
            "details": str(error)[:100]
        }), 500
    
    # Preload logic - Run once in a thread
    def start_preload():
        if app.testing: return # Don't preload in tests
        from app.services.tsetmc import client
        from app.services.data_refresh import start_background_service
        from app.services.incremental_updater import start_updater
        
        def background_preload():
            # Wait a few seconds for app to fully start
            time.sleep(5)
            
            # Start continuous data refresh service
            try:
                start_background_service()
                logger.info("✅ Background data refresh service started")
            except Exception as e:
                logger.warning(f"Could not start data refresh service: {e}")
            
            # Start incremental database updater
            try:
                symbols_per_day = 100  # آپدیت 100 نماد در روز
                updater = start_updater(symbols_per_day=symbols_per_day)
                logger.info(f"✅ Incremental database updater started ({symbols_per_day} symbols/day)")
            except Exception as e:
                logger.warning(f"Could not start database updater: {e}")
            
            if db.get_total_symbols_count() < 100:
                logger.info("🚀 STARTUP: Registry empty. Initiating background pre-warm...")
                for t in ["1", "2"]:
                    try:
                        logger.debug(f"Preloading symbol type {t}...")
                        client.get_all_symbols(t)
                        time.sleep(random.uniform(15, 25))
                    except Exception as e:
                        logger.error(f"Failed to preload type {t}: {str(e)}")
        
        thread = threading.Thread(target=background_preload, daemon=True)
        thread.name = "BackgroundPreloadThread"
        thread.start()

    # In newer Flask, we just call it once here instead of using hook
    # unless we need the request context.
    start_preload()

    return app
