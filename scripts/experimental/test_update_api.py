#!/usr/bin/env python3
"""
🧪 API Testing Script - ٹیسٹ تمام آپڈیٹ endpoints
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_response(response, name):
    print(f"📌 {name}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print("Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(f"Response: {response.text}")
    print()

def test_all_endpoints():
    """تمام endpoints کو ٹیسٹ کریں"""
    
    print_header("🧪 API ENDPOINTS TESTING")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Base URL: {BASE_URL}\n")
    
    # ٹیسٹ 1: Status چیک کریں
    print_header("1️⃣ GET /api/updates/status")
    try:
        response = requests.get(f"{BASE_URL}/api/updates/status")
        print_response(response, "Current Status")
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False
    
    # ٹیسٹ 2: Progress چیک کریں
    print_header("2️⃣ GET /api/updates/progress")
    try:
        response = requests.get(f"{BASE_URL}/api/updates/progress")
        print_response(response, "Progress Details")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # ٹیسٹ 3: Failed symbols چیک کریں
    print_header("3️⃣ GET /api/updates/failed")
    try:
        response = requests.get(f"{BASE_URL}/api/updates/failed")
        print_response(response, "Failed Symbols")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # ٹیسٹ 4: Start اپڈیٹ
    print_header("4️⃣ POST /api/updates/start")
    try:
        response = requests.post(f"{BASE_URL}/api/updates/start")
        print_response(response, "Start Update")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # تھوڑا انتظار کریں
    time.sleep(2)
    
    # ٹیسٹ 5: دوبارہ status چیک کریں
    print_header("5️⃣ GET /api/updates/status (After Start)")
    try:
        response = requests.get(f"{BASE_URL}/api/updates/status")
        print_response(response, "Status After Start")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # ٹیسٹ 6: Stop اپڈیٹ
    print_header("6️⃣ POST /api/updates/stop")
    try:
        response = requests.post(f"{BASE_URL}/api/updates/stop")
        print_response(response, "Stop Update")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # ٹیسٹ 7: Resume اپڈیٹ
    print_header("7️⃣ POST /api/updates/resume")
    try:
        response = requests.post(f"{BASE_URL}/api/updates/resume")
        print_response(response, "Resume Update")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    print_header("✅ تمام ٹیسٹ مکمل!")
    print("""
    📊 اگلے مرحلہ:
    
    1. لاگ فائل دیکھیں:
       tail -f database_update.log
    
    2. پیشرفت کی نگرانی کریں:
       curl http://localhost:5000/api/updates/progress
    
    3. ناکام نمادیں دیکھیں:
       curl http://localhost:5000/api/updates/failed
    """)

if __name__ == "__main__":
    try:
        test_all_endpoints()
    except KeyboardInterrupt:
        print("\n\n⚠️  صارف نے ٹیسٹ منسوخ کیا")
    except Exception as e:
        print(f"\n❌ خرابی: {e}")
