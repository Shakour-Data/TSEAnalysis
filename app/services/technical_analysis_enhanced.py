"""
Technical Analysis Module - Enhanced Version
Integrates with EnhancedAIAssistant for comprehensive analysis
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """
    Enhanced Technical Analyzer with advanced indicators and pattern recognition
    """
    
    @staticmethod
    def prepare_ohlcv_data(data: List[Dict]) -> pd.DataFrame:
        """Prepare OHLCV data from API response"""
        if not data:
            return pd.DataFrame()
        
        try:
            df = pd.DataFrame(data)
            
            # Standardize column names
            column_mapping = {
                'close': 'close',
                'pc': 'close',
                'open': 'open',
                'pf': 'open',
                'high': 'high',
                'pmax': 'high',
                'low': 'low',
                'pmin': 'low',
                'vol': 'volume',
                'tvol': 'volume',
                'volume': 'volume',
                'date': 'date',
                'dtyear': 'date'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Ensure required columns exist
            required = ['close', 'open', 'high', 'low', 'volume', 'date']
            for col in required:
                if col not in df.columns:
                    df[col] = 0
            
            # Convert types
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            
            # Sort by date
            df = df.sort_values('date')
            
            return df.dropna()
            
        except Exception as e:
            logger.error(f"Error preparing OHLCV data: {e}")
            return pd.DataFrame()
    
    # ============ Basic Indicators ============
    
    @staticmethod
    def calculate_sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)  # Neutral for no data
        
        return rsi
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD - Moving Average Convergence Divergence"""
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    @staticmethod
    def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_adx(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average Directional Index"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        plus_di = 100 * (high.diff()) / data['close'].shift(1)
        plus_di = plus_di.rolling(window=period).mean()
        
        minus_di = 100 * (low.diff().abs()) / data['close'].shift(1)
        minus_di = minus_di.rolling(window=period).mean()
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        dx = dx.fillna(0)
        
        adx = dx.rolling(window=period).mean()
        
        return adx
    
    @staticmethod
    def calculate_obv(data: pd.DataFrame) -> pd.Series:
        """On-Balance Volume"""
        close = data['close']
        volume = data['volume']
        
        obv = [0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.append(obv[-1] + volume.iloc[i])
            elif close.iloc[i] < close.iloc[i-1]:
                obv.append(obv[-1] - volume.iloc[i])
            else:
                obv.append(obv[-1])
        
        return pd.Series(obv, index=data.index)
    
    # ============ Pattern Recognition ============
    
    @staticmethod
    def detect_candlestick_patterns(data: pd.DataFrame) -> Dict[str, int]:
        """Detect common candlestick patterns"""
        if len(data) < 5:
            return {}
        
        patterns = {}
        df = data.copy()
        
        # Body and shadow calculations
        df['body'] = abs(df['close'] - df['open'])
        df['upper_shadow'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_shadow'] = df[['close', 'open']].min(axis=1) - df['low']
        
        # Doji
        doji = df[df['body'] <= df['body'].rolling(10).mean() * 0.1]
        patterns['doji'] = len(doji)
        
        # Hammer (bullish reversal)
        hammer = df[(df['lower_shadow'] > df['body'] * 2) & 
                    (df['upper_shadow'] < df['body'] * 0.3) &
                    (df['close'] > df['open'])]
        patterns['hammer'] = len(hammer)
        
        # Shooting star (bearish reversal)
        shooting_star = df[(df['upper_shadow'] > df['body'] * 2) & 
                           (df['lower_shadow'] < df['body'] * 0.3) &
                           (df['close'] < df['open'])]
        patterns['shooting_star'] = len(shooting_star)
        
        # Engulfing patterns
        for i in range(1, len(df)):
            if i < len(df):
                prev = df.iloc[i-1]
                curr = df.iloc[i]
                
                # Bullish engulfing
                if (prev['close'] < prev['open'] and  # Previous bearish
                    curr['close'] > curr['open'] and  # Current bullish
                    curr['open'] < prev['close'] and  # Open below previous close
                    curr['close'] > prev['open']):    # Close above previous open
                    patterns['bullish_engulfing'] = patterns.get('bullish_engulfing', 0) + 1
                
                # Bearish engulfing
                if (prev['close'] > prev['open'] and  # Previous bullish
                    curr['close'] < curr['open'] and  # Current bearish
                    curr['open'] > prev['close'] and  # Open above previous close
                    curr['close'] < prev['open']):    # Close below previous open
                    patterns['bearish_engulfing'] = patterns.get('bearish_engulfing', 0) + 1
        
        return patterns
    
    # ============ Signal Generation ============
    
    @staticmethod
    def generate_signals(data: pd.DataFrame) -> Dict:
        """Generate trading signals based on multiple indicators"""
        if len(data) < 50:
            return {'error': 'Insufficient data'}
        
        signals = {
            'overall': 'NEUTRAL',
            'rsi': 'NEUTRAL',
            'macd': 'NEUTRAL',
            'sma': 'NEUTRAL',
            'bollinger': 'NEUTRAL',
            'confidence': 0.0
        }
        
        try:
            close = data['close']
            
            # RSI signals
            rsi = TechnicalAnalyzer.calculate_rsi(close)
            current_rsi = rsi.iloc[-1]
            
            if current_rsi > 70:
                signals['rsi'] = 'BEARISH'
            elif current_rsi < 30:
                signals['rsi'] = 'BULLISH'
            else:
                signals['rsi'] = 'NEUTRAL'
            
            # MACD signals
            macd, signal, hist = TechnicalAnalyzer.calculate_macd(close)
            current_hist = hist.iloc[-1]
            prev_hist = hist.iloc[-2]
            
            if current_hist > 0 and prev_hist <= 0:
                signals['macd'] = 'BULLISH'  # Crossover
            elif current_hist < 0 and prev_hist >= 0:
                signals['macd'] = 'BEARISH'  # Crossover down
            elif current_hist > 0:
                signals['macd'] = 'BULLISH'
            elif current_hist < 0:
                signals['macd'] = 'BEARISH'
            
            # SMA signals
            sma_20 = TechnicalAnalyzer.calculate_sma(close, 20).iloc[-1]
            sma_50 = TechnicalAnalyzer.calculate_sma(close, 50).iloc[-1]
            
            if close.iloc[-1] > sma_20 > sma_50:
                signals['sma'] = 'BULLISH'
            elif close.iloc[-1] < sma_20 < sma_50:
                signals['sma'] = 'BEARISH'
            else:
                signals['sma'] = 'NEUTRAL'
            
            # Bollinger Bands signals
            upper, middle, lower = TechnicalAnalyzer.calculate_bollinger_bands(close)
            current_price = close.iloc[-1]
            
            if current_price > upper.iloc[-1]:
                signals['bollinger'] = 'BEARISH'  # Overbought
            elif current_price < lower.iloc[-1]:
                signals['bollinger'] = 'BULLISH'  # Oversold
            else:
                signals['bollinger'] = 'NEUTRAL'
            
            # Overall signal
            bullish_count = sum(1 for v in [signals['rsi'], signals['macd'], 
                                              signals['sma'], signals['bollinger']] 
                               if v == 'BULLISH')
            bearish_count = sum(1 for v in [signals['rsi'], signals['macd'], 
                                              signals['sma'], signals['bollinger']] 
                                if v == 'BEARISH')
            
            if bullish_count >= 3:
                signals['overall'] = 'BULLISH'
                signals['confidence'] = 0.75
            elif bearish_count >= 3:
                signals['overall'] = 'BEARISH'
                signals['confidence'] = 0.75
            elif bullish_count > bearish_count:
                signals['overall'] = 'BULLISH'
                signals['confidence'] = 0.6
            elif bearish_count > bullish_count:
                signals['overall'] = 'BEARISH'
                signals['confidence'] = 0.6
            else:
                signals['overall'] = 'NEUTRAL'
                signals['confidence'] = 0.5
                
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
        
        return signals
    
    # ============ Support/Resistance ============
    
    @staticmethod
    def find_support_resistance(data: pd.DataFrame, window: int = 20) -> Dict:
        """Find support and resistance levels"""
        if len(data) < window:
            return {'supports': [], 'resistances': []}
        
        try:
            close = data['close']
            highs = data['high']
            lows = data['low']
            
            # Find local maxima and minima
            supports = []
            resistances = []
            
            for i in range(window, len(data) - window):
                # Resistance (local maximum)
                if highs.iloc[i] >= highs.iloc[i-window:i].max() and \
                   highs.iloc[i] >= highs.iloc[i:i+window].max():
                    resistances.append(highs.iloc[i])
                
                # Support (local minimum)
                if lows.iloc[i] <= lows.iloc[i-window:i].min() and \
                   lows.iloc[i] <= lows.iloc[i:i+window].min():
                    supports.append(lows.iloc[i])
            
            # Cluster nearby levels
            def cluster_levels(levels, threshold: float = 0.02):
                if not levels:
                    return []
                levels = sorted(levels, reverse=True)
                clusters = [[levels[0]]]
                
                for level in levels[1:]:
                    if abs(level - clusters[-1][0]) / clusters[-1][0] < threshold:
                        clusters[-1].append(level)
                    else:
                        clusters.append([level])
                
                return [sum(c) / len(c) for c in clusters]
            
            supports = cluster_levels(supports)[:5]
            resistances = cluster_levels(resistances)[:5]
            
            return {
                'supports': sorted(supports)[:5],
                'resistances': sorted(resistances, reverse=True)[:5]
            }
            
        except Exception as e:
            logger.error(f"Support/Resistance error: {e}")
            return {'supports': [], 'resistances': []}
    
    # ============ Strategy Matrix ============
    
    @staticmethod
    def generate_strategy_matrix(current_price: float, 
                                  supports: List[float], 
                                  resistances: List[float]) -> List[Dict]:
        """Generate trading strategy matrix with risk/reward"""
        
        if not supports or not resistances:
            supports = [current_price * 0.95, current_price * 0.90, current_price * 0.85]
            resistances = [current_price * 1.05, current_price * 1.10, current_price * 1.15]
        
        strategies = []
        
        # Aggressive Long
        strategies.append({
            'پروفایل سرمایه‌گذار': 'پرخطر',
            'تیپ شخصیتی': 'ریسک‌پذیر',
            'افق زمانی': 'کوتاه‌مدت',
            'نقطه ورود': current_price,
            'حد سود (TP)': resistances[0] if resistances else current_price * 1.05,
            'حد ضرر (SL)': supports[-1] if supports else current_price * 0.95,
            'R/R': round((resistances[0] - current_price) / (current_price - supports[-1]), 2) if supports and resistances else 1.0
        })
        
        # Moderate Long
        if len(resistances) > 1:
            strategies.append({
                'پروفایل سرمایه‌گذار': 'متوسط',
                'تیپ شخصیتی': 'محافظه‌کار',
                'افق زمانی': 'میان‌مدت',
                'نقطه ورود': supports[0] if supports else current_price * 0.98,
                'حد سود (TP)': resistances[1] if len(resistances) > 1 else resistances[0],
                'حد ضرر (SL)': supports[-1] if len(supports) > 1 else supports[0],
                'R/R': 1.5
            })
        
        # Conservative Long
        if len(supports) > 1:
            strategies.append({
                'پروفایل سرمایه‌گذار': 'محافظه‌کار',
                'تیپ شخصیتی': 'بسیار محتاط',
                'افق زمانی': 'بلندمدت',
                'نقطه ورود': supports[1] if len(supports) > 1 else supports[0],
                'حد سود (TP)': resistances[0] if resistances else current_price * 1.1,
                'حد ضرر (SL)': supports[-1] if len(supports) > 1 else supports[0] * 0.95,
                'R/R': 2.0
            })
        
        return strategies
    
    # ============ Chart Generation ============
    
    @staticmethod
    def generate_chart_image(data: pd.DataFrame, symbol: str, timeframe: str = 'daily') -> Optional[bytes]:
        """Generate chart image (placeholder - requires matplotlib)"""
        # This is a placeholder - actual implementation would use matplotlib
        logger.info(f"Chart generation requested for {symbol} ({timeframe})")
        return None
