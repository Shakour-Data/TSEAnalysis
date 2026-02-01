from flask import Flask
from flask_caching import Cache
import os
import threading
import time
import random
import logging

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
    
    # Configure Caching
    app.config['CACHE_TYPE'] = 'FileSystemCache'
    app.config['CACHE_DIR'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
    cache.init_app(app)
    
    # Register Blueprints
    from app.api.routes import main_bp, update_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(update_bp)
    
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
