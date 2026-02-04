"""
Chart rendering optimization - بہتری اور caching
"""
import logging
import io
import base64
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ChartOptimizer:
    """Chart rendering کو optimize کریں"""
    
    # In-memory cache برائے charts
    _chart_cache = {}
    _cache_ttl = 300  # 5 منٹ
    
    @staticmethod
    def get_chart_cache_key(symbol, chart_type, period, resolution):
        """Chart کے لیے cache key بنائیں"""
        key_str = f"{symbol}:{chart_type}:{period}:{resolution}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @staticmethod
    def get_cached_chart(cache_key):
        """Cached chart حاصل کریں"""
        if cache_key in ChartOptimizer._chart_cache:
            chart_data, timestamp = ChartOptimizer._chart_cache[cache_key]
            age = datetime.now().timestamp() - timestamp
            
            if age < ChartOptimizer._cache_ttl:
                logger.debug(f"✅ Chart cache hit: {cache_key[:8]} (age: {age:.1f}s)")
                return chart_data
            else:
                # Cache expired
                del ChartOptimizer._chart_cache[cache_key]
        
        return None
    
    @staticmethod
    def cache_chart(cache_key, chart_data):
        """Chart کو cache میں ڈالیں"""
        ChartOptimizer._chart_cache[cache_key] = (chart_data, datetime.now().timestamp())
        logger.debug(f"📊 Chart cached: {cache_key[:8]}")
    
    @staticmethod
    def clear_chart_cache(symbol=None):
        """Chart cache صاف کریں"""
        if symbol is None:
            ChartOptimizer._chart_cache.clear()
            logger.info("✅ تمام charts صاف کیے گئے")
        else:
            # صرف خاص symbol کے charts صاف کریں
            keys_to_delete = [k for k in ChartOptimizer._chart_cache.keys() if symbol in k]
            for k in keys_to_delete:
                del ChartOptimizer._chart_cache[k]
            logger.info(f"✅ {len(keys_to_delete)} charts صاف کیے گئے ({symbol})")
    
    @staticmethod
    def optimize_image_size(image_buffer, max_size_kb=500):
        """
        Image کو optimize کریں - سائز کم کریں
        """
        try:
            from PIL import Image
            
            # Image لوڈ کریں
            img = Image.open(image_buffer)
            
            # Original سائز
            original_size = len(image_buffer.getvalue()) / 1024
            
            # Quality کم کریں اگر بہت بڑا ہو
            quality = 95
            while quality > 30:
                buffer = io.BytesIO()
                
                # Resize if needed
                if max(img.size) > 2000:
                    ratio = 2000 / max(img.size)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                else:
                    img_resized = img
                
                img_resized.save(buffer, format='PNG', quality=quality, optimize=True)
                
                new_size = len(buffer.getvalue()) / 1024
                
                if new_size <= max_size_kb or quality <= 40:
                    logger.info(f"📊 Image optimized: {original_size:.1f}KB → {new_size:.1f}KB (Quality: {quality})")
                    buffer.seek(0)
                    return buffer
                
                quality -= 5
            
            # اگر ابھی بھی بڑا ہے تو resample کریں
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', quality=30, optimize=True)
            logger.warning(f"📊 Image forcefully compressed to {len(buffer.getvalue()) / 1024:.1f}KB")
            buffer.seek(0)
            return buffer
        
        except Exception as e:
            logger.warning(f"Image optimization ناکام: {e}")
            return image_buffer
    
    @staticmethod
    def encode_chart_to_base64(image_buffer):
        """Chart کو base64 میں encode کریں"""
        try:
            image_buffer.seek(0)
            image_data = base64.b64encode(image_buffer.read()).decode('utf-8')
            return f"data:image/png;base64,{image_data}"
        except Exception as e:
            logger.error(f"Base64 encoding ناکام: {e}")
            return None
    
    @staticmethod
    def get_chart_stats():
        """Chart cache کی معلومات"""
        total_charts = len(ChartOptimizer._chart_cache)
        total_size = 0
        for chart_data, _ in ChartOptimizer._chart_cache.values():
            if isinstance(chart_data, str) and ',' in chart_data:
                try:
                    total_size += len(base64.b64decode(chart_data.split(',')[1]))
                except:
                    total_size += len(chart_data)
            else:
                total_size += len(chart_data)
        
        total_size_mb = total_size / 1024 / 1024  # MB میں
        
        return {
            'cached_charts': total_charts,
            'total_size_mb': total_size_mb,
            'cache_ttl': ChartOptimizer._cache_ttl,
            'estimated_memory': f"{total_size_mb:.2f} MB"
        }
    
    @staticmethod
    def cleanup_expired_charts():
        """Expired charts کو صاف کریں"""
        now = datetime.now().timestamp()
        expired_keys = []
        
        for key, (chart_data, timestamp) in ChartOptimizer._chart_cache.items():
            age = now - timestamp
            if age > ChartOptimizer._cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del ChartOptimizer._chart_cache[key]
        
        if expired_keys:
            logger.info(f"✅ {len(expired_keys)} expired charts صاف کیے گئے")
        
        return len(expired_keys)
    
    @staticmethod
    def set_chart_cache_ttl(seconds):
        """Chart cache TTL سیٹ کریں"""
        ChartOptimizer._cache_ttl = seconds
        logger.info(f"📊 Chart cache TTL set to {seconds}s")
    
    @staticmethod
    def estimate_data_points(period, resolution):
        """
        Data points کو estimate کریں
        چھوٹے resolutions پر زیادہ data points
        """
        resolution_map = {
            '1d': 1,      # 1 day = 1 point
            '1w': 7,      # 1 week = 1 point per day
            '1M': 30,     # 1 month = 1 point per day
        }
        
        days_map = {
            '1M': 30,
            '3M': 90,
            '6M': 180,
            '1Y': 365,
            '5Y': 1825,
        }
        
        period_days = days_map.get(period, 30)
        points_per_day = resolution_map.get(resolution, 1)
        
        return period_days * points_per_day
    
    # get_chart_cache_key is already defined at line 19-23

