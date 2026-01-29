import pytest
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.database import SymbolDatabase

# Register custom marks
def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration test")

# Suppress deprecation warnings
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="flask_caching")

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
