"""
Unicode اور encoding issues کو handle کریں
"""
import logging
import json
from urllib.parse import quote, unquote
from typing import Any
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)

class EncodingHandler:
    """Unicode اور encoding کے مسائل حل کریں"""
    
    # مختلف encoding formats
    ENCODINGS = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'iso-8859-1']
    
    @staticmethod
    def safe_encode(text, target_encoding='utf-8'):
        """متن کو محفوظ طریقے سے encode کریں"""
        if text is None:
            return None
        
        if isinstance(text, bytes):
            try:
                return text.decode('utf-8')
            except UnicodeDecodeError:
                # دوسری encoding آزمائیں
                for enc in EncodingHandler.ENCODINGS:
                    try:
                        return text.decode(enc)
                    except (UnicodeDecodeError, LookupError):
                        continue
                logger.warning(f"کردار decode نہیں ہو سکے: {text[:50]}")
                return text.decode('utf-8', errors='replace')
        
        if not isinstance(text, str):
            text = str(text)
        
        try:
            return text.encode(target_encoding).decode(target_encoding)
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            logger.warning(f"Encoding issue: {e}")
            return text.encode(target_encoding, errors='replace').decode(target_encoding)
    
    @staticmethod
    def safe_decode(encoded_text: bytes, encoding: str = "utf-8") -> str | None:
        """
        Decodes a byte string to a string using the specified encoding,
        handling potential errors by returning None.
        """
        if not isinstance(encoded_text, bytes):
            try:
                return str(encoded_text)
            except Exception:
                return None
        try:
            return encoded_text.decode(encoding)
        except (UnicodeDecodeError, LookupError) as e:
            logger.error(f"Decode failed for {encoding}: {e}")
            return None

    @staticmethod
    def normalize_unicode(text: str, form: str = "NFC") -> str:
        """
        Unicode نارملائزیشن - مختلف forms کو یکساں کریں

        Args:
            text (str): وہ متن جسے نارملائز کرنا ہے
            form (str): نارملائزیشن کی شکل (NFC یا NFD)

        Returns:
            str: نارملائزڈ متن
        """
        if not text or not isinstance(text, str):
            return text
        
        import unicodedata
        
        try:
            # NFC normalization (Composed form)
            normalized = unicodedata.normalize('NFC', text)
            return normalized
        except Exception as e:
            logger.warning(f"Unicode normalization ناکام: {e}")
            return text
    
    @staticmethod
    def remove_control_characters(text: str) -> str:
        """کنٹرول کریکٹرز کو ہٹائیں"""
        if not isinstance(text, str):
            return text
        
        import unicodedata
        
        # تمام control characters کو ہٹائیں
        cleaned = ''.join(
            char for char in text 
            if unicodedata.category(char)[0] != 'C' or char in '\n\r\t'
        )
        
        return cleaned
    
    @staticmethod
    def detect_encoding(text):
        """متن کی encoding detect کریں"""
        if isinstance(text, str):
            return 'utf-8'  # Python 3 میں strings UTF-8 ہیں
        
        if isinstance(text, bytes):
            for enc in EncodingHandler.ENCODINGS:
                try:
                    text.decode(enc)
                    logger.debug(f"Encoding detected: {enc}")
                    return enc
                except (UnicodeDecodeError, LookupError):
                    continue
        
        return 'utf-8'  # Default
    
    @staticmethod
    def safe_json_dumps(obj, **kwargs):
        """JSON میں محفوظ طریقے سے convert کریں (Unicode support)"""
        def default_serializer(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, set):
                return list(obj)
            logger.error(f"JSON encode ناکام: Object of type {type(obj).__name__} is not JSON serializable")
            # Forcing a TypeError to be caught by the outer handler if it's truly unhandled
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        try:
            return json.dumps(obj, default=default_serializer, ensure_ascii=False, **kwargs)
        except TypeError as e:
            logger.error(f"JSON encode ناکام: {e}")
            return json.dumps({"error": str(e)})

    @staticmethod
    def safe_json_loads(text, **kwargs):
        """JSON سے محفوظ طریقے سے decode کریں"""
        if not text:
            return None
        
        try:
            # پہلے text کو decode کریں
            if isinstance(text, bytes):
                text = text.decode('utf-8')
            
            return json.loads(text, **kwargs)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode ناکام: {e}")
            # Fallback - اضافی whitespace/control characters کو ہٹائیں
            text_cleaned = EncodingHandler.remove_control_characters(text)
            try:
                return json.loads(text_cleaned)
            except json.JSONDecodeError:
                logger.error(f"JSON decode retry ناکام: {text[:100]}")
                return None
    
    @staticmethod
    def sanitize_string(
        input_string: Any, max_length: int = 255, ellipsis: str = "..."
    ) -> str:
        """
        Sanitizes a string by converting to string, stripping whitespace,
        and truncating if necessary.

        Args:
            input_string (Any): The input to sanitize.
            max_length (int): The maximum allowed length.
            ellipsis (str): The string to append if truncated.

        Returns:
            str: The sanitized string.
        """
        if not isinstance(input_string, str):
            s = str(input_string)
        else:
            s = input_string

        s = s.strip()

        if max_length is not None and len(s) > max_length:
            return s[:max_length] + ellipsis
        return s

    @staticmethod
    def urlencode_safely(url_or_param: str) -> str:
        """URL encoding محفوظ طریقے سے"""
        if url_or_param is None:
            return ""
        try:
            return quote(url_or_param, safe="")
        except Exception as e:
            logger.warning(f"URL encode ناکام: {e}")
            return url_or_param

    @staticmethod
    def urldecode_safely(encoded_text: str) -> str:
        """URL decoding محفوظ طریقے سے"""
        if encoded_text is None:
            return ""
        try:
            return unquote(encoded_text, errors='replace')
        except Exception as e:
            logger.warning(f"URL decoding ناکام: {e}")
            return encoded_text
    
    @staticmethod
    def clean_symbol_string(symbol):
        """نماد کو صاف کریں (encoding + validation)"""
        if not symbol:
            return None
        
        if not isinstance(symbol, str):
            symbol = str(symbol)
        
        # Sanitize کریں
        symbol = EncodingHandler.sanitize_string(symbol, max_length=50, ellipsis='')
        
        # صرف alphanumeric اور `-` رکھیں
        import re
        symbol = re.sub(r'[^a-zA-Z0-9\-_آ-ی]', '', symbol)
        
        if not symbol:
            logger.warning(f"Symbol cleanup نے خالی نتیجہ دیا")
            return None
        
        return symbol
    
    @staticmethod
    def convert_to_string(value):
        """کوئی بھی value کو محفوظ طریقے سے string میں تبدیل کریں"""
        if value is None:
            return None
        
        if isinstance(value, str):
            return EncodingHandler.safe_encode(value)
        
        if isinstance(value, bytes):
            return EncodingHandler.safe_decode(value)
        
        # دوسری types
        text = str(value)
        return EncodingHandler.safe_encode(text)

