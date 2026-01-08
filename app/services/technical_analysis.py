import pandas as pd
import numpy as np
import ta
import mplfinance as mpf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import jdatetime
import io
import base64
import random
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """
    Encapsulates all technical analysis logic, including indicators, 
    support/resistance levels, and chart generation.
    """

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
        except:
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
        Calculates suggested Entry, StopLoss and TakeProfit with R/R ratio.
        """
        if not supports or not resistances:
            return None
            
        # Best support for SL (nearest below), Best resistance for TP (nearest above)
        sl = supports[0]['value'] * 0.98 # 2% below support
        tp = resistances[0]['value'] * 0.98 # Just before resistance
        
        risk = current_price - sl
        reward = tp - current_price
        
        if risk <= 0: return None
        
        rr_ratio = round(reward / risk, 2)
        return {
            'entry': current_price,
            'stop_loss': round(sl, 0),
            'take_profit': round(tp, 0),
            'rr_ratio': rr_ratio,
            'status': "Attractive" if rr_ratio > 2 else "Fair" if rr_ratio > 1.5 else "Risky"
        }

    @staticmethod
    def prepare_ohlcv_data(data):
        if not data or not isinstance(data, list):
            return data
        
        standardized = []
        for item in data:
            # Map BrsApi historical keys (pc, pf, pmax, pmin, tvol, index) to standard OHLCV
            # 'pc' = Previous Close/Close, 'pf' = First/Open, 'index' = Index value
            close = item.get('pc') or item.get('close') or item.get('index') or item.get('value')
            open_p = item.get('pf') or item.get('open') or close
            high = item.get('pmax') or item.get('high') or close
            low = item.get('pmin') or item.get('low') or close
            volume = item.get('tvol') or item.get('volume') or 0
            
            if close is not None:
                new_item = item.copy()
                p_close = float(close)
                rounding = 0 if p_close > 1000 else (1 if p_close > 100 else 2)
                
                new_item['close'] = round(p_close, rounding)
                new_item['open'] = round(float(open_p), rounding)
                new_item['high'] = round(float(high), rounding)
                new_item['low'] = round(float(low), rounding)
                new_item['volume'] = float(volume)
                standardized.append(new_item)
                
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
                    
            weekly_df = df.resample('W-WED').apply(logic)
            weekly_df = weekly_df.dropna(subset=['close'])
            weekly_df.reset_index(inplace=True)
            weekly_df['date'] = weekly_df[date_col].dt.strftime('%Y-%m-%d')
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
            if not levels: return []
            clusters = []
            for l in sorted(levels):
                found = False
                for c in clusters:
                    if abs(c['value'] - l) / l < 0.02:
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
                return sorted(valid, key=lambda x: x['value'])[:5]
            else:
                valid = [c for c in clusters if c['value'] < current_price]
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
                df['SMA20'] = ta.trend.sma_indicator(df['close'], window=20)
                df['BBU'] = ta.volatility.bollinger_hband(df['close'], window=20)
                df['BBL'] = ta.volatility.bollinger_lband(df['close'], window=20)
            else:
                df['SMA20'] = df['close'].rolling(window=min(len(df), 5)).mean()
                df['BBU'] = None
                df['BBL'] = None

            if len(df) >= 50:
                df['SMA50'] = ta.trend.sma_indicator(df['close'], window=50)
            else:
                df['SMA50'] = None

            if len(df) >= 26:
                df['MACD'] = ta.trend.macd(df['close'])
                df['MACD_Sig'] = ta.trend.macd_signal(df['close'])
            else:
                df['MACD'] = None
                df['MACD_Sig'] = None

            if len(df) >= 14:
                df['RSI'] = ta.momentum.rsi(df['close'], window=14)
                df['ADX'] = ta.trend.adx(df['high'], df['low'], df['close'])
                df['ATR'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
            else:
                df['RSI'] = None
                df['ADX'] = None
                df['ATR'] = None

            # Ichimoku
            if len(df) >= 52:
                df['Ichimoku_A'] = ta.trend.ichimoku_a(df['high'], df['low'])
                df['Ichimoku_B'] = ta.trend.ichimoku_b(df['high'], df['low'])
                df['Ichimoku_Base'] = ta.trend.ichimoku_base_line(df['high'], df['low'])
                df['Ichimoku_Conv'] = ta.trend.ichimoku_conversion_line(df['high'], df['low'])
            else:
                df['Ichimoku_A'] = None
                df['Ichimoku_B'] = None
                df['Ichimoku_Base'] = None
                df['Ichimoku_Conv'] = None

            # Beta calculation if index_data is provided
            beta_val = None
            if index_data and isinstance(index_data, list):
                try:
                    idf = pd.DataFrame(index_data)
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
                        beta_val = round(cov / var, 2)
                except:
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
                if row['SMA20'] > row['SMA50']: sigs.append('Bullish (SMA)')
                elif row['SMA20'] < row['SMA50']: sigs.append('Bearish (SMA)')
                if row['RSI'] < 30: sigs.append('Oversold')
                elif row['RSI'] > 70: sigs.append('Overbought')
                if row['MACD'] > row['MACD_Sig']: sigs.append('MACD Bullish')
                if row['Ichimoku_Conv'] > row['Ichimoku_Base']: sigs.append('Ichimoku Bullish Cross')
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
                
            return results
        except Exception as e:
            logger.error(f"Error: {e}")
            return data

    @classmethod
    @classmethod
    @classmethod
    def generate_chart_image(cls, data, symbol_name, timeframe='daily'):
        try:
            if not data: return None
            df = pd.DataFrame(data)
            if df.empty: return None
            
            df_plot = df.copy()
            if 'date' in df_plot.columns:
                df_plot['date'] = pd.to_datetime(df_plot['date'])
                df_plot.set_index('date', inplace=True)
            
            # Use last 100 points for plot if not already limited
            if len(df_plot) > 100:
                df_plot = df_plot.sort_index().tail(100)
            else:
                df_plot = df_plot.sort_index()
            
            for c in ['open', 'high', 'low', 'close', 'volume']:
                if c in df_plot.columns:
                    df_plot[c] = pd.to_numeric(df_plot[c], errors='coerce')

            supports, resistances = cls.get_support_resistance(df)
            
            hlines, colors, hlabels = [], [], []
            for s in supports[:3]:
                hlines.append(s['value']); colors.append('g'); hlabels.append(f"S:{s['strength']}")
            for r in resistances[:3]:
                hlines.append(r['value']); colors.append('r'); hlabels.append(f"R:{r['strength']}")

            apds = []
            if 'Ichimoku_A' in df_plot.columns and 'Ichimoku_B' in df_plot.columns:
                apds.append(mpf.make_addplot(df_plot['Ichimoku_A'], color='green', width=0.5, alpha=0.3))
                apds.append(mpf.make_addplot(df_plot['Ichimoku_B'], color='red', width=0.5, alpha=0.3))

            if 'RSI' in df_plot.columns:
                apds.append(mpf.make_addplot(df_plot['RSI'], panel=1, color='purple', ylabel='RSI', ylim=(0, 100)))
            
            if 'MACD' in df_plot.columns and 'MACD_Sig' in df_plot.columns:
                macd_hist = df_plot['MACD'] - df_plot['MACD_Sig']
                apds.append(mpf.make_addplot(df_plot['MACD'], panel=2, color='orange', ylabel='MACD'))
                apds.append(mpf.make_addplot(df_plot['MACD_Sig'], panel=2, color='blue'))
                apds.append(mpf.make_addplot(macd_hist, type='bar', panel=2, color='gray', alpha=0.3))

            buf = io.BytesIO()
            mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False)
            
            timeframe_label = "Weekly" if timeframe == 'weekly' else "Daily"
            tf_fa = "هفتگی" if timeframe == 'weekly' else "روزانه"
            
            # Create subplots for better control
            fig, axes = mpf.plot(df_plot, type='candle', style=s, volume=True, 
                                 addplot=apds,
                                 hlines=dict(hlines=hlines, colors=colors, linestyle='-.', alpha=0.4),
                                 title=f"Technical Analysis ({tf_fa}): {symbol_name}",
                                 ylabel='Price', ylabel_lower='Volume',
                                 returnfig=True, figsize=(15, 12),
                                 panel_ratios=(6, 2, 2, 2)) # Increased volume panel height

            # Shamsi date conversion for X-axis
            def to_jalali(x, pos):
                try:
                    # Check if x is within bounds of the dataframe index
                    idx = int(round(x))
                    if 0 <= idx < len(df_plot):
                        dt = df_plot.index[idx]
                        j_dt = jdatetime.date.fromgregorian(date=dt.date())
                        return j_dt.strftime('%y/%m/%d')
                    return ""
                except Exception as e:
                    return ""

            # Apply Jalali formatter to the price axis
            for ax in axes:
                # In mplfinance, usually the last axis with labels is the one we want
                # or we can check if it has a major formatter that we can override
                ax.xaxis.set_major_formatter(plt.FuncFormatter(to_jalali))
            
            # Adjust date label spacing
            fig.autofmt_xdate()
            
            ax_price = axes[0]
            for val, label, color in zip(hlines, hlabels, colors):
                ax_price.annotate(label, xy=(1, val), xycoords=('axes fraction', 'data'),
                                 xytext=(10, 0), textcoords='offset points',
                                 color=color, fontsize=8, fontweight='bold')

            fig.savefig(buf, format='png', bbox_inches='tight', dpi=120)
            plt.close(fig)
            buf.seek(0)
            return buf
        except Exception as e:
            logger.error(f"Chart error: {e}")
            return None

    @staticmethod
    def generate_strategy_matrix(current_price, supports, resistances):
        """
        Generates a strategy matrix based on 4 dimensions:
        1. Personality: Real, Legal
        2. Risk: Aggressive, Neutral, Cautious
        3. Return: Defensive, Balanced, Offensive
        4. Horizon: Short, Medium, Long
        """
        if not current_price or not supports or not resistances:
            return []

        strategies = []
        
        # Helper to get levels
        s1 = supports[0]['value'] if len(supports) > 0 else current_price * 0.95
        s2 = supports[1]['value'] if len(supports) > 1 else s1 * 0.95
        r1 = resistances[0]['value'] if len(resistances) > 0 else current_price * 1.05
        r2 = resistances[1]['value'] if len(resistances) > 1 else r1 * 1.05
        r3 = resistances[2]['value'] if len(resistances) > 2 else r2 * 1.10

        # Define 12 reasonable archetypes (covering the 54-state space meaningfully)
        archetypes = [
            # 1. Personality | Risk | Return | Horizon
            ("حقیقی", "جسور", "تهاجمی", "کوتاه مدت", "نوسان‌گیری سریع (Scalping)", f"خرید در {s1} - تریگر: واگرایی مثبت RSI", r1, s2, "ورود پله‌ای در حمایت‌های نزدیک"),
            ("حقیقی", "جسور", "تهاجمی", "میان مدت", "معاملات تکانه‌ای (Momentum)", f"خرید در شکست {r1} - تریگر: حجم بالا", r2, s1, "تعقیب روند با حد ضرر شناور"),
            ("حقیقی", "خنثی", "متعادل", "کوتاه مدت", "نوسان‌گیری کانالی", f"خرید در {s1} - تریگر: کندل برگشتی", r1, s2, "خرید در کف و فروش در سقف کانال"),
            ("حقیقی", "خنثی", "متعادل", "میان مدت", "معاملات روندی (Trend Following)", f"خرید در تثبیت بالای SMA20", r2, s1, "صبر برای تایید روند و حفظ موقعیت"),
            ("حقیقی", "محتاط", "تدافعی", "میان مدت", "سرمایه‌گذاری کم‌ریسک", f"خرید در {s1} - تریگر: اشباع فروش RSI", r1, s2, "تمرکز بر حفظ اصل سرمایه"),
            ("حقیقی", "محتاط", "تدافعی", "بلند مدت", "ارزش‌محور (Value Investing)", f"خرید در {s2} - تریگر: نزدیکی به کف تاریخی", r2, s1, "نادیده گرفتن نوسانات موقت"),
            ("حقوقی", "خنثی", "ارزشمند", "بلند مدت", "استراتژی انباشت (Accumulation)", f"خرید پله‌ای در محدوده {s1} تا {s2}", r3, s2 * 0.9, "ورود سنگین در نواحی حمایتی معتبر"),
            ("حقوقی", "محتاط", "تدافعی", "بلند مدت", "مدیریت ثروت (Wealth Mgmt)", f"خرید در {s2} - تریگر: نسبت P/E تاریخی", r2, s2 * 0.85, "رویکرد صبورانه و خروج در سقف‌های قیمتی"),
            ("حقیقی", "جسور", "متعادل", "کوتاه مدت", "معاملات خبری (Event Driven)", f"خرید در {current_price} - تریگر: اخبار رانتی/بنیادی", r1, current_price * 0.94, "ورود سریع و خروج با سود معقول"),
            ("حقوقی", "جسور", "تهاجمی", "میان مدت", "بازارگردانی/حمایت", f"خرید در محدوده {s1}", r1, s2, "کنترل قیمت و جمع‌آوری سهم"),
            ("حقیقی", "خنثی", "تهاجمی", "بلند مدت", "رشد‌محور (Growth)", f"خرید در {s1} - تریگر: گزارشات ماهانه مثبت", r3, s2, "سرمایه‌گذاری در شرکت‌های با پتانسیل رشد بالا"),
            ("حقیقی", "محتاط", "متعادل", "بلند مدت", "سرمایه‌گذاری سنتی", f"خرید در {s1} - تریگر: تثبیت در کف", r2, s2, "تنوع‌بخشی به پرتفوی و دوری از هیجان")
        ]

        for p, risk, ret, hor, style, entry, target, sl, desc in archetypes:
            strategies.append({
                "پروفایل سرمایه‌گذار": f"{p} ({ret})",
                "تیپ شخصیتی": risk,
                "افق زمانی": hor,
                "نقطه ورود": entry,
                "حد ضرر (SL)": sl,
                "حد سود (TP)": target,
                "توضیحات استراتژی": f"{style}: {desc}"
            })
        return strategies
