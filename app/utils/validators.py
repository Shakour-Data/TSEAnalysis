"""
Data validation اور falsy value handling کے لیے utilities
"""
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    """Falsy values کو صحیح طریقے سے validate کریں"""
    
    @staticmethod
    def is_valid_price(price):
        """قیمت valid ہے یا نہیں؟"""
        try:
            if price is None or price == '':
                return False
            
            # String یا number ہو سکتا ہے
            float_price = float(price)
            
            # قیمت منفی یا صفر نہیں ہو سکتی
            if float_price <= 0:
                logger.warning(f"منفی یا صفر قیمت: {price}")
                return False
            
            # بہت بڑی قیمت شک انگیز ہے
            if float_price > 1e10:
                logger.warning(f"بہت بڑی قیمت: {price}")
                return False
            
            return True
        
        except (ValueError, TypeError) as e:
            logger.warning(f"قیمت validation ناکام: {price} -> {e}")
            return False
    
    @staticmethod
    def is_valid_volume(volume):
        """حجم valid ہے یا نہیں؟"""
        try:
            if volume is None or volume == '':
                return False
            
            int_volume = int(volume)
            
            # حجم منفی یا صفر نہیں ہو سکتی
            if int_volume <= 0:
                logger.warning(f"منفی یا صفر حجم: {volume}")
                return False
            
            return True
        
        except (ValueError, TypeError) as e:
            logger.warning(f"حجم validation ناکام: {volume} -> {e}")
            return False
    
    @staticmethod
    def is_valid_symbol(symbol):
        """نماد valid ہے یا نہیں؟"""
        if not symbol:
            return False
        
        if not isinstance(symbol, str):
            return False
        
        symbol = symbol.strip()
        
        # خالی نہیں ہو سکتا
        if len(symbol) == 0:
            return False
        
        # بہت لمبا نہیں ہو سکتا
        if len(symbol) > 50:
            logger.warning(f"نماد بہت لمبا: {symbol}")
            return False
        
        return True
    
    @staticmethod
    def is_valid_date(date_str):
        """تاریخ valid ہے یا نہیں؟ (YYYY-MM-DD format)"""
        if not date_str or not isinstance(date_str, str):
            return False
        
        try:
            from datetime import datetime
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            logger.warning(f"تاریخ invalid: {date_str}")
            return False
    
    @staticmethod
    def is_valid_number(value, min_value=None, max_value=None):
        """عام نمبر validation"""
        try:
            if value is None or value == '':
                return False
            
            num = float(value)
            
            if min_value is not None and num < min_value:
                logger.warning(f"نمبر بہت چھوٹا: {num} < {min_value}")
                return False
            
            if max_value is not None and num > max_value:
                logger.warning(f"نمبر بہت بڑا: {num} > {max_value}")
                return False
            
            return True
        
        except (ValueError, TypeError) as e:
            logger.warning(f"نمبر validation ناکام: {value} -> {e}")
            return False
    
    @staticmethod
    def ensure_non_empty_list(lst, default=None):
        """List خالی نہ ہو"""
        if not lst or not isinstance(lst, list):
            return default or []
        
        return lst
    
    @staticmethod
    def ensure_non_empty_dict(d, default=None):
        """Dictionary خالی نہ ہو"""
        if not d or not isinstance(d, dict):
            return default or {}
        
        return d
    
    @staticmethod
    def ensure_non_empty_string(s, default=''):
        """String خالی نہ ہو"""
        if not s or not isinstance(s, str):
            return default
        
        s = s.strip()
        if not s:
            return default
        
        return s
    
    @staticmethod
    def validate_ohlcv_candle(candle):
        """
        OHLCV candle valid ہے یا نہیں؟
        Expected keys: open, high, low, close, volume, date
        """
        if not candle or not isinstance(candle, dict):
            logger.warning("Candle dict نہیں ہے")
            return False
        
        required_keys = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        # تمام keys موجود ہیں؟
        for key in required_keys:
            if key not in candle:
                logger.warning(f"Candle میں key missing: {key}")
                return False
        
        # تاریخ valid ہے؟
        if not DataValidator.is_valid_date(candle['date']):
            logger.warning(f"Candle میں invalid تاریخ: {candle['date']}")
            return False
        
        # قیمتیں valid ہیں؟
        for price_key in ['open', 'high', 'low', 'close']:
            if not DataValidator.is_valid_price(candle[price_key]):
                logger.warning(f"Candle میں invalid قیمت {price_key}: {candle[price_key]}")
                return False
        
        # قیمت کی ترتیب صحیح ہے؟ (low <= open,close <= high)
        try:
            low = float(candle['low'])
            high = float(candle['high'])
            open_p = float(candle['open'])
            close_p = float(candle['close'])
            
            if not (low <= open_p <= high and low <= close_p <= high):
                logger.warning(f"Candle میں قیمت کی ترتیب غلط: {candle}")
                return False
        
        except (ValueError, TypeError):
            logger.warning(f"Candle price conversion ناکام: {candle}")
            return False
        
        # حجم valid ہے؟
        if not DataValidator.is_valid_volume(candle['volume']):
            logger.warning(f"Candle میں invalid حجم: {candle['volume']}")
            return False
        
        return True
    
    @staticmethod
    def filter_valid_candles(candles):
        """
        غلط candles کو نکال کر صرف valid candles واپس کریں
        """
        if not candles or not isinstance(candles, list):
            return []
        
        valid = []
        for i, candle in enumerate(candles):
            if DataValidator.validate_ohlcv_candle(candle):
                valid.append(candle)
            else:
                logger.warning(f"Candle #{i} invalid ہے، skip کر رہے ہیں")
        
        if len(valid) < len(candles):
            logger.info(f"✅ {len(valid)}/{len(candles)} candles valid ہیں")
        
        return valid

