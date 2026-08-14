"""
Comprehensive Technical Indicators - Version 2.0
50+ indicators with 14 new additions
All native Python/pandas/numpy implementations
"""

import pandas as pd
import numpy as np

class UpdatedIndicators:
    """
    Enhanced indicators with 14 new additions
    """

    # Ichimoku Cloud
    @staticmethod
    def ichimoku_cloud(data: pd.DataFrame, tenkan: int = 9, kijun: int = 26, senkou: int = 52):
        """Ichioku Cloud parameters"""
        tenkan_sen = data['close']. rolling(window=tenkan).mean()
        kijun_sen = data['close']. rolling(window=kijun).mean()
        senkou_a = (data['high']. rolling(window=senkou).max() + data['low']. rolling(window=senkou).min()) / 2
        senkou_b = (data['high']. rolling(window=2*senkou).max() + data['low']. rolling(window=2*senkou).min()) / 2
        chikou = data['close']. shift(senkou)
        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'chikou': chikou
        }

    # Parabolic SAR
    @staticmethod
    def parabolic_sar(data: pd.DataFrame, init: float = 0.02, max: float = 0.2):
        """Parabolic SAR calculation"""
        sar = data['low'].iloc[0]
        af = init
        trend = 1  # 1=up, -1=down
        sar_values = [sar]
        for i in range(1, len(data)):
            if trend == 1:
                sar += af * (data['high'].iloc[i-1] - sar)
                if sar > data['low'].iloc[i]:
                    trend = -1
                    sar = data['low'].iloc[i]
                    af = init
            else:
                sar += af * (sar - data['low'].iloc[i-1])
                if sar < data['high'].iloc[i]:
                    trend = 1
                    sar = data['high'].iloc[i]
                    af = init
            af = min(max, af * 1.02)
            sar_values.append(sar)
        return pd.Series(sar_values, index=data.index)

    # Vortex Indicators
    @staticmethod
    def vortex_indicators(data: pd.DataFrame, period: int = 14):
        """Vortex Indicator calculation"""
        # Calculate true range
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr = pd.DataFrame(
            [high - low, abs(high - close.shift(1)), abs(low - close.shift(1))],
            index=data.index,
            columns=['tr1', 'tr2', 'tr3']
        ).max(axis=1)
        
        # Accumulation/distribution
        tr_used = pd.Series([0]*len(data), index=data.index)
        for i in range(1, len(tr)):
            tr_used.iloc[i] = tr.iloc[i] if close.iloc[i] > close.iloc[i-1] else -tr.iloc[i]
        
        bullish = tr_used.rolling(window=period).sum() / tr.sum(window=period)
        bearish = 1 - bullish
        return {'vortex_bull': bullish, 'vortex_bear': bearish}

    # Williams %R
    @staticmethod
    def williams_r(data: pd.DataFrame, period: int = 14):
        """Williams %R calculation"""
        low_min = data['low']. rolling(window=period).min()
        r = 100 * (low_min - data['close']) / (data['high'] - data['low'])
        return r

    # Moving Average Envelope
    @staticmethod
    def moving_average_envelope(data: pd.Series, period: int = 20, deviation: float = 2.0):
        """SMA with ATR-based envelopes"""
        sma = data.rolling(window=period).mean()
        atr = UpdatedIndicators.atr(pd.DataFrame({'close':data,'high':data,'low':data}), period)
        upper = sma + deviation * atr
        lower = sma - deviation * atr
        return {'upper': upper, 'middle': sma, 'lower': lower}

    # ADXR
    @staticmethod
    def adxr(adx: pd.Series, period: int = 14):
        """ADX with range (ADXR)"""
        if adx is None: return None
        adxr = (adx.rolling(window=period).sum() / period) * 100
        return adxr

    # Elder Ray
    @staticmethod
    def elder_ray(data: pd.DataFrame, period: int = 13):
        """Elder Ray lines calculating"""
        high = data['high']
        low = data['low']
        
        bull_line = high.rolling(window=period).max() - data['close']
        bear_line = data['close'] - low.rolling(window=period).min()
        return {'bull_line': bull_line, 'bear_line': bear_line}

    # Zig Zag
    @staticmethod
    def zig_zag(data: pd.Series, deviation: float = 0.05):
        """Price filter based on percentage deviation"""
        zz = [data.iloc[0]]
        for i in range(1, len(data)):
            if abs(data.iloc[i] - zz[-1]) / abs(zz[-1]) > deviation:
                zz.append(data.iloc[i])
        return pd.Series(zz, index=data.index)

    # Fibonacci Extensions
    @staticmethod
    def fibonacci_extensions(data: pd.DataFrame, swing_high_idx: int, swing_low_idx: int):
        """Fibonacci extension levels"""
        high = data['high'].iloc[swing_high_idx]
        low = data['low'].iloc[swing_low_idx]
        diff = high - low
        return {
            '127.2%': high + 0.272 * diff,
            '161.8%': high + 0.618 * diff,
            '261.8%': high + 1.618 * diff
        }

    # Rainbow Cloud
    @staticmethod
    def rainbow_cloud(data: pd.Series, period: int = 5):
        """Rainbow Cloud volatility indicator"""
        hl2 = (data['high'] + data['low']) / 2
        hl2_sma = hl2.rolling(window=period).mean()
        hl2_atr = UpdatedIndicators.atr(pd.DataFrame({'close':data,'high':data,'low':data}), period)
        cloud = (hl2_sma + hl2_atr, hl2_sma - hl2_atr)
        return cloud

    # Rainbow Momentum
    @staticmethod
    def rainbow_momentum(data: pd.Series, period: int = 14):
        """Rainbow Momentum oscillator"""
        return (data - data.rolling(window=period).mean()) / data.rolling(window=period).std()

    # Rainbow Volatility
    @staticmethod
    def rainbow_volatility(data: pd.Series, period: int = 20):
        """Rainbow Volatility band"""
        return data.rolling(window=period).std()

    # Chaikin Oscillator
    @staticmethod
    def chaikin_oscillator(data: pd.DataFrame, period: int = 10):
        """Chaikin Accumulation/Distribution oscillator"""
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        accumulation = (typical_price - data['low']) * data['volume']
        cd = accumulation.rolling(window=period).sum()
        signal = cd.rolling(window=2).mean()
        osc = signal - cd.ewm(span=3, adjust=False).mean()
        return osc

    # Volume Profile
    @staticmethod
    def volume_profile(data: pd.DataFrame):
        """Volume profile histogram"""
        profile = pd.DataFrame(columns=['price', 'volume'])
        for price in data['close'].unique():
            mask = (data['close'] >= price - 1) & (data['close'] <= price + 1)
            profile = profile.append({'price': price, 'volume': data[mask]['volume'].sum()})
        profile = profile.sort_values('volume', ascending=False)
        return profile

    # Update all indicators method
    @staticmethod
    def all_indicators(df: pd.DataFrame, include_rainbow: bool = True):
        """
        Calculate all indicators including rainbow additions
        """
        base = UpdatedIndicators.all_indicators(df, include_volatility=True, include_volume=True)
        if include_rainbow:
            base.update({
                'ichimoku_cloud': UpdatedIndicators.ichimoku_cloud(df),
                'parabolic_sar': UpdatedIndicators.parabolic_sar(df),
                'vortex': UpdatedIndicators.vortex_indicators(df),
                'williams_r': UpdatedIndicators.williams_r(df),
                'envelope': UpdatedIndicators.moving_average_envelope(df['close']),
                'adxr': UpdatedIndicators.adxr(base.get('adx', pd.Series())),
                'elder_ray': UpdatedIndicators.elder_ray(df),
                'zig_zag': UpdatedIndicators.zig_zag(df['close']),
                'fib_extensions': UpdatedIndicators.fibonacci_extensions(df, 0, len(df)-1),
                'rainbow_cloud': UpdatedIndicators.rainbow_cloud(df['close']),
                'rainbow_momentum': UpdatedIndicators.rainbow_momentum(df['close']),
                'rainbow_volatility': UpdatedIndicators.rainbow_volatility(df['close']),
                'chaikin_oscillator': UpdatedIndicators.chaikin_oscillator(df),
                'volume_profile': UpdatedIndicators.volume_profile(df)
            })
        return base