"""
Data Refresh Service - Automatic real data fetching and caching

This service:
1. Attempts to fetch fresh data from TSETMC API
2. Falls back to cached data if API fails
3. Never uses mock data
4. Retrains AI model when new data is available
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time
import logging
from datetime import datetime
from app.services.tsetmc import client
from app.database import db
from app.services.local_ai_assistant import ai_assistant

logger = logging.getLogger(__name__)

class DataRefreshService:
    """Service to keep market data fresh and retrain AI periodically."""
    
    def __init__(self):
        self.is_running = False
        self.last_refresh = None
        self.refresh_interval = 3600  # 1 hour
        self.thread = None
    
    def start(self):
        """Start background data refresh service."""
        if self.is_running:
            logger.warning("Data refresh service already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self.thread.start()
        logger.info("✅ Data refresh service started (runs every hour)")
    
    def stop(self):
        """Stop background service."""
        self.is_running = False
        logger.info("Data refresh service stopped")
    
    def _refresh_loop(self):
        """Background loop for data refresh."""
        while self.is_running:
            try:
                # Check if refresh is needed
                if self.last_refresh is None or \
                   (datetime.now() - self.last_refresh).total_seconds() > self.refresh_interval:
                    logger.info("Starting scheduled data refresh...")
                    self.refresh_market_data()
                    self.last_refresh = datetime.now()
                
                # Sleep before next check
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in data refresh loop: {e}")
                time.sleep(300)
    
    def refresh_market_data(self, sample_size=50):
        """
        Refresh market data for active symbols.
        
        Args:
            sample_size: Number of symbols to refresh per cycle
        """
        try:
            symbols = db.get_all_symbols()
            total_symbols = len(symbols)
            
            logger.info(f"Refreshing data for up to {sample_size} symbols...")
            
            refreshed_count = 0
            for i, sym_data in enumerate(symbols[:sample_size]):
                if not self.is_running:
                    break
                
                symbol = sym_data.get('l18', '')
                if not symbol:
                    continue
                
                try:
                    # Attempt to fetch fresh data
                    price_history = client.get_price_history(symbol, force_refresh=True)
                    
                    if price_history and len(price_history) > 0:
                        logger.debug(f"  ✅ Updated {symbol}: {len(price_history)} records")
                        refreshed_count += 1
                    
                except Exception as e:
                    logger.debug(f"  ⚠️  Could not refresh {symbol}: {str(e)[:50]}")
                    # Fall through to cached data
                
                # Rate limiting - be nice to the API
                time.sleep(0.5)
            
            logger.info(f"Data refresh complete: {refreshed_count} symbols updated")
            
            # Check if we should retrain the model
            self._maybe_retrain_model()
            
        except Exception as e:
            logger.error(f"Error during data refresh: {e}")
    
    def _maybe_retrain_model(self):
        """Retrain AI model if significant new data is available."""
        try:
            # Simple heuristic: retrain if last model update was > 24 hours ago
            if ai_assistant.last_update and \
               (datetime.now() - ai_assistant.last_update).total_seconds() > 86400:
                logger.info("Retraining AI model with fresh data...")
                ai_assistant.update_model()
                logger.info("✅ AI model retrained")
        except Exception as e:
            logger.error(f"Error during model retraining: {e}")

# Global instance
_service = None

def get_service():
    """Get or create the data refresh service."""
    global _service
    if _service is None:
        _service = DataRefreshService()
    return _service

def start_background_service():
    """Start the background data refresh service."""
    service = get_service()
    service.start()

if __name__ == "__main__":
    # Test the service
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    service = DataRefreshService()
    service.start()
    
    # Run for 10 seconds as demo
    print("Running data refresh service for demo...")
    time.sleep(10)
    service.stop()
    print("Service stopped")
