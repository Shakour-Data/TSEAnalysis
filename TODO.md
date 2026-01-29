# TODO List for TSEAnalysis Project Issues

## High Priority (Security & Critical Bugs)
1. **Fix Security Issues**
   - Remove or warn about firewall bypass techniques (tls_client, curl_cffi) - may violate TOS
   - Secure subprocess execution in tsetmc.py to prevent command injection
   - Disable debug mode in production (app.py)
   - Change host binding to '127.0.0.1' instead of '0.0.0.0' for security
   - Move API keys to environment variables

2. **Fix Failing Tests (Code Bugs)**
   - Fix _make_request error handling in tsetmc.py (test_tsetmc_all_techniques_fail)
   - Fix chart generation in technical_analysis.py (test_ta_full_cycle)
   - Fix API response in /api/fetch_data (test_fetch_data_ta_signals)
   - Fix indicators processing in TA (test_ta_indicators_missing_cols)

## Medium Priority (Performance & Dependencies)
3. **Improve Performance**
   - Replace simple cache with Redis/Memcached for production
   - Fix threading issues in preload (app/__init__.py)
   - Enable WAL mode for SQLite to improve concurrency
   - Add proper rate limiting enforcement

4. **Update Dependencies**
   - Update Flask and other packages to latest secure versions
   - Fix deprecation warnings in flask_caching
   - Pin all dependency versions in requirements.txt

## Low Priority (Structure & Miscellaneous)
5. **Refactor Code Structure**
   - Add type hints throughout the codebase
   - Split large files (tsetmc.py, routes.py) into smaller modules
   - Improve error handling and logging
   - Add input validation for API endpoints

6. **Enhance Architecture**
   - Move configuration to environment variables or config files
   - Add structured logging (JSON format)
   - Improve documentation and docstrings
   - Add monitoring/metrics for performance

7. **Miscellaneous Fixes**
   - Fix Unicode issues in subprocess and logging
   - Improve database schema migration safety
   - Add comprehensive integration tests
   - Prepare for deployment (Docker, CI/CD)