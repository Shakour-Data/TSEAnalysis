import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import logging
from typing import Dict, List, Optional, Tuple
from app.utils.core_utils import CoreUtils
from app.services.technical_analysis import TechnicalAnalyzer
from app.utils.chart_optimizer import ChartOptimizer

logger = logging.getLogger(__name__)

class SymbolInfographics:
    """
    نماد کے لیے جامع انفوگرافکس بنانے کا نظام
    شامل ہے: چارٹ، تجزیات، شماریات، اور بصری اجزاء
    """

    @staticmethod
    def generate_symbol_infographics(symbol: str, data: List[Dict], period: str = "1Y") -> Dict:
        """
        نماد کے لیے مکمل انفوگرافکس بنائیں

        Args:
            symbol: نماد کا نام
            data: قیمت کی تاریخی ڈیٹا
            period: تجزیہ کی مدت

        Returns:
            انفوگرافکس کا ڈکشنری شامل تصاویر اور ڈیٹا
        """
        if not data or len(data) < 10:
            logger.warning(f"Insufficient data for {symbol}")
            return {}

        try:
            # ڈیٹا کو DataFrame میں تبدیل کریں
            df = pd.DataFrame(data)
            df = SymbolInfographics._prepare_dataframe(df)

            if df.empty:
                return {}

            infographics = {
                'symbol': symbol,
                'period': period,
                'charts': {},
                'statistics': {},
                'analysis': {},
                'metadata': {}
            }

            # 1. قیمت چارٹ بنائیں
            infographics['charts']['price_chart'] = SymbolInfographics._generate_price_chart(df, symbol)

            # 2. حجم چارٹ بنائیں
            infographics['charts']['volume_chart'] = SymbolInfographics._generate_volume_chart(df, symbol)

            # 3. تکنیکی انڈیکیٹرز چارٹ
            infographics['charts']['technical_chart'] = SymbolInfographics._generate_technical_chart(df, symbol)

            # 5. Correlation matrix
            infographics['charts']['correlation_matrix'] = SymbolInfographics._generate_correlation_matrix(df, symbol)

            # 6. Volatility analysis
            infographics['charts']['volatility_analysis'] = SymbolInfographics._generate_volatility_analysis(df, symbol)

            # 7. Seasonal analysis
            infographics['charts']['seasonal_analysis'] = SymbolInfographics._generate_seasonal_analysis(df, symbol)

            # 5. شماریات کا خلاصہ
            infographics['statistics'] = SymbolInfographics._calculate_statistics(df)

            # 6. تکنیکی تجزیہ
            infographics['analysis'] = SymbolInfographics._enhanced_technical_analysis(df)

            # 7. میٹا ڈیٹا
            infographics['metadata'] = SymbolInfographics._generate_metadata(df, symbol)

            return infographics

        except Exception as e:
            logger.error(f"Infographics generation failed for {symbol}: {e}")
            return {}

    @staticmethod
    def _prepare_dataframe(data: pd.DataFrame) -> pd.DataFrame:
        """ڈیٹا کو صاف اور تیار کریں"""
        try:
            # ضروری کالم چیک کریں
            required_cols = ['close', 'open', 'high', 'low', 'volume']
            if not all(col in data.columns for col in required_cols):
                logger.warning("Missing required columns in data")
                return pd.DataFrame()

            # عددی اقدار کو یقینی بنائیں
            for col in required_cols:
                data[col] = pd.to_numeric(data[col], errors='coerce')

            # NaN اقدار کو ہٹائیں
            data = data.dropna(subset=['close'])

            # تاریخ کو انڈیکس بنائیں اگر موجود ہو
            date_col = None
            for col in ['date', 'time', 'timestamp']:
                if col in data.columns:
                    date_col = col
                    break

            if date_col:
                data[date_col] = pd.to_datetime(data[date_col], errors='coerce')
                data = data.sort_values(date_col)
                data.set_index(date_col, inplace=True)

            return data

        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            return pd.DataFrame()

    @staticmethod
    def _generate_price_chart(df: pd.DataFrame, symbol: str) -> Optional[str]:
        """قیمت کا چارٹ بنائیں"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})

            # کندل اسٹک چارٹ
            ax1.plot(df.index, df['close'], label='Close', color='blue', linewidth=1.5)

            # حرکت پذیر اوسط
            if len(df) > 20:
                sma20 = df['close'].rolling(window=20).mean()
                ax1.plot(df.index, sma20, label='SMA 20', color='orange', linestyle='--')

            if len(df) > 50:
                sma50 = df['close'].rolling(window=50).mean()
                ax1.plot(df.index, sma50, label='SMA 50', color='red', linestyle='-.')

            ax1.set_title(f'{symbol} - قیمت چارٹ', fontsize=14, fontweight='bold')
            ax1.set_ylabel('قیمت')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # حجم چارٹ
            ax2.bar(df.index, df['volume'], color='green', alpha=0.7)
            ax2.set_ylabel('حجم')
            ax2.set_xlabel('تاریخ')

            plt.tight_layout()

            # تصویر کو base64 میں تبدیل کریں
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)

            return SymbolInfographics._buffer_to_base64(buf)

        except Exception as e:
            logger.error(f"Price chart generation failed: {e}")
            return None

    @staticmethod
    def _generate_volume_chart(df: pd.DataFrame, symbol: str) -> Optional[str]:
        """حجم کا چارٹ بنائیں"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))

            # حجم بار چارٹ
            colors = ['green' if row['close'] >= row['open'] else 'red' for _, row in df.iterrows()]
            ax.bar(df.index, df['volume'], color=colors, alpha=0.7)

            # حجم کا اوسط
            if len(df) > 20:
                vol_sma = df['volume'].rolling(window=20).mean()
                ax.plot(df.index, vol_sma, color='blue', linewidth=2, label='Volume SMA 20')

            ax.set_title(f'{symbol} - حجم چارٹ', fontsize=14, fontweight='bold')
            ax.set_ylabel('حجم')
            ax.set_xlabel('تاریخ')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)

            return SymbolInfographics._buffer_to_base64(buf)

        except Exception as e:
            logger.error(f"Volume chart generation failed: {e}")
            return None

    @staticmethod
    def _generate_technical_chart(df: pd.DataFrame, symbol: str) -> Optional[str]:
        """تکنیکی انڈیکیٹرز کا چارٹ بنائیں"""
        try:
            fig, axes = plt.subplots(3, 1, figsize=(12, 12))

            # قیمت چارٹ
            axes[0].plot(df.index, df['close'], label='Close', color='blue')
            if len(df) > 20:
                axes[0].plot(df.index, df['close'].rolling(20).mean(), label='SMA 20', color='orange')
            axes[0].set_title('قیمت اور حرکت پذیر اوسط')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)

            # RSI
            if len(df) > 14:
                rsi = SymbolInfographics._calculate_rsi(df['close'])
                axes[1].plot(df.index, rsi, color='purple', linewidth=2)
                axes[1].axhline(y=70, color='red', linestyle='--', alpha=0.7)
                axes[1].axhline(y=30, color='green', linestyle='--', alpha=0.7)
                axes[1].fill_between(df.index, 30, 70, alpha=0.1, color='gray')
                axes[1].set_title('RSI (Relative Strength Index)')
                axes[1].set_ylim(0, 100)
                axes[1].grid(True, alpha=0.3)

            # MACD
            if len(df) > 26:
                macd, signal, hist = SymbolInfographics._calculate_macd(df['close'])
                axes[2].plot(df.index, macd, label='MACD', color='blue')
                axes[2].plot(df.index, signal, label='Signal', color='red')
                axes[2].bar(df.index, hist, label='Histogram', color='green', alpha=0.5)
                axes[2].set_title('MACD')
                axes[2].legend()
                axes[2].grid(True, alpha=0.3)

            plt.suptitle(f'{symbol} - تکنیکی تجزیہ', fontsize=16, fontweight='bold')
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)

            return SymbolInfographics._buffer_to_base64(buf)

        except Exception as e:
            logger.error(f"Technical chart generation failed: {e}")
            return None

    @staticmethod
    def _generate_price_distribution(df: pd.DataFrame, symbol: str) -> Optional[str]:
        """قیمت کی تقسیم کا چارٹ بنائیں"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))

            # قیمت کی تقسیم
            axes[0, 0].hist(df['close'], bins=50, alpha=0.7, color='blue', edgecolor='black')
            axes[0, 0].set_title('قیمت کی تقسیم')
            axes[0, 0].set_xlabel('قیمت')
            axes[0, 0].set_ylabel('تعدد')
            axes[0, 0].grid(True, alpha=0.3)

            # Box plot
            axes[0, 1].boxplot(df['close'])
            axes[0, 1].set_title('Box Plot')
            axes[0, 1].set_ylabel('قیمت')
            axes[0, 1].grid(True, alpha=0.3)

            # حجم کی تقسیم
            axes[1, 0].hist(df['volume'], bins=30, alpha=0.7, color='green', edgecolor='black')
            axes[1, 0].set_title('حجم کی تقسیم')
            axes[1, 0].set_xlabel('حجم')
            axes[1, 0].set_ylabel('تعدد')
            axes[1, 0].grid(True, alpha=0.3)

            # Scatter plot: قیمت vs حجم
            axes[1, 1].scatter(df['close'], df['volume'], alpha=0.5, color='purple')
            axes[1, 1].set_title('قیمت vs حجم')
            axes[1, 1].set_xlabel('قیمت')
            axes[1, 1].set_ylabel('حجم')
            axes[1, 1].grid(True, alpha=0.3)

            plt.suptitle(f'{symbol} - قیمت اور حجم کی تقسیم', fontsize=16, fontweight='bold')
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)

            return SymbolInfographics._buffer_to_base64(buf)

        except Exception as e:
            logger.error(f"Price distribution chart generation failed: {e}")
            return None

    @staticmethod
    def _calculate_statistics(df: pd.DataFrame) -> Dict:
        """شماریات کا خلاصہ بنائیں"""
        try:
            close_prices = df['close'].dropna()

            stats = {
                'current_price': CoreUtils.format_number(close_prices.iloc[-1], 'تومان', persian_digits=True),
                'price_change': SymbolInfographics._calculate_price_change(close_prices),
                'highest_price': CoreUtils.format_number(close_prices.max(), 'تومان', persian_digits=True),
                'lowest_price': CoreUtils.format_number(close_prices.min(), 'تومان', persian_digits=True),
                'average_price': CoreUtils.format_number(close_prices.mean(), 'تومان', persian_digits=True),
                'price_volatility': f"{close_prices.std() / close_prices.mean() * 100:.2f}%",
                'total_volume': CoreUtils.format_number(df['volume'].sum(), persian_digits=True),
                'average_volume': CoreUtils.format_number(df['volume'].mean(), persian_digits=True),
                'data_points': len(df),
                'date_range': f"{df.index.min()} to {df.index.max()}" if hasattr(df.index, 'min') else 'N/A'
            }

            return stats

        except Exception as e:
            logger.error(f"Statistics calculation failed: {e}")
            return {}

    @staticmethod
    def _calculate_price_change(prices: pd.Series) -> str:
        """قیمت کی تبدیلی کا حساب لگائیں"""
        try:
            if len(prices) < 2:
                return "N/A"

            current = prices.iloc[-1]
            previous = prices.iloc[-2]
            change = current - previous
            change_percent = (change / previous) * 100

            change_str = CoreUtils.format_number(change, 'تومان', persian_digits=True)
            return f"{change_str} ({change_percent:+.2f}%)"

        except Exception:
            return "N/A"

    @staticmethod
    def _perform_technical_analysis(df: pd.DataFrame) -> Dict:
        """تکنیکی تجزیہ انجام دیں"""
        try:
            analysis = {}

            # موجودہ رجحان
            if len(df) > 20:
                sma20 = df['close'].rolling(20).mean()
                sma50 = df['close'].rolling(50).mean() if len(df) > 50 else None

                current_price = df['close'].iloc[-1]
                sma20_val = sma20.iloc[-1]

                if current_price > sma20_val:
                    analysis['trend'] = "صعودی"
                else:
                    analysis['trend'] = "نزولی"

                if sma50 is not None:
                    sma50_val = sma50.iloc[-1]
                    if sma20_val > sma50_val:
                        analysis['trend'] = "صعودی قوی"
                    elif sma20_val < sma50_val:
                        analysis['trend'] = "نزولی قوی"

            # RSI تجزیہ
            if len(df) > 14:
                rsi = SymbolInfographics._calculate_rsi(df['close'])
                rsi_val = rsi.iloc[-1]
                if rsi_val > 70:
                    analysis['rsi_signal'] = "فروش بیش از حد"
                elif rsi_val < 30:
                    analysis['rsi_signal'] = "خرید بیش از حد"
                else:
                    analysis['rsi_signal'] = "متعادل"

            # حجم تجزیہ
            avg_volume = df['volume'].mean()
            recent_volume = df['volume'].tail(5).mean()
            if recent_volume > avg_volume * 1.5:
                analysis['volume_trend'] = "افزایشی"
            
            # مومنتم تجزیہ
            if len(df) > 14:
                momentum = SymbolInfographics._calculate_momentum(df['close'])
                latest_momentum = momentum.iloc[-1]
                if latest_momentum > 0:
                    analysis['momentum'] = "مثبت"
                else:
                    analysis['momentum'] = "منفی"

            # حمایت و مقاومت
            supports, resistances = SymbolInfographics._find_support_resistance(df)
            analysis['support_levels'] = len(supports)
            analysis['resistance_levels'] = len(resistances)

            if recent_volume > avg_volume * 1.5:
                analysis['volume_signal'] = "حجم بالا"
            elif recent_volume < avg_volume * 0.5:
                analysis['volume_signal'] = "حجم کم"
            else:
                analysis['volume_signal'] = "حجم متعادل"

            return analysis

        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            return {}

    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI کا حساب لگائیں"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception:
            return pd.Series()

    @staticmethod
    def _calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD کا حساب لگائیں"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd = ema_fast - ema_slow
            signal_line = macd.ewm(span=signal).mean()
            histogram = macd - signal_line
            return macd, signal_line, histogram
        except Exception:
            return pd.Series(), pd.Series(), pd.Series()

    @staticmethod
    def _generate_metadata(df: pd.DataFrame, symbol: str) -> Dict:
        """میٹا ڈیٹا بنائیں"""
        return {
            'symbol': symbol,
            'data_points': len(df),
            'last_updated': pd.Timestamp.now().isoformat(),
            'price_range': {
                'min': float(df['close'].min()),
                'max': float(df['close'].max())
            },
            'volume_range': {
                'min': float(df['volume'].min()),
                'max': float(df['volume'].max())
            }
        }

    @staticmethod
    def _generate_correlation_matrix(df: pd.DataFrame, symbol: str) -> Optional[str]:
        """Generate correlation matrix heatmap"""
        try:
            # Select numeric columns
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            available_cols = [col for col in numeric_cols if col in df.columns]

            if len(available_cols) < 2:
                return None

            # Calculate correlation matrix
            corr_matrix = df[available_cols].corr()

            fig, ax = plt.subplots(figsize=(10, 8))

            # Create heatmap
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                       square=True, linewidths=0.5, ax=ax)

            ax.set_title(f'{symbol} - Correlation Matrix', fontsize=14, fontweight='bold')

            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)

            return SymbolInfographics._buffer_to_base64(buf)

        except Exception as e:
            logger.error(f"Correlation matrix generation failed: {e}")
            return None

    @staticmethod
    def _generate_volatility_analysis(df: pd.DataFrame, symbol: str) -> Optional[str]:
        """Generate volatility analysis chart"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

            # Price volatility (rolling std)
            if len(df) > 20:
                price_volatility = df['close'].rolling(window=20).std()
                ax1.plot(df.index, price_volatility, color='red', linewidth=2, label='Price Volatility (20-day)')
                ax1.fill_between(df.index, 0, price_volatility, alpha=0.3, color='red')
                ax1.set_title('Price Volatility Analysis')
                ax1.set_ylabel('Volatility')
                ax1.legend()
                ax1.grid(True, alpha=0.3)

            # Volume volatility
            if len(df) > 20:
                volume_volatility = df['volume'].rolling(window=20).std()
                ax2.plot(df.index, volume_volatility, color='blue', linewidth=2, label='Volume Volatility (20-day)')
                ax2.fill_between(df.index, 0, volume_volatility, alpha=0.3, color='blue')
                ax2.set_title('Volume Volatility Analysis')
                ax2.set_ylabel('Volume Volatility')
                ax2.set_xlabel('Date')
                ax2.legend()
                ax2.grid(True, alpha=0.3)

            plt.suptitle(f'{symbol} - Volatility Analysis', fontsize=16, fontweight='bold')
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)

            return SymbolInfographics._buffer_to_base64(buf)

        except Exception as e:
            logger.error(f"Volatility analysis generation failed: {e}")
            return None

    @staticmethod
    def _generate_seasonal_analysis(df: pd.DataFrame, symbol: str) -> Optional[str]:
        """Generate seasonal analysis chart"""
        try:
            if not hasattr(df.index, 'month') or len(df) < 30:
                return None

            # Group by month
            monthly_returns = df.groupby(df.index.month)['close'].agg(['first', 'last'])
            monthly_returns['return'] = (monthly_returns['last'] - monthly_returns['first']) / monthly_returns['first'] * 100

            fig, ax = plt.subplots(figsize=(12, 6))

            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

            ax.bar(range(1, 13), monthly_returns['return'], color='skyblue', alpha=0.7)
            ax.set_xlabel('Month')
            ax.set_ylabel('Average Return (%)')
            ax.set_title(f'{symbol} - Seasonal Performance by Month')
            ax.set_xticks(range(1, 13))
            ax.set_xticklabels(months)
            ax.grid(True, alpha=0.3)

            # Add value labels on bars
            for i, v in enumerate(monthly_returns['return']):
                ax.text(i + 1, v + 0.1, f'{v:.1f}%', ha='center', va='bottom')

            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)

            return SymbolInfographics._buffer_to_base64(buf)

        except Exception as e:
            logger.error(f"Seasonal analysis generation failed: {e}")
            return None
        """Buffer کو base64 string میں تبدیل کریں"""
        try:
            buffer.seek(0)
            image_data = base64.b64encode(buffer.read()).decode('utf-8')
            return f"data:image/png;base64,{image_data}"
        except Exception as e:
            return ""

    @staticmethod
    def generate_infographics_report(symbol: str, data: List[Dict], period: str = "1Y") -> Dict:
        """
        نماد کے لیے مکمل انفوگرافکس رپورٹ بنائیں
        شامل ہے: تمام چارٹ، شماریات، اور تجزیہ
        """
        infographics = SymbolInfographics.generate_symbol_infographics(symbol, data, period)

        if not infographics:
            return {}

        # رپورٹ کا خلاصہ بنائیں
        report = {
            'symbol': symbol,
            'generated_at': pd.Timestamp.now().isoformat(),
            'summary': {
                'current_price': infographics.get('statistics', {}).get('current_price', 'N/A'),
                'trend': infographics.get('analysis', {}).get('trend', 'N/A'),
                'rsi_signal': infographics.get('analysis', {}).get('rsi_signal', 'N/A'),
                'volume_signal': infographics.get('analysis', {}).get('volume_signal', 'N/A')
            },
            'charts': infographics.get('charts', {}),
            'full_statistics': infographics.get('statistics', {}),
            'technical_analysis': infographics.get('analysis', {}),
            'metadata': infographics.get('metadata', {})
        }

        return report

    @staticmethod
    def _calculate_momentum(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate momentum indicator"""
        try:
            return (df['close'] - df['close'].shift(period)) / df['close'].shift(period) * 100
        except Exception:
            return pd.Series()

    @staticmethod
    def _detect_support_resistance(df: pd.DataFrame, window: int = 20) -> Tuple[float, float]:
        """Detect support and resistance levels"""
        try:
            recent_high = df['high'].tail(window).max()
            recent_low = df['low'].tail(window).min()
            return recent_low, recent_high
        except Exception:
            return 0.0, 0.0

    @staticmethod
    def _enhanced_technical_analysis(df: pd.DataFrame) -> Dict:
        """Perform enhanced technical analysis with momentum and support/resistance"""
        try:
            analysis = SymbolInfographics._perform_technical_analysis(df)

            # Add momentum analysis
            if len(df) > 14:
                momentum = SymbolInfographics._calculate_momentum(df)
                current_momentum = momentum.iloc[-1] if not momentum.empty else 0

                if current_momentum > 5:
                    analysis['momentum'] = "قوی مثبت"
                elif current_momentum > 0:
                    analysis['momentum'] = "مثبت"
                elif current_momentum > -5:
                    analysis['momentum'] = "منفی"
                else:
                    analysis['momentum'] = "قوی منفی"

            # Add support/resistance levels
            support, resistance = SymbolInfographics._detect_support_resistance(df)
            current_price = df['close'].iloc[-1]

            analysis['support_level'] = CoreUtils.format_number(support, 'تومان', persian_digits=True)
            analysis['resistance_level'] = CoreUtils.format_number(resistance, 'تومان', persian_digits=True)

            # Position analysis
            if current_price > resistance * 0.98:
                analysis['price_position'] = "نزدیک مزاحمت"
            elif current_price < support * 1.02:
                analysis['price_position'] = "نزدیک حمایت"
            else:
                analysis['price_position'] = "متعادل"

            return analysis

        except Exception as e:
            logger.error(f"Enhanced technical analysis failed: {e}")
            return {}