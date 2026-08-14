#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("Testing health check...")
try:
    from app import create_app
    print("App imported successfully")
    app = create_app()
    print("App created successfully")
    with app.test_client() as client:
        response = client.get('/api/health')
        print('Status:', response.status_code)
        data = response.get_json()
        print('Response:', data)
except Exception as e:
    print('Error:', str(e))
    import traceback
    traceback.print_exc()