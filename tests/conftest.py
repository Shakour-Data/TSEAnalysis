import pytest
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.database import SymbolDatabase

# Mock matplotlib to avoid display issues in tests
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
plt.ioff()  # Turn off interactive mode

# Register custom marks
def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "performance: mark test as performance test")

# Suppress deprecation warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="flask_caching")

@pytest.fixture(scope='function')
def mock_price_history():
    """Mock price history data برای تست‌ها"""
    return [
        {'c': 100, 'o': 99, 'h': 101, 'l': 98, 'd': '2026-01-31'},
        {'c': 101, 'o': 100, 'h': 102, 'l': 99, 'd': '2026-01-30'},
        {'c': 99, 'o': 101, 'h': 102, 'l': 98, 'd': '2026-01-29'},
        {'c': 102, 'o': 99, 'h': 103, 'l': 99, 'd': '2026-01-28'},
        {'c': 103, 'o': 102, 'h': 104, 'l': 101, 'd': '2026-01-27'},
    ]


@pytest.fixture(scope='function')
def mock_features():
    """Mock feature data برای AI testing"""
    import numpy as np
    return np.array([
        [100, 99, 101, 98, 0.95, 1.2, -0.5],
        [101, 100, 102, 99, 1.05, 1.3, 0.5],
        [99, 101, 102, 98, 0.98, 1.1, 0.2]
    ])


@pytest.fixture(scope='function')
def mock_labels():
    """Mock label data برای model training"""
    return [1, 0, 1]

@pytest.fixture
def app():
    # Use a unique test database per test session to avoid locking issues on Windows
    import uuid
    test_db_path = f"data/test_tse_data_{uuid.uuid4().hex[:8]}.db"
    
    app = create_app()
    app.config.update({
        "TESTING": True,
        "DEBUG": False,
        "CACHE_TYPE": "null" # Disable cache for tests
    })
    
    # Override database for tests
    from app.database import db
    db.db_path = test_db_path
    db._init_db()
    
    # Ensure tables are created before yielding
    with app.app_context():
        db._init_db()
    
    yield app
    
    # Cleanup
    if os.path.exists(test_db_path):
        try:
            # Close connections before removing
            if hasattr(db, 'conn') and db.conn:
                db.conn.close()
            os.remove(test_db_path)
        except:
            pass

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    from app.database import db
    return db
