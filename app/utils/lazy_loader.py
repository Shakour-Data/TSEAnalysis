"""
Lazy Loading Module for Heavy ML Libraries
Reduces startup time by deferring imports until needed
"""

import logging
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)


class LazyLoader:
    """
    Thread-safe lazy loader for heavy imports.
    Delays import until first access, then caches the result.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._cache = {}
        self._initialized = True
    
    def register(self, name: str, import_path: str, attr: str | None = None):
        """
        Register a module to be lazily loaded.
        
        Args:
            name: Internal name for the loader
            import_path: Full import path (e.g., 'sklearn.ensemble.RandomForestClassifier')
            attr: Specific attribute to load (optional)
        """
        self._cache[name] = {
            'import_path': import_path,
            'attr': attr,
            'loaded': False,
            'instance': None
        }
        logger.debug(f"LazyLoader: Registered '{name}' -> {import_path}")
    
    def get(self, name: str) -> Any:
        """
        Get a lazily loaded module/attribute.
        Loads the module on first access.
        """
        if name not in self._cache:
            raise ValueError(f"LazyLoader: '{name}' is not registered")
        
        entry = self._cache[name]
        if not entry['loaded']:
            self._load(name)
        
        return entry['instance']
    
    def _load(self, name: str):
        """Load a registered module"""
        entry = self._cache[name]
        import_path = entry['import_path']
        attr = entry['attr']
        
        logger.info(f"LazyLoader: Loading '{name}' ({import_path})...")
        start_time = __import__('time').time()
        
        try:
            # Dynamic import
            module_parts = import_path.rsplit('.', 1)
            if len(module_parts) == 2:
                module_name, class_name = module_parts
                module = __import__(module_name, fromlist=[class_name])
                obj = getattr(module, class_name)
            else:
                # Simple module import
                obj = __import__(import_path)
            
            entry['instance'] = obj if attr is None else getattr(obj, attr, obj)
            entry['loaded'] = True
            
            elapsed = __import__('time').time() - start_time
            logger.info(f"LazyLoader: '{name}' loaded successfully in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"LazyLoader: Failed to load '{name}': {e}")
            raise
    
    def is_loaded(self, name: str) -> bool:
        """Check if a module has been loaded"""
        return name in self._cache and self._cache[name]['loaded']
    
    def preload(self, name: str):
        """Force load a module immediately"""
        if not self.is_loaded(name):
            self._load(name)


# Global lazy loader instance
lazy = LazyLoader()

# Register heavy ML modules (loaded on first access)
lazy.register('random_forest', 'sklearn.ensemble.RandomForestClassifier')
lazy.register('joblib', 'joblib')
lazy.register('pandas', 'pandas')
lazy.register('numpy', 'numpy')
lazy.register('technical_analysis', 'app.services.technical_analysis', 'TechnicalAnalyzer')


# Convenience getters for commonly used modules
def get_random_forest(*args, **kwargs):
    """Get RandomForestClassifier with optional initialization"""
    RF = lazy.get('random_forest')
    return RF(*args, **kwargs)


def get_joblib():
    """Get joblib module"""
    return lazy.get('joblib')


def get_pandas():
    """Get pandas module"""
    return lazy.get('pandas')


def get_numpy():
    """Get numpy module"""
    return lazy.get('numpy')


def get_technical_analyzer():
    """Get TechnicalAnalyzer class"""
    return lazy.get('technical_analysis')


# Preload function for critical modules
def preload_critical_modules():
    """Preload modules that are needed at startup"""
    critical = ['pandas', 'numpy']
    for name in critical:
        try:
            if not lazy.is_loaded(name):
                lazy.preload(name)
        except Exception as e:
            logger.warning(f"Failed to preload '{name}': {e}")
