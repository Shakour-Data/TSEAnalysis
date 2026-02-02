"""
Smart Rate Limiter for TSETMC API
- مدیریت هوشمند میزان درخواست‌ها
- تطبیق داینامیکی بر اساس شرایط
- پیشگیری از blocking
"""

import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SmartRateLimiter:
    """
    نرخ‌محدود کننده هوشمند برای API
    """
    
    def __init__(self, base_delay=2.0, max_delay=60.0, max_attempts=3, backoff_factor=2.0):
        """
        Args:
            base_delay: تاخیر پایه بین درخواست‌ها (ثانیه)
            max_delay: حداکثر تاخیر (ثانیه)
            max_attempts: حداکثر تلاش مجدد
            backoff_factor: ضریب افزایش تاخیر
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_delay = base_delay
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        
        self.last_request_time = 0
        self.consecutive_failures = 0
        self.last_failure_time = None
        self.reset_time = None
    
    def wait_before_request(self):
        """
        Waits for the calculated delay time before allowing a new request.
        """
        time_since_last = time.time() - self.last_request_time
        wait_time = self.current_delay - time_since_last
        if wait_time > 0:
            time.sleep(wait_time)
        self.last_request_time = time.time()

    def on_success(self):
        """
        Resets the delay to the base delay after a successful request.
        """
        self.current_delay = self.base_delay
        logger.info(f"Request successful, delay reset to {self.current_delay:.2f}s")
    
    def on_failure(self, error_code=None):
        """فراخوانی شده هنگام شکست درخواست."""
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        
        # افزایش تاخیر بر اساس نوع خطا
        if error_code == 429:  # Too Many Requests
            self.current_delay = min(
                self.max_delay,
                self.current_delay * 3  # مسئله‌تر برای rate limiting
            )
            logger.warning(f"429 Too Many Requests - delay: {self.current_delay:.1f}s")
        
        elif error_code == 503:  # Service Unavailable
            self.current_delay = min(
                self.max_delay,
                self.current_delay * 2
            )
            logger.warning(f"503 Service Unavailable - delay: {self.current_delay:.1f}s")
        
        else:  # سایر خطاها
            self.current_delay = min(
                self.max_delay,
                self.current_delay * self.backoff_factor
            )
            logger.warning(f"Request failed - delay: {self.current_delay:.1f}s")
    
    def should_retry(self):
        """تعیین اینکه آیا باید دوباره تلاش کنیم."""
        if self.consecutive_failures >= self.max_attempts:
            logger.error(f"Max retries ({self.max_attempts}) exceeded")
            return False
        return True
    
    def get_status(self):
        """کسب وضعیت فعلی rate limiter."""
        return {
            "current_delay": self.current_delay,
            "consecutive_failures": self.consecutive_failures,
            "last_request_time": datetime.fromtimestamp(self.last_request_time),
            "last_failure_time": datetime.fromtimestamp(self.last_failure_time) if self.last_failure_time else None
        }


class AdaptiveUpdateScheduler:
    """
    برنامه‌ریزی آپدیت متناسب با شرایط API
    """
    
    def __init__(self):
        self.rate_limiter = SmartRateLimiter()
        self.api_health_score = 100  # 0-100
        self.update_schedule = {}  # نقشه برنامة آپدیت
    
    def calculate_daily_quota(self):
        """محاسبه تعداد نمادهایی که می‌توانند امروز آپدیت شوند."""
        # بر اساس وضعیت API
        base_quota = 100  # پایه 100 نماد در روز
        
        if self.api_health_score > 90:
            return base_quota  # سرعت عادی
        elif self.api_health_score > 70:
            return int(base_quota * 0.7)  # کاهش 30%
        elif self.api_health_score > 50:
            return int(base_quota * 0.4)  # کاهش 60%
        else:
            return int(base_quota * 0.2)  # کاهش 80%
    
    def update_api_health(self, success_rate):
        """بروزرسانی نمره سلامت API."""
        # success_rate بین 0 و 1
        self.api_health_score = int(success_rate * 100)
        
        if success_rate < 0.5:
            logger.warning(f"⚠️  API health low: {self.api_health_score}%")
        elif success_rate > 0.9:
            logger.info(f"✅ API health good: {self.api_health_score}%")
    
    def get_next_update_time(self, priority="normal"):
        """محاسبه زمان آپدیت بعدی."""
        if priority == "critical":
            delay = self.rate_limiter.current_delay * 1.5
        elif priority == "high":
            delay = self.rate_limiter.current_delay * 2
        else:
            delay = self.rate_limiter.current_delay * 3
        
        return datetime.now() + timedelta(seconds=delay)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    limiter = SmartRateLimiter()
    print("Testing rate limiter...")
    
    for i in range(5):
        limiter.wait_before_request()
        if i % 2 == 0:
            limiter.on_success()
        else:
            limiter.on_failure(429)
        print(f"Request {i+1}: {limiter.get_status()}")
