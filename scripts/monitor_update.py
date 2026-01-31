#!/usr/bin/env python3
"""
📊 Real-time Database Update Monitor
آپڈیٹ کی پیشرفت کو حقیقی وقت میں دیکھیں
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path

class UpdateMonitor:
    def __init__(self, api_url="http://localhost:5000"):
        self.api_url = api_url
        self.progress_file = Path("data/update_progress.json")
        self.last_percentage = 0
        
    def clear_screen(self):
        """اسکرین صاف کریں"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_progress_from_api(self):
        """API سے پیشرفت حاصل کریں"""
        try:
            response = requests.get(f"{self.api_url}/api/updates/progress")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def get_progress_from_file(self):
        """فائل سے پیشرفت حاصل کریں"""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return None
    
    def get_status(self):
        """موجودہ حالت حاصل کریں"""
        try:
            response = requests.get(f"{self.api_url}/api/updates/status")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def get_failed(self):
        """ناکام نمادیں حاصل کریں"""
        try:
            response = requests.get(f"{self.api_url}/api/updates/failed")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def draw_progress_bar(self, percentage, width=50):
        """Progress bar بنائیں"""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {percentage:.1f}%"
    
    def format_time_remaining(self, days_left):
        """باقی وقت فارمیٹ کریں"""
        if days_left < 1:
            hours = int(days_left * 24)
            minutes = int((days_left * 24 * 60) % 60)
            return f"{hours}h {minutes}m"
        else:
            return f"{days_left:.1f} days"
    
    def display_dashboard(self):
        """ڈیش بورڈ دکھائیں"""
        self.clear_screen()
        
        # ہیڈر
        print("╔" + "═" * 78 + "╗")
        print("║" + " 📊 DATABASE UPDATE MONITOR - اپڈیٹ مانیٹر ".center(78) + "║")
        print("║" + f" Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".ljust(78) + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        
        # پیشرفت حاصل کریں
        progress = self.get_progress_from_api()
        if not progress:
            progress = self.get_progress_from_file()
        
        if progress:
            percentage = progress.get('percentage', 0)
            updated = progress.get('updated', 0)
            failed = progress.get('failed', 0)
            total = progress.get('total', 1919)
            pending = progress.get('pending', 0)
            days_left = progress.get('days_left', 0)
            daily_quota = progress.get('daily_quota', 100)
            
            # Progress bar
            print("📈 PROGRESS")
            print(self.draw_progress_bar(percentage))
            print()
            
            # تفصیلات
            print("📋 DETAILS")
            print(f"   Updated:    {updated:>5} / {total:<5} symbols")
            print(f"   Failed:     {failed:>5} symbols (retry)")
            print(f"   Pending:    {pending:>5} symbols")
            print(f"   Daily Quota: {daily_quota} symbols/day")
            print()
            
            # وقت
            print("⏱️  TIME ESTIMATE")
            time_remaining = self.format_time_remaining(days_left)
            print(f"   Days Left:  {time_remaining}")
            print()
            
            # روزانہ کی رفتار
            if daily_quota > 0:
                symbols_per_minute = daily_quota / 5  # تقریباً 5 منٹ میں مکمل ہوتا ہے
                print("⚡ SPEED")
                print(f"   Symbols/min: {symbols_per_minute:.1f}")
                print()
        
        # حالت
        status = self.get_status()
        if status:
            print("🔄 STATUS")
            print(f"   State:      {status.get('status', 'UNKNOWN')}")
            print(f"   Message:    {status.get('message', 'N/A')}")
            current = status.get('current_symbol', 'N/A')
            if current and current != 'None':
                print(f"   Current:    {current}")
            print()
        
        # ناکام نمادیں
        failed_data = self.get_failed()
        if failed_data and failed_data.get('failed'):
            print("❌ FAILED SYMBOLS (Retrying)")
            failed_list = failed_data.get('failed', [])
            for i, item in enumerate(failed_list[:5], 1):
                symbol = item.get('symbol', 'N/A')
                tries = item.get('tries', 0)
                print(f"   {i}. {symbol} (Attempt {tries})")
            
            total_failed = failed_data.get('total_failed', 0)
            if total_failed > 5:
                print(f"   ... اور {total_failed - 5} مزید")
            print()
        
        # نیچے کی معلومات
        print("─" * 80)
        print("💡 نکات:")
        print("   • F5 دوبارہ تازہ کریں")
        print("   • Ctrl+C منسوخ کریں")
        print("   • API: http://localhost:5000/api/updates/status")
        print()
    
    def run(self, refresh_interval=5):
        """مسلسل مانیٹور کریں"""
        print("🚀 شروع کیے جا رہے ہیں... ")
        time.sleep(1)
        
        try:
            while True:
                self.display_dashboard()
                
                # انتظار کریں
                for i in range(refresh_interval):
                    time.sleep(1)
                    print(f"⏳ اگلی تازہ کاری میں {refresh_interval - i}s...", end='\r')
                print(" " * 50, end='\r')  # صاف کریں
                
        except KeyboardInterrupt:
            print("\n\n✋ مانیٹر بند کیا گیا")

def main():
    """اہم فنکشن"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Update Monitor")
    parser.add_argument(
        '--url',
        default='http://localhost:5000',
        help='API URL (default: http://localhost:5000)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Refresh interval in seconds (default: 5)'
    )
    
    args = parser.parse_args()
    
    monitor = UpdateMonitor(api_url=args.url)
    monitor.run(refresh_interval=args.interval)

if __name__ == "__main__":
    main()
