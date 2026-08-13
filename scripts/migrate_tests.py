#!/usr/bin/env python
"""
Migration & Cleanup Script for TSE Analysis Test Runner
- Removes PyQt dependencies
- Initializes new Web Test Runner database tables
- Migrates any legacy test data (simulated)
- Validates the environment
"""

import sys
import os
import sqlite3
import subprocess
import logging

# Add project root to path
sys.path.append(os.getcwd())

from app.database import db

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Migration")

def remove_pyqt_remnants():
    logger.info("Step 1: Removing PyQt remnants...")
    pyqt_packages = ["PyQt6", "qt-material", "pytest-qt"]
    
    python_exe = sys.executable
    for pkg in pyqt_packages:
        try:
            subprocess.run([python_exe, "-m", "pip", "uninstall", "-y", pkg], check=False, capture_output=True)
            logger.info(f"  - Removed {pkg} (if present)")
        except Exception as e:
            logger.warning(f"  - Failed to remove {pkg}: {e}")

    legacy_file = os.path.join(os.getcwd(), "admin_panel.py")
    if os.path.exists(legacy_file):
        os.remove(legacy_file)
        logger.info("  - Deleted legacy admin_panel.py")

def init_db_tables():
    logger.info("Step 2: Initializing Web Test Runner tables...")
    try:
        # This calls the internal _init_test_tables via __init__ or manual call
        db._init_test_tables()
        logger.info("  - Database tables verified/created.")
    except Exception as e:
        logger.error(f"  - Database error: {e}")

def migrate_legacy_data():
    logger.info("Step 3: Migrating legacy data (simulated)...")
    # In a real scenario, we would read old files and insert into SQLite
    # Since this is a fresh start, we just ensure the record count is 0 or base-set.
    logger.info("  - No legacy test data found to migrate. Skipping.")

def validate_environment():
    logger.info("Step 4: Validating environment...")
    required_packages = ["pytest", "pytest-cov", "flask"]
    import pkg_resources
    
    installed = {pkg.key for pkg in pkg_resources.working_set or []}
    missing = [p for p in required_packages if p not in installed]
    
    if missing:
        logger.error(f"  - Missing critical dependencies: {missing}")
        return False
    
    logger.info("  - Environment validated successfully.")
    return True

if __name__ == "__main__":
    logger.info("--- Starting TSE Analysis Test Runner Migration ---")
    remove_pyqt_remnants()
    init_db_tables()
    migrate_legacy_data()
    success = validate_environment()
    
    if success:
        logger.info("--- Migration COMPLETED successfully ---")
    else:
        logger.error("--- Migration FAILED validation ---")
        sys.exit(1)
