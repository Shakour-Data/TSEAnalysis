import pandas as pd
import numpy as np
import ta  # type: ignore[attr-defined]
import mplfinance as mpf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import jdatetime
import io
import base64
import logging
from app.utils.nan_handler import NaNHandler

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """
    تحلیل تکنیکی - شامل شناسایی و تصفیه داده‌های پرت
    """

    @staticmethod
    def detect_outliers(data, column='close', threshold=3.0):
        """
        شناسایی داده‌های پرت با استفاده از Z-score
        - threshold=3.0: 99.7% از داده‌ها درون range
        - threshold=2.5: 98.8% از داده‌ها درون range
        """
        if not data or not isinstance(data, list) or len(data) < 5:
            return data, []
        
        try:
            df = pd.DataFrame(data)
            
            if column not in df.columns:
                logger.warning(f"Column {column} not found in data")
                return data, []
            
            # Convert to numeric
            df[column] = pd.to_numeric(df[column], errors='coerce')
            
            # Remove NaN
            valid_df = df[df[column].notna()].copy()
            
            if len(valid_df) < 5:
                return data, []
            
            # Calculate Z-score
            mean = valid_df[column].mean()
            std = valid_df[column].std()
            
            if std == 0:
                return data, []
            
            z_scores = np.abs((valid_df[column] - mean) / std)
            
            # Find outliers
            outlier_mask = np.array(z_scores) > threshold
            outlier_indices = valid_df[outlier_mask].index.tolist()
            
            if outlier_indices:
                logger.warning(f"تشخیص {len(outlier_indices)} داده پرت در {column}")
                
                # Remove outliers
                cleaned_data = [item for i, item in enumerate(data) if i not in outlier_indices]
                outlier_data = [data[i] for i in outlier_indices]
                
                return cleaned_data, outlier_data
            
            return data, []
        
        except Exception as e:
            logger.error(f"Outlier detection failed: {e}")
            return data, []

    @staticmethod
    def detect_divergence(df, indicator_col='RSI', window=5):
        """
        Detects regular divergences between Price and an Indicator.
        """
        if len(df) < 50: return "No Divergence"
        
        # Latest peaks/troughs
        recent_df = df.tail(50).copy()
        
        # Find Price Lows and Indicator Highs
        # 1. Bullish Divergence (Price making lower low, RSI making higher low)
        try:
            p_min1_idx = recent_df['low'].tail(20).idxmin()
            p_min2_idx = recent_df['low'].iloc[:-20].tail(20).idxmin()
            
            if recent_df.loc[p_min1_idx, 'low'] < recent_df.loc[p_min2_idx, 'low']:
                if recent_df.loc[p_min1_idx, indicator_col] > recent_df.loc[p_min2_idx, indicator_col]:
                    return "Bullish Divergence (Positive)"
            
            # 2. Bearish Divergence (Price making higher high, RSI making lower high)
            p_max1_idx = recent_df['high'].tail(20).idxmax()
            p_max2_idx = recent_df['high'].iloc[:-20].tail(20).idxmax()
            
            if recent_df.loc[p_max1_idx, 'high'] > recent_df.loc[p_max2_idx, 'high']:
                if recent_df.loc[p_max1_idx, indicator_col] < recent_df.loc[p_max2_idx, indicator_col]:
                    return "Bearish Divergence (Negative)"
        except (KeyError, IndexError, ValueError) as e:
            logger.debug(f"Divergence detection failed: {e}")
            pass
            
        return "Normal"

    @staticmethod
    def get_fibonacci_levels(df):
        """
        Calculates Fibonacci retracement levels for the current trend.
        """
        if df.empty: return {}
        recent = df.tail(120) # Last 6 months approx
        price_min = recent['low'].min()
        price_max = recent['high'].max()
        diff = price_max - price_min
        
        return {
            '0%': price_max,
            '23.6%': price_max - 0.236 * diff,
            '38.2%': price_max - 0.382 * diff,
            '50.0%': price_max - 0.5 * diff,
            '61.8%': price_max - 0.618 * diff,
            '100%': price_min
        }

    @staticmethod
    def calculate_risk_reward(current_price, supports, resistances):
        """
        خطرہ/انعام کا تناسب محفوظ طریقے سے
        """
        if not supports or not resistances:
            return None
            
        try:
            # Best support for SL (nearest below), Best resistance for TP (nearest above)
            sl = supports[0]['value'] * 0.98 # 2% below support
            tp = resistances[0]['value'] * 1.02 # 2% above resistance
            
            # Zero/negative check
            if sl >= current_price or tp <= current_price:
                return None
            
            risk = current_price - sl
            reward = tp - current_price
            
            # Risk validation
            if risk <= 0:
                logger.warning(f"Invalid risk calculation: current={current_price}, sl={sl}")
                return None
            
            # Division by zero protection
            rr_ratio = round(reward / risk, 2) if risk != 0 else 0
            
            return {
                'entry': round(current_price, 0),
                'stop_loss': round(sl, 0),
                'take_profit': round(tp, 0),
                'rr_ratio': rr_ratio,
                'status': "Attractive" if rr_ratio > 2 else "Fair" if rr_ratio > 1.5 else "Risky"
            }
        except (ValueError, ZeroDivisionError, TypeError) as e:
            logger.error(f"Risk/Reward calculation failed: {e}")
            return None

    @staticmethod
    def prepare_ohlcv_data(data):
        """
        معیاری OHLCV format - شامل outlier detection اور NaN handling
        - صرف valid numeric data
        - پرت‌ها شناسایی و حذف شود
        - NaN values کو handle کریں
        """
        if not data or not isinstance(data, list):
            return data
        
        # Step 1: Outlier detection
        cleaned_data, outliers = TechnicalAnalyzer.detect_outliers(data, column='pc', threshold=2.5)
        
        if outliers:
            logger.info(f"✅ {len(outliers)} داده پرت حذف شد")
        
        data = cleaned_data
        standardized = []
        nan_replaced = 0
        
        for item in data:
            if not isinstance(item, dict):
                continue
            
            try:
                # صرف close پر کام ہو (ضروری فیلڈ)
                close = item.get('pc') or item.get('close')
                if close is None or NaNHandler.has_nan(close):
                    continue
                
                # Convert to float - error check
                try:
                    close_val = float(close)
                    if NaNHandler.has_nan(close_val):
                        continue
                except (ValueError, TypeError):
                    logger.debug(f"Invalid close price: {close}")
                    continue
                
                # Open, High, Low
                try:
                    open_raw = item.get('pf') or item.get('open') or close_val
                    high_raw = item.get('pmax') or item.get('high') or close_val
                    low_raw = item.get('pmin') or item.get('low') or close_val
                    volume_raw = item.get('tvol') or item.get('volume') or 0
                    
                    # NaN check اور handling
                    if NaNHandler.has_nan(open_raw):
                        open_val = close_val
                        nan_replaced += 1
                    else:
                        open_val = float(open_raw)
                    
                    if NaNHandler.has_nan(high_raw):
                        high_val = close_val
                        nan_replaced += 1
                    else:
                        high_val = float(high_raw)
                    
                    if NaNHandler.has_nan(low_raw):
                        low_val = close_val
                        nan_replaced += 1
                    else:
                        low_val = float(low_raw)
                    
                    if NaNHandler.has_nan(volume_raw):
                        volume_val = 0
                        nan_replaced += 1
                    else:
                        volume_val = int(volume_raw)
                
                except (ValueError, TypeError) as e:
                    logger.debug(f"Invalid OHLCV data: {e}")
                    continue
                
                # Validation: High >= Low
                if high_val < low_val:
                    high_val, low_val = low_val, high_val
                
                # Close validation
                if close_val > high_val:
                    high_val = close_val
                if close_val < low_val:
                    low_val = close_val
                
                # Build standardized item
                new_item = item.copy()
                new_item['close'] = close_val
                new_item['open'] = open_val
                new_item['high'] = high_val
                new_item['low'] = low_val
                new_item['volume'] = volume_val
                
                standardized.append(new_item)
            
            except Exception as e:
                logger.debug(f"OHLCV preparation error: {e}")
                continue
        
        if nan_replaced > 0:
            logger.info(f"✅ {nan_replaced} NaN values replace کیے گئے")
        
        return standardized

    @staticmethod
    def resample_to_weekly(data):
        if not data or not isinstance(data, list) or len(data) < 5:
            return data
        
        df = pd.DataFrame(data)
        date_col = next((c for c in df.columns if c in ['date', 'time']), None)
        if not date_col:
            return data
            
        try:
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.sort_values(date_col)
            df.set_index(date_col, inplace=True)
            
            logic = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            for col in df.columns:
                if col not in logic:
                    logic[col] = 'first'
                    
            weekly_df = df.resample('W-WED').apply(logic)  # type: ignore[arg-type]
            weekly_df = weekly_df.dropna(subset=['close'])
            weekly_df.reset_index(inplace=True)
            weekly_df['date'] = weekly_df[date_col].dt.strftime('%Y-%m-%d')  # type: ignore[attr-defined]
            weekly_df = weekly_df.sort_values('date', ascending=False)
            
            return weekly_df.to_dict('records')
        except Exception as e:
            logger.error(f"Resampling Error: {e}")
            return data

    @staticmethod
    def get_support_resistance(df, window=5):
        if len(df) < window * 2:
            return [], []
        
        df = df.copy()
        df['is_min'] = df['low'] == df['low'].rolling(window=window*2+1, center=True).min()
        df['is_max'] = df['high'] == df['high'].rolling(window=window*2+1, center=True).max()
        
        minima = df[df['is_min']]['low'].tolist()
        maxima = df[df['is_max']]['high'].tolist()
        
        def cluster_levels(levels, current_price, is_resistance=True):
            if not levels: 
                # Provide fallback levels if none found
                if is_resistance:
                    return [{'value': round(current_price * (1 + 0.02 * i)), 'hits': 1, 'strength': 1.0} for i in range(1, 6)]
                else:
                    return [{'value': round(current_price * (1 - 0.02 * i)), 'hits': 1, 'strength': 1.0} for i in range(1, 6)]

            clusters = []
            for l in sorted(levels):
                found = False
                for c in clusters:
                    if abs(c['value'] - l) / l < 0.03: # Increased cluster tolerance
                        c['hits'] += 1
                        c['value'] = (c['value'] * (c['hits']-1) + l) / c['hits']
                        found = True
                        break
                if not found:
                    clusters.append({'value': l, 'hits': 1})
            
            for c in clusters:
                if c['value'] > 1000:
                    c['value'] = round(c['value'], -1)
                elif c['value'] > 100:
                    c['value'] = round(c['value'], 0)
                else:
                    c['value'] = round(c['value'], 2)
                    
                dist = abs(c['value'] - current_price) / current_price
                c['strength'] = round(c['hits'] * (1 / (dist + 0.05)), 1)
                
            if is_resistance:
                valid = [c for c in clusters if c['value'] > current_price]
                # If less than 5, add extrapolated ones
                while len(valid) < 5:
                    last_val = valid[-1]['value'] if valid else current_price
                    valid.append({'value': round(last_val * 1.03), 'hits': 0, 'strength': 0.5})
                return sorted(valid, key=lambda x: x['value'])[:5]
            else:
                valid = [c for c in clusters if c['value'] < current_price]
                # If less than 5, add extrapolated ones
                while len(valid) < 5:
                    last_val = valid[-1]['value'] if valid else current_price
                    valid.append({'value': round(last_val * 0.97), 'hits': 0, 'strength': 0.5})
                return sorted(valid, key=lambda x: x['value'], reverse=True)[:5]

        current_price = df['close'].iloc[-1]
        supports = cluster_levels(minima, current_price, False)
        resistances = cluster_levels(maxima, current_price, True)
        
        return supports, resistances

    @staticmethod
    def prioritize_indicators(df):
        if df.empty or len(df) < 50:
            return []

        history = df.sort_values('date').copy()
        history['future_return'] = (history['close'].shift(-5) - history['close']) / history['close']
        
        indicators = [
            {'name': 'RSI', 'type': 'Momentum', 'desc': 'سیگنال‌های نوسانی و اشباع خرید/فروش'},
            {'name': 'MACD', 'type': 'Trend', 'desc': 'تایید روند و واگرایی‌ها'},
            {'name': 'SMA', 'type': 'Trend', 'desc': 'تقاطع میانگین‌های متحرک'},
            {'name': 'Bollinger', 'type': 'Volatility', 'desc': 'نواحی حمایتی و مقاومتی پویا'},
            {'name': 'Stoch', 'type': 'Momentum', 'desc': 'سرعت تغییرات قیمت و بازگشت‌ها'}
        ]
        
        rankings = []
        for ind in indicators:
            accuracy = 0
            signals_count = 0
            avg_profit = 0
            
            if ind['name'] == 'RSI':
                signals = history[(history['RSI'] < 30) | (history['RSI'] > 70)]
                if not signals.empty:
                    success = signals.apply(lambda r: (r['future_return'] > 0 if r['RSI'] < 30 else r['future_return'] < 0), axis=1)
                    accuracy = success.mean()
                    signals_count = len(signals)
                    avg_profit = signals['future_return'].abs().mean()
            
            elif ind['name'] == 'MACD':
                history['macd_cross'] = (history['MACD'] > history['MACD_Sig']).astype(int).diff()
                signals = history[history['macd_cross'] != 0]
                if not signals.empty:
                    success = signals.apply(lambda r: (r['future_return'] > 0 if r['macd_cross'] > 0 else r['future_return'] < 0), axis=1)
                    accuracy = success.mean()
                    signals_count = len(signals)
                    avg_profit = signals['future_return'].abs().mean()

            elif ind['name'] == 'SMA':
                if 'SMA20' in history.columns and 'SMA50' in history.columns:
                    history['sma_cross'] = (history['SMA20'] > history['SMA50']).astype(int).diff()
                    signals = history[history['sma_cross'].notnull() & (history['sma_cross'] != 0)]
                    if not signals.empty:
                        success = signals.apply(lambda r: (r['future_return'] > 0 if r['sma_cross'] > 0 else r['future_return'] < 0), axis=1)
                        accuracy = success.mean()
                        signals_count = len(signals)
                        avg_profit = signals['future_return'].abs().mean()

            elif ind['name'] == 'Bollinger':
                signals = history[(history['close'] < history['BBL']) | (history['close'] > history['BBU'])]
                if not signals.empty:
                    success = signals.apply(lambda r: (r['future_return'] > 0 if r['close'] < r['BBL'] else r['future_return'] < 0), axis=1)
                    accuracy = success.mean()
                    signals_count = len(signals)
                    avg_profit = signals['future_return'].abs().mean()

            elif ind['name'] == 'Stoch':
                signals = history[(history['STOCHk'] < 20) | (history['STOCHk'] > 80)]
                if not signals.empty:
                    success = signals.apply(lambda r: (r['future_return'] > 0 if r['STOCHk'] < 20 else r['future_return'] < 0), axis=1)
                    accuracy = success.mean()
                    signals_count = len(signals)
                    avg_profit = signals['future_return'].abs().mean()

            score = (accuracy * 0.6) + (avg_profit * 0.3) + (min(signals_count / 10, 1) * 0.1)
            rankings.append({
                'name': ind['name'],
                'type': ind['type'],
                'description': ind['desc'],
                'accuracy': round(accuracy * 100, 1),
                'score': round(score, 3),
                'signals': signals_count
            })

        rankings = sorted(rankings, key=lambda x: x['score'], reverse=True)
        return rankings

    @classmethod
    def calculate_technical_analysis(cls, data, index_data=None):
        if not data or not isinstance(data, list) or len(data) < 10:
            return data

        df = pd.DataFrame(data)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        if 'date' in df.columns:
            df = df.sort_values('date')

        try:
            # Trend & Momentum
            if len(df) >= 20:
                df['SMA20'] = ta.trend.sma_indicator(df['close'], window=20)  # type: ignore[attr-defined]
                df['BBU'] = ta.volatility.bollinger_hband(df['close'], window=20)  # type: ignore[attr-defined]
                df['BBL'] = ta.volatility.bollinger_lband(df['close'], window=20)  # type: ignore[attr-defined]
            else:
                df['SMA20'] = df['close'].rolling(window=min(len(df), 5)).mean()
                df['BBU'] = None
                df['BBL'] = None

            if len(df) >= 50:
                df['SMA50'] = ta.trend.sma_indicator(df['close'], window=50)  # type: ignore[attr-defined]
            else:
                df['SMA50'] = None

            if len(df) >= 26:
                df['MACD'] = ta.trend.macd(df['close'])  # type: ignore[attr-defined]
                df['MACD_Sig'] = ta.trend.macd_signal(df['close'])  # type: ignore[attr-defined]
            else:
                df['MACD'] = None
                df['MACD_Sig'] = None

            if len(df) >= 14:
                df['RSI'] = ta.momentum.rsi(df['close'], window=14)  # type: ignore[attr-defined]
                df['ADX'] = ta.trend.adx(df['high'], df['low'], df['close'])  # type: ignore[attr-defined]
                df['ATR'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)  # type: ignore[attr-defined]
                df['STOCHk'] = ta.momentum.stoch(df['high'], df['low'], df['close'], window=14, smooth_window=3)  # type: ignore[attr-defined]
            else:
                df['RSI'] = None
                df['ADX'] = None
                df['ATR'] = None
                df['STOCHk'] = None

            # Ichimoku
            if len(df) >= 52:
                df['Ichimoku_A'] = ta.trend.ichimoku_a(df['high'], df['low'])  # type: ignore[attr-defined]
                df['Ichimoku_B'] = ta.trend.ichimoku_b(df['high'], df['low'])  # type: ignore[attr-defined]
                df['Ichimoku_Base'] = ta.trend.ichimoku_base_line(df['high'], df['low'])  # type: ignore[attr-defined]
                df['Ichimoku_Conv'] = ta.trend.ichimoku_conversion_line(df['high'], df['low'])  # type: ignore[attr-defined]
            else:
                df['Ichimoku_A'] = None
                df['Ichimoku_B'] = None
                df['Ichimoku_Base'] = None
                df['Ichimoku_Conv'] = None

            # Beta calculation if index_data is provided
            beta_val = None
            if index_data and isinstance(index_data, list) and len(index_data) > 0:
                try:
                    idf = pd.DataFrame(index_data)
                    # Normalize columns for index dataframe
                    if 'pc' in idf.columns and 'close' not in idf.columns: idf['close'] = idf['pc']
                    if 'time' in idf.columns and 'date' not in idf.columns: idf['date'] = idf['time']
                    
                    if 'close' in idf.columns and 'date' in idf.columns:
                        idf['close'] = pd.to_numeric(idf['close'], errors='coerce')
                        idf = idf.sort_values('date')
                        # Merge on date
                        merged = pd.merge(df[['date', 'close']], idf[['date', 'close']], on='date', suffixes=('_s', '_i'))
                        if len(merged) > 30:
                            merged['ret_s'] = merged['close_s'].pct_change()
                            merged['ret_i'] = merged['close_i'].pct_change()
                            merged = merged.dropna()
                            cov = merged['ret_s'].cov(merged['ret_i'])
                            var = merged['ret_i'].var()
                            if var != 0 and isinstance(var, (int, float)) and isinstance(cov, (int, float)):
                                beta_val = round(float(cov) / float(var), 2)
                except Exception as e:
                    logger.debug(f"Beta calculation error: {e}")
                    pass

            for col in df.select_dtypes(include=[np.number]).columns:
                if any(x in col for x in ['MACD', 'RSI', 'ADX', 'ATR', 'Ichimoku']):
                    df[col] = df[col].round(2)
                else:
                    avg_val = df[col].mean()
                    if avg_val > 1000:
                        df[col] = df[col].round(0)
                    elif avg_val > 100:
                        df[col] = df[col].round(1)
                    else:
                        df[col] = df[col].round(2)
            
            def get_signals(row):
                sigs = []
                try:
                    if row.get('SMA20') and row.get('SMA50'):
                        if row['SMA20'] > row['SMA50']: sigs.append('Bullish (SMA)')
                        elif row['SMA20'] < row['SMA50']: sigs.append('Bearish (SMA)')
                    
                    if row.get('RSI'):
                        if row['RSI'] < 30: sigs.append('Oversold')
                        elif row['RSI'] > 70: sigs.append('Overbought')
                    
                    if row.get('MACD') and row.get('MACD_Sig'):
                        if row['MACD'] > row['MACD_Sig']: sigs.append('MACD Bullish')
                    
                    if row.get('Ichimoku_Conv') and row.get('Ichimoku_Base'):
                        if row['Ichimoku_Conv'] > row['Ichimoku_Base']: sigs.append('Ichimoku Bullish Cross')
                except:
                    pass
                return ", ".join(sigs) if sigs else 'Neutral'

            df['Signal'] = df.apply(get_signals, axis=1)
            
            # Patterns
            df['Pattern'] = None
            body = (df['close'] - df['open']).abs()
            upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
            lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
            df.loc[body <= (df['high'] - df['low']) * 0.1, 'Pattern'] = 'Doji'
            df.loc[(lower_shadow >= 2 * body) & (upper_shadow <= 0.1 * body) & (body > 0), 'Pattern'] = 'Hammer'

            # S/R and Advanced
            supports, resistances = cls.get_support_resistance(df)
            fib_levels = cls.get_fibonacci_levels(df)
            divergence = cls.detect_divergence(df)
            risk_reward = cls.calculate_risk_reward(df['close'].iloc[-1], supports, resistances)
            
            if 'date' in df.columns:
                cols = ['date', 'Signal', 'Pattern'] + [c for c in df.columns if c not in ['date', 'Signal', 'Pattern']]
                df = df[cols]
            
            df = df.replace({np.nan: None})
            if 'date' in df.columns:
                df = df.sort_values('date', ascending=False)
            
            results = df.to_dict('records')
            if results:
                results[0]['supports'] = supports
                results[0]['resistances'] = resistances
                results[0]['fibonacci'] = fib_levels
                results[0]['divergence'] = divergence
                results[0]['risk_reward'] = risk_reward
                results[0]['beta'] = beta_val
                try:
                    indicator_rankings = cls.prioritize_indicators(df)
                    results[0]['recommended_indicators'] = indicator_rankings
                except:
                    pass
                
                # Generate chart image
                try:
                    chart_buffer = cls.generate_chart_image(df)
                    if chart_buffer:
                        results[0]['chart_image'] = base64.b64encode(chart_buffer.getvalue()).decode('utf-8')
                except Exception as e:
                    logger.error(f"Chart generation failed: {e}")
                
            return results
        except Exception as e:
            logger.error(f"Error: {e}")
            return data

    @staticmethod
    def generate_strategy_matrix(current_price, supports, resistances):
        """
        Generates the specialized 6-profile strategy matrix correctly mapped to the 7-slide protocol.
        """
        if not current_price or not supports or not resistances:
            return []

        strategies = []
        
        # Helper to get numeric value from supports/resistances which can be dicts or floats
        def _get_val(lvl_list, index, fallback_mult):
            if not lvl_list or len(lvl_list) <= index:
                return current_price * fallback_mult
            item = lvl_list[index]
            if isinstance(item, dict):
                return item.get('value', current_price * fallback_mult)
            try:
                return float(item)
            except (ValueError, TypeError):
                return current_price * fallback_mult

        s1 = _get_val(supports, 0, 0.95)
        s2 = _get_val(supports, 1, 0.90)
        r1 = _get_val(resistances, 0, 1.05)
        r2 = _get_val(resistances, 1, 1.10)
        
        # 6 Profiles requested in Slide 5
        archetypes = [
            ("سرمایه‌گذار محافظه‌کار", "ریسک‌گریز", "بلند مدت", s2, r1, s2 * 0.95, "ورود در لایه‌های حمایتی معتبر و خروج در اولین مقاومت سنگین"),
            ("سرمایه‌گذار متعادل", "ریسک‌پذیر متوسط", "میان مدت", s1, r2, s2, "تعامل با نوسانات میانی و حفظ بخشی از سود در میانه راه"),
            ("معامله‌گر تهاجمی", "ریسک‌پذیر بالا", "کوتاه مدت", current_price, r1, current_price * 0.97, "ورود با تریگر حجم و خروج سریع در تارگت‌های نوسانی"),
            ("نوسان‌گیر روزانه (Scalper)", "فوق تهاجمی", "روزانه", current_price, current_price * 1.02, current_price * 0.99, "بهره‌گیری از نوسانات ۱ تا ۳ درصدی روزانه با استاپ بسیار نزدیک"),
            ("سبدگردان (Portfolio)", "استراتژیک", "بلند مدت", f"محدوده {s1}-{s2}", r2, s2 * 0.9, "چینش پله‌ای سبد بر اساس ارزش ذاتی و میانگین کم کردن در حمایت‌ها"),
            ("هج فاند (Hedge Fund)", "پیچیده", "متغیر", current_price, r2, s2, "استفاده از معاملات دوطرفه و پوشش ریسک بر اساس همبستگی با شاخص")
        ]

        for profile, personality, horizon, entry, target, sl, desc in archetypes:
            risk = 0
            reward = 0
            rr_val = "1:2.0"
            try:
                # Basic RR calculation for display if entry is numeric
                if isinstance(entry, (int, float)):
                    risk = abs(entry - sl)
                    reward = abs(target - entry)
                    if risk > 0: rr_val = f"1:{round(reward/risk, 1)}"
            except: pass

            strategies.append({
                "پروفایل سرمایه‌گذار": profile,
                "تیپ شخصیتی": personality,
                "افق زمانی": horizon,
                "نقطه ورود": entry,
                "حد ضرر (SL)": sl,
                "حد سود (TP)": target,
                "R/R": rr_val,
                "توضیحات استراتژی": desc
            })
        return strategies

    @staticmethod
    def generate_chart_image(df, symbol=None, timeframe='daily'):
        """Generate candlestick chart with indicators as base64 image."""
        if df is None or (hasattr(df, 'empty') and df.empty) or len(df) < 10:
            return None
        
        try:
            # Prepare data for mplfinance
            plot_df = df.copy()
            if 'date' in plot_df.columns:
                plot_df['date'] = pd.to_datetime(plot_df['date'], format='%Y-%m-%d')
                plot_df.set_index('date', inplace=True)
            
            # Create subplots
            fig = mpf.figure(figsize=(12, 8), style='charles')
            ax1 = fig.add_subplot(211)
            ax2 = fig.add_subplot(212)
            
            # Candlestick chart
            mpf.plot(plot_df, type='candle', volume=ax2, ax=ax1, show_nontrading=False)
            
            # Add indicators if available
            if 'SMA20' in plot_df.columns and plot_df['SMA20'].notna().any():
                ax1.plot(plot_df.index, plot_df['SMA20'], label='SMA20', color='blue')
            if 'BBU' in plot_df.columns and plot_df['BBU'].notna().any():
                ax1.plot(plot_df.index, plot_df['BBU'], label='BB Upper', color='red', linestyle='--')
            if 'BBL' in plot_df.columns and plot_df['BBL'].notna().any():
                ax1.plot(plot_df.index, plot_df['BBL'], label='BB Lower', color='green', linestyle='--')
            
            ax1.legend()
            
            # Save to buffer
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight')
            plt.close(fig)
            buffer.seek(0)
            return buffer
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            return None
