"""
Intelligent Database Update Scheduler
- آپدیت تدریجی و خودکار دیتابیس
- مدیریت Rate Limiting API
- ردیابی پیشرفت روز به روز
- دوباره تلاش برای failures
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
from app.services.tsetmc import client
from app.database import db

# لاگنگ سیٹ اپ
log_file = Path("database_update.log").absolute()
if not logging.getLogger('incremental_updater').handlers:
    logger = logging.getLogger('incremental_updater')
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
else:
    logger = logging.getLogger('incremental_updater')

class IncrementalDatabaseUpdater:
    """
    سیستم هوشمند برای آپدیت تدریجی دیتابیس
    
    ویژگی‌ها:
    - آپدیت N نماد در روز
    - احترام به rate limiting API
    - ردیابی خودکار پیشرفت
    - دوباره تلاش برای failures
    - استمرار از جایی که متوقف شد
    """
    
    def __init__(self, symbols_per_day=100, api_delay=2.0):
        """
        Args:
            symbols_per_day: تعداد نمادهای آپدیت در روز
            api_delay: تاخیر بین API requests (ثانیه)
        """
        self.symbols_per_day = symbols_per_day
        self.api_delay = api_delay
        self.progress_file = Path("data/update_progress.json")
        self.status_file = Path("data/update_status.json")
        self.is_running = False
        self.thread = None
        
        # بارگیری پیشرفت موجود
        self.progress = self._load_progress()
    
    def _load_progress(self):
        """بارگیری وضعیت آپدیت از فایل."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load progress: {e}")
        
        return {
            "start_date": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "symbols_updated": 0,
            "symbols_failed": 0,
            "total_symbols": 0,
            "completed_symbols": [],
            "failed_symbols": [],
            "daily_progress": {}
        }
    
    def _save_progress(self):
        """ذخیره وضعیت آپدیت."""
        try:
            self.progress["last_update"] = datetime.now().isoformat()
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def _save_status(self, message):
        """ذخیره وضعیت فعلی برای نمایش."""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "progress": {
                    "updated": self.progress.get("symbols_updated", 0),
                    "failed": self.progress.get("symbols_failed", 0),
                    "total": self.progress.get("total_symbols", 0)
                }
            }
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving status: {e}")
    
    def get_status(self):
        """بازگرداندن وضعیت فعلی."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "timestamp": datetime.now().isoformat(),
            "message": "No update running",
            "progress": {"updated": 0, "failed": 0, "total": 0}
        }
    
    def start(self):
        """شروع سرویس آپدیت خودکار."""
        if self.is_running:
            logger.warning("Updater already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        logger.info("✅ Incremental database updater started")
    
    def stop(self):
        """توقف سرویس."""
        self.is_running = False
        logger.info("Database updater stopped")
    
    def _update_loop(self):
        """حلقه اصلی آپدیت."""
        while self.is_running:
            try:
                self._run_daily_update()
                
                # خواب تا فردا
                sleep_hours = 24
                logger.info(f"Next update in {sleep_hours} hours")
                time.sleep(sleep_hours * 3600)
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(3600)  # خواب 1 ساعت اگر خطا
    
    def _run_daily_update(self):
        """اجرای آپدیت روزانه."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Starting daily update cycle: {today}")
        logger.info(f"{'='*60}")
        
        # کل نمادها
        all_symbols = db.get_all_symbols()
        self.progress["total_symbols"] = len(all_symbols)
        
        # نمادهای باقی‌مانده (هنوز آپدیت نشده)
        pending_symbols = [
            sym for sym in all_symbols 
            if sym.get('l18') not in self.progress.get("completed_symbols", [])
        ]
        
        logger.info(f"Total symbols: {len(all_symbols)}")
        logger.info(f"Pending updates: {len(pending_symbols)}")
        logger.info(f"Already updated: {len(self.progress.get('completed_symbols', []))}")
        logger.info(f"Failed (retrying): {len(self.progress.get('failed_symbols', []))}")
        
        if not pending_symbols:
            logger.info("✅ All symbols updated! Resetting for next cycle...")
            self.progress["completed_symbols"] = []
            self.progress["failed_symbols"] = []
            self._save_progress()
            return
        
        # بررسی پیشرفت امروز
        today_progress = self.progress.get("daily_progress", {}).get(today, {})
        completed_today = today_progress.get("actual", 0)
        
        # اگر امروز پیشرفت داشته، از همانجا ادامه بده
        if completed_today > 0:
            start_idx = completed_today
            logger.info(f"📍 Resuming from symbol {start_idx + 1} (completed {completed_today} today)")
        else:
            start_idx = 0
        
        # اخذ نمادهای امروز (از جایی که متوقف شد)
        symbols_today = pending_symbols[start_idx:start_idx + self.symbols_per_day]
        
        # اگر نمادی باقی نمانده، پایان روز
        if not symbols_today:
            logger.info("✅ Today's quota completed! Waiting for tomorrow...")
            return
        
        daily_stat = {
            "date": today,
            "target": self.symbols_per_day,
            "actual": completed_today,  # شروع از پیشرفت قبلی
            "failed": today_progress.get("failed", 0),
            "updated_symbols": today_progress.get("updated_symbols", [])
        }
        
        # آپدیت هر نماد
        for idx, sym_data in enumerate(symbols_today, start_idx + 1):
            symbol = sym_data.get('l18')
            
            if not self.is_running:
                break
            
            try:
                # نمایش پیشرفت (کل نمادهای امروز)
                total_today = min(len(pending_symbols), self.symbols_per_day)
                pct = (idx / total_today) * 100
                logger.info(f"\n[{idx}/{total_today}] {pct:.1f}% - Updating: {symbol}")
                
                # دریافت داده‌های جدید
                history = client.get_price_history(symbol, force_refresh=True)
                
                if history and len(history) > 0:
                    # ذخیره در دیتابیس
                    db.save_history(symbol, history)
                    
                    self.progress["symbols_updated"] += 1
                    self.progress["completed_symbols"].append(symbol)
                    daily_stat["updated_symbols"].append(symbol)
                    daily_stat["actual"] += 1
                    
                    logger.debug(f"    ✅ {symbol}: {len(history)} records saved")
                else:
                    logger.warning(f"    ⚠️  {symbol}: No data received")
                    if symbol not in self.progress.get("failed_symbols", []):
                        self.progress["failed_symbols"].append(symbol)
                    daily_stat["failed"] += 1
                
            except Exception as e:
                logger.warning(f"    ❌ {symbol}: {str(e)[:50]}")
                if symbol not in self.progress.get("failed_symbols", []):
                    self.progress["failed_symbols"].append(symbol)
                self.progress["symbols_failed"] += 1
                daily_stat["failed"] += 1
            
            # Rate limiting
            time.sleep(self.api_delay)
        
        # ذخیره پیشرفت
        self.progress["daily_progress"][today] = daily_stat
        self._save_progress()
        
        # خلاصه روزانه
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 Daily Summary: {today}")
        logger.info(f"{'='*60}")
        logger.info(f"  Updated today: {daily_stat['actual']}/{self.symbols_per_day}")
        logger.info(f"  Failed today: {daily_stat['failed']}")
        logger.info(f"  Total progress: {self.progress['symbols_updated']}/{len(all_symbols)}")
        
        # محاسبه روز‌های باقی
        remaining = len(pending_symbols) - len(symbols_today)
        if remaining > 0:
            days_left = (remaining + self.symbols_per_day - 1) // self.symbols_per_day
            logger.info(f"  Estimated days left: {days_left}")
        else:
            logger.info(f"  ✅ All symbols will be updated soon!")
        
        logger.info(f"{'='*60}\n")
        
        # بروزرسانی وضعیت
        msg = f"Daily update: {daily_stat['actual']} updated, {daily_stat['failed']} failed"
        self._save_status(msg)

# تابع helper برای شروع سرویس
_updater_instance = None

def get_updater(symbols_per_day=100):
    """کسب نمونه updater."""
    global _updater_instance
    if _updater_instance is None:
        _updater_instance = IncrementalDatabaseUpdater(symbols_per_day=symbols_per_day)
    return _updater_instance

def start_updater(symbols_per_day=100):
    """شروع سرویس آپدیت."""
    updater = get_updater(symbols_per_day)
    updater.start()
    return updater

if __name__ == "__main__":
    # تنظیم logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('database_update.log', encoding='utf-8')
        ]
    )
    
    # تست
    print("Testing incremental updater...")
    updater = IncrementalDatabaseUpdater(symbols_per_day=10)
    print(f"Current progress: {json.dumps(updater.progress, ensure_ascii=False, indent=2)}")
