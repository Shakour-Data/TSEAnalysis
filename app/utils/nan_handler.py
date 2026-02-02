"""
NaN values کو handle کرنے کی سہولیات
"""
import logging
import numpy as np
import pandas as pd
from typing import Union, List, Dict, Any

logger = logging.getLogger(__name__)

class NaNHandler:
    """NaN values کو detect، clean اور handle کریں"""
    
    @staticmethod
    def has_nan(value):
        """چیک کریں کہ value NaN ہے؟"""
        try:
            if value is None:
                return False
            if isinstance(value, float):
                return np.isnan(value)
            if isinstance(value, (pd.Series, pd.DataFrame)):
                return value.isna().any().any() if isinstance(value, pd.DataFrame) else value.isna().any()
            if isinstance(value, (int, str, list, dict)):
                return False
            return False
        except (TypeError, ValueError):
            return False
    
    @staticmethod
    def replace_nan(value, replacement=0):
        """NaN کو کسی چیز سے replace کریں"""
        if NaNHandler.has_nan(value):
            return replacement
        return value
    
    @staticmethod
    def remove_nan_values(lst):
        """لسٹ سے NaN values کو ہٹائیں"""
        if not lst or not isinstance(lst, list):
            return []
        
        result = []
        for item in lst:
            if not NaNHandler.has_nan(item):
                result.append(item)
        
        return result
    
    @staticmethod
    def clean_dataframe_nan(df, strategy='drop'):
        """
        DataFrame سے NaN کو صاف کریں
        strategy:
            - 'drop': NaN والی rows کو ہٹائیں
            - 'forward_fill': آگے والی value سے fill کریں
            - 'backward_fill': پیچھے والی value سے fill کریں
            - 'mean': column کی mean سے fill کریں
            - 'zero': صفر سے fill کریں
        """
        if not isinstance(df, pd.DataFrame):
            logger.warning("Input is not a DataFrame")
            return df
        
        try:
            if strategy == 'drop':
                result = df.dropna()
                dropped = len(df) - len(result)
                if dropped > 0:
                    logger.info(f"✅ {dropped} NaN rows ہٹائے گئے")
            
            elif strategy == 'forward_fill':
                result = df.fillna(method='ffill')
                logger.debug("✅ Forward fill applied")
            
            elif strategy == 'backward_fill':
                result = df.fillna(method='bfill')
                logger.debug("✅ Backward fill applied")
            
            elif strategy == 'mean':
                # numeric columns کے لیے mean
                result = df.fillna(df.mean(numeric_only=True))
                logger.debug("✅ Mean fill applied")
            
            elif strategy == 'zero':
                result = df.fillna(0)
                logger.debug("✅ Zero fill applied")
            
            else:
                logger.warning(f"Unknown strategy: {strategy}")
                result = df
            
            return result
        
        except Exception as e:
            logger.error(f"DataFrame NaN cleaning ناکام: {e}")
            return df
    
    @staticmethod
    def clean_dict_nan(d):
        """Dictionary سے NaN values کو ہٹائیں"""
        if not isinstance(d, dict):
            return d
        
        cleaned = {}
        for key, value in d.items():
            if NaNHandler.has_nan(value):
                cleaned[key] = None  # یا skip کریں
            elif isinstance(value, dict):
                cleaned[key] = NaNHandler.clean_dict_nan(value)
            elif isinstance(value, list):
                cleaned[key] = [v for v in value if not NaNHandler.has_nan(v)]
            else:
                cleaned[key] = value
        
        return cleaned
    
    @staticmethod
    def get_nan_statistics(data):
        """NaN کی معلومات دریافت کریں"""
        if data is None or not isinstance(data, pd.DataFrame) or data.size == 0:
            return {'total_nan': 0, 'total_cells': 0, 'nan_percentage': 0, 'by_column': {}}
        
        nan_stats = {
            'total_cells': data.size,
            'total_nan': data.isna().sum().sum(),
            'nan_percentage': (data.isna().sum().sum() / data.size * 100),
            'by_column': {}
        }
        
        for col in data.columns:
            nan_count = data[col].isna().sum()
            if nan_count > 0:
                nan_stats['by_column'][col] = {
                    'count': nan_count,
                    'percentage': (nan_count / len(data) * 100)
                }
        
        return nan_stats
    
    @staticmethod
    def handle_ohlcv_nan(df: pd.DataFrame, strategy: str = "forward_fill") -> None:
        """
        Handles NaN values specifically in OHLCV DataFrames.
        A common strategy is forward-fill, assuming the value hasn't changed.

        Args:
            df (pd.DataFrame): The OHLCV DataFrame.
            strategy (str): The strategy to use for filling NaNs.
        """
        if not isinstance(df, pd.DataFrame) or df.empty:
            return

        for col in ["open", "high", "low", "close", "volume"]:
            if col in df:
                NaNHandler.validate_numeric_column(df, col, strategy)

        logger.info(f"✅ OHLCV NaN handling مکمل - {len(df)} rows")

    @staticmethod
    def validate_numeric_column(
        df: pd.DataFrame, column_name: str, strategy: str = "drop"
    ):
        """
        Validates that a column is numeric and handles NaNs based on a strategy.
        This now performs the operation in-place on the DataFrame.
        """
        if column_name not in df.columns:
            logger.warning(f"Column '{column_name}' not found in DataFrame.")
            return

        # Ensure column is numeric, coercing errors
        df[column_name] = pd.to_numeric(df[column_name], errors="coerce")

        if df[column_name].isna().any():
            if strategy == "zero":
                df[column_name].fillna(0, inplace=True)
            elif strategy == "mean":
                mean_val = df[column_name].mean()
                df[column_name].fillna(mean_val, inplace=True)
            elif strategy == "forward_fill":
                df[column_name].ffill(inplace=True)
            elif strategy == "backward_fill":
                df[column_name].bfill(inplace=True)
            elif strategy == "interpolate":
                df[column_name].interpolate(inplace=True)
            elif strategy == "drop":
                df.dropna(subset=[column_name], inplace=True)
            else:
                logger.warning(f"Unknown NaN strategy: {strategy}. NaNs will be dropped.")
                df.dropna(subset=[column_name], inplace=True)
    
    @staticmethod
    def replace_inf_nan(df):
        """Infinity اور NaN دونوں کو replace کریں"""
        if not isinstance(df, pd.DataFrame):
            return
        
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # NaN کو صفر سے replace کریں
        df.fillna(0, inplace=True)
        
        logger.debug("✅ Infinity اور NaN replaced")
        return df

