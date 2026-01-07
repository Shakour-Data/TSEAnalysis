from flask import Flask
from flask_caching import Cache
import os
import threading
import time
import random

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
                print("🚀 STARTUP: Registry empty. Initiating background pre-warm...")
                for t in ["1", "2"]:
                    try:
                        client.get_all_symbols(t)
                        time.sleep(random.uniform(15, 25))
                    except: pass
        
        threading.Thread(target=background_preload, daemon=True).start()

    # In newer Flask, we just call it once here instead of using hook
    # unless we need the request context.
    start_preload()

    return app
