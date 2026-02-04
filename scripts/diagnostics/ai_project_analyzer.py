import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.enhanced_ai import EnhancedAIAssistant, Trend, TechnicalIndicators
from app.services.autonomous_ai import ContentGenerator, ContentType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProjectAIAnalyzer")

def analyze_project_health():
    """
    Uses the project's own AI components to 'analyze' the project's state.
    We map project metrics (coverage, errors) to technical indicators.
    """
    print("\n--- Project AI Health Analysis ---")
    
    # Mock project metrics as 'market indicators'
    # Price = Coverage %
    # Volume = Code size (normalized)
    # RSI = Stability (100 - error_rate)
    
    current_coverage = 51.0 # From our recent run
    target_coverage = 95.0
    
    indicators = TechnicalIndicators(
        price=current_coverage,
        volume=6279, # Total statements
        rsi=40.0,    # High error rate/missing features
        macd=-5.0,   # Negative momentum due to missing space
        macd_signal=-2.0,
        macd_histogram=-3.0,
        sma_20=55.0,
        sma_50=60.0,
        sma_200=70.0,
        bollinger_upper=95.0,
        bollinger_middle=70.0,
        bollinger_lower=40.0,
        atr=10.0,
        adx=35.0,    # Strong bearish trend in coverage
        obv=5000,
        volume_ma=6000
    )
    
    ai = EnhancedAIAssistant()
    trend, confidence = ai._determine_trend(indicators)
    
    # Generate content using project's AI
    # (Checking if ContentGenerator exists, otherwise using basic template)
    try:
        from app.services.autonomous_ai import ContentGenerator
        generator = ContentGenerator()
    except:
        generator = None
    
    report = f"""
    وضعیت پروژه: {trend.value}
    اطمینان مدل: {confidence*100:.1f}%
    
    تحلیل فنی پروژه:
    - پوشش تست (قیمت): {current_coverage}% (زیر میانگین متحرک ۲۰۰ روزه {indicators.sma_200}%)
    - پایداری (RSI): {indicators.rsi} (اشباع فروش - نیاز به بهبود فوری)
    - حجم کد: {indicators.volume} خط
    
    پیشنهاد هوش مصنوعی:
    - {trend.value == Trend.BEARISH and "پروژه در وضعیت بحرانی تست قرار دارد. افزایش پوشش تست توصیه می‌شود." or "وضعیت پروژه مطلوب است."}
    - رفع خطاهای پایگاه داده و تنظیم متغیرهای محیطی.
    """
    
    print(report)
    return report

if __name__ == "__main__":
    analyze_project_health()
