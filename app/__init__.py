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

from app.core_utils import stats
from app.database import db

cache = Cache()

def create_app():
    app = Flask(__name__, 
                template_folder='../templates', 
                static_folder='../static')
    
    # Configure Caching
    app.config['CACHE_TYPE'] = 'simple'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    cache.init_app(app)
    
    # Register Blueprints
    from app.api.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Preload logic - Run once in a thread
    def start_preload():
        from app.services.tsetmc import client
        def background_preload():
            # Wait a few seconds for app to fully start
            time.sleep(5)
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
