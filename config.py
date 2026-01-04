"""
تنظیمات پروژه و کلید API
"""

class Config:
    # کلید دسترسی BrsApi
    BRS_API_KEY = "BA9C8JBliDmfPapn9WYTX76uR5Q3m2r3"
    
    # آدرس‌های API
    BRS_CANDLE_URL = "https://BrsApi.ir/Api/Bourse/Candlestick.php"
    BRS_ALL_SYMBOLS_URL = "https://BrsApi.ir/Api/Tsetmc/AllSymbols.php"
    BRS_INDEX_URL = "https://BrsApi.ir/Api/Bourse/Index.php"
    BRS_GOLD_CURRENCY_URL = "https://BrsApi.ir/Api/Free/GoldCurrency.php"
    BRS_CODAL_URL = "https://BrsApi.ir/Api/Bourse/Codal.php"
    BRS_TRANSACTION_URL = "https://BrsApi.ir/Api/Bourse/Transaction.php"
    BRS_SHAREHOLDER_URL = "https://BrsApi.ir/Api/Bourse/Shareholder.php"
    BRS_ETF_URL = "https://BrsApi.ir/Api/Bourse/ETF.php"
    BRS_OPTION_URL = "https://BrsApi.ir/Api/Bourse/Option.php"
    BRS_COMMODITY_URL = "https://BrsApi.ir/Api/Free/Commodity.php"
    BRS_CRYPTO_URL = "https://BrsApi.ir/Api/Free/Cryptocurrency.php"
    BRS_HISTORY_URL = "https://BrsApi.ir/Api/Bourse/History.php"
    
    # هدر مورد نیاز برای جلوگیری از مسدود شدن IP
    COMMON_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
    }
    
    # تنظیمات پیش‌فرض
    DEFAULT_CANDLE_COUNT = 100
    DEFAULT_DATA_TYPE = 2  # 1: لحظه‌ای، 2: تعدیل‌نشده، 3: تعدیل‌شده
    
    # تنظیمات Flask
    SECRET_KEY = "your-secret-key-here-change-in-production"
    DEBUG = True