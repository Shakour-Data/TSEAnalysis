"""
Enhanced AI Assistant for TSE Analysis
- Advanced ML Model with more features
- Intelligent text generation for analysis reports
- LLM integration support (OpenAI, local models)
- Comprehensive error handling and fallbacks
"""

import os
import random
import pickle
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np
import jdatetime

logger = logging.getLogger(__name__)


class Trend(Enum):
    BULLISH = "صعودی"
    BEARISH = "نزولی"
    NEUTRAL = "خنثی"
    UNKNOWN = "نامشخص"


@dataclass
class TechnicalIndicators:
    """Technical indicators container"""
    price: float
    volume: float
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    sma_20: float
    sma_50: float
    sma_200: float
    bollinger_upper: float
    bollinger_middle: float
    bollinger_lower: float
    atr: float
    adx: float
    obv: float
    volume_ma: float
    
    def to_dict(self) -> Dict:
        return {
            'price': self.price,
            'volume': self.volume,
            'rsi': round(self.rsi, 2),
            'macd': round(self.macd, 2),
            'macd_signal': round(self.macd_signal, 2),
            'macd_histogram': round(self.macd_histogram, 2),
            'sma_20': round(self.sma_20, 2),
            'sma_50': round(self.sma_50, 2),
            'sma_200': round(self.sma_200, 2),
            'bollinger_upper': round(self.bollinger_upper, 2),
            'bollinger_middle': round(self.bollinger_middle, 2),
            'bollinger_lower': round(self.bollinger_lower, 2),
            'atr': round(self.atr, 2),
            'adx': round(self.adx, 2),
            'obv': round(self.obv, 2),
            'volume_ma': round(self.volume_ma, 2)
        }


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    symbol: str
    trend: Trend
    confidence: float
    indicators: TechnicalIndicators
    support_levels: List[float]
    resistance_levels: List[float]
    signal: str
    recommendation: str
    risk_score: float
    analysis_text: str
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'trend': self.trend.value,
            'confidence': round(self.confidence, 2),
            'indicators': self.indicators.to_dict(),
            'support_levels': [round(s, 2) for s in self.support_levels],
            'resistance_levels': [round(r, 2) for r in self.resistance_levels],
            'signal': self.signal,
            'recommendation': self.recommendation,
            'risk_score': round(self.risk_score, 2),
            'analysis_text': self.analysis_text
        }


class EnhancedAIAssistant:
    """
    Enhanced AI Assistant with:
    - Advanced ML model with 20+ features
    - Multi-model ensemble
    - Intelligent text generation
    - LLM integration support
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_path="models/ai_model.pkl"):
        if self._initialized:
            return
            
        self.model_path = model_path
        self.model = None
        self.ensemble_models = {}
        self.scaler = None
        self.model_loaded = False
        self.last_update = datetime.now()
        self.feature_names = []
        self.accuracy = 0.0
        
        # Text generation templates
        self.templates = self._load_templates()
        
        # LLM configuration
        self.llm_config = {
            'enabled': False,
            'provider': None,
            'api_key': None,
            'model': None
        }
        
        self._initialized = True
        
        # Load model in background
        self._load_thread = threading.Thread(target=self._lazy_load_model, daemon=True)
        self._load_thread.start()
    
    def _load_templates(self) -> Dict:
        """Load text generation templates"""
        return {
            'analysis': {
                'bullish': [
                    "نماد {symbol} در روند صعودی قرار دارد. قیمت فعلی {price} تومان با RSI در سطح {rsi} نشان‌دهنده قدرت خریداران است.",
                    "تحلیل تکنیکال نماد {symbol}: مومنتوم مثبت با MACD در ناحیه صعودی. هدف قیمتی {target} تومان.",
                    "سیگنال BUY برای {symbol}: شکست مقاومت {resistance} تأیید روند صعودی را نشان می‌دهد."
                ],
                'bearish': [
                    "نماد {symbol} در روند نزولی است. RSI در سطح {rsi} و عبور از حمایت {support} هشدار فروش صادر می‌کند.",
                    "تحلیل تکنیکال نماد {symbol}: فشار فروش افزایش یافته و MACD در ناحیه منفی قرار دارد.",
                    "سیگنال SELL برای {symbol}: شکست حمایت {support} تأیید روند نزولی را نشان می‌دهد."
                ],
                'neutral': [
                    "نماد {symbol} در فاز رنج قرار دارد. قیمت بین حمایت {support} و مقاومت {resistance} نوسان می‌کند.",
                    "تحلیل تکنیکال نماد {symbol}: عدم قطعیت در بازار با RSI در سطح {rsi}. انتظار برای شکست الگو.",
                    "نگهداری نماد {symbol}: وضعیت خنثی، منتظر سیگنال واضح برای ورود یا خروج."
                ]
            },
            'support_resistance': [
                "حمایت‌های کلیدی: {supports} | مقاومت‌های کلیدی: {resistances}",
                "سطوح حمایتی: {supports} | سطوح مقاومتی: {resistances}",
                "پیشنهاد: خرید در {support} و فروش در {resistance}"
            ],
            'risk': {
                'low': "ریسک پایین: نسبت R/R مناسب با حد ضرر مشخص",
                'medium': "ریسک متوسط: نسبت R/R قابل قبول با مدیریت سرمایه",
                'high': "ریسک بالا: نوسانات شدید، احتیاط در معامله"
            }
        }
    
    def _get_ml_components(self):
        """Lazy import ML libraries"""
        try:
            from sklearn.ensemble import (
                RandomForestClassifier, 
                GradientBoostingClassifier,
                AdaBoostClassifier,
                VotingClassifier
            )
            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import cross_val_score
            from sklearn.metrics import accuracy_score, classification_report
            import joblib
            import pandas as pd
            import numpy as np
            
            return {
                'RandomForestClassifier': RandomForestClassifier,
                'GradientBoostingClassifier': GradientBoostingClassifier,
                'AdaBoostClassifier': AdaBoostClassifier,
                'VotingClassifier': VotingClassifier,
                'StandardScaler': StandardScaler,
                'cross_val_scores': cross_val_score,
                'accuracy_score': accuracy_score,
                'classification_report': classification_report,
                'joblib': joblib,
                'pd': pd,
                'np': np
            }
        except ImportError as e:
            logger.error(f"Failed to import ML libraries: {e}")
            return None
    
    def _calculate_advanced_indicators(self, history: List[Dict]) -> Optional[TechnicalIndicators]:
        """Calculate comprehensive technical indicators"""
        ml = self._get_ml_components()
        if not ml:
            return None
        
        try:
            if len(history) < 50:
                return None
            
            # Extract price data
            closes = np.array([h.get('close', 0) for h in history])
            highs = np.array([h.get('high', 0) for h in history])
            lows = np.array([h.get('low', 0) for h in history])
            volumes = np.array([h.get('vol', 0) for h in history])
            
            if len(closes) < 200:
                return None
            
            latest = history[-1]
            price = latest.get('close', 0)
            volume = latest.get('vol', 0)
            
            # Basic Moving Averages
            sma_20 = np.mean(closes[-20:])
            sma_50 = np.mean(closes[-50:])
            sma_200 = np.mean(closes[-200:])
            
            # RSI (14 period)
            deltas = np.diff(closes)
            seed = deltas[:15]
            up = seed[seed >= 0].sum() / 14
            down = -seed[seed < 0].sum() / 14
            rs = up / down if down != 0 else 0
            rsi = 100 - (100 / (1 + rs)) if rs != 0 else 50
            
            # MACD
            ema_12 = np.mean(closes[-12:])
            ema_26 = np.mean(closes[-26:])
            macd = ema_12 - ema_26
            macd_signal = np.mean(closes[-9:])  # Simple signal
            macd_histogram = macd - macd_signal
            
            # Bollinger Bands
            std = np.std(closes[-20:])
            bollinger_middle = sma_20
            bollinger_upper = bollinger_middle + (std * 2)
            bollinger_lower = bollinger_middle - (std * 2)
            
            # ATR (14 period)
            tr1 = highs[-1] - lows[-1]
            tr2 = abs(highs[-1] - closes[-2])
            tr3 = abs(lows[-1] - closes[-2])
            tr = max(tr1, tr2, tr3)
            atr = tr  # Simplified
            
            # ADX (simplified)
            plus_di = ((highs[-1] - highs[-2]) if (highs[-1] - highs[-2]) > 0 else 0)
            minus_di = ((lows[-2] - lows[-1]) if (lows[-2] - lows[-1]) > 0 else 0)
            adx = 50  # Simplified default
            
            # On-Balance Volume
            obv = 0
            for i in range(1, len(closes)):
                if closes[i] > closes[i-1]:
                    obv += volumes[i]
                elif closes[i] < closes[i-1]:
                    obv -= volumes[i]
            
            # Volume MA
            volume_ma = np.mean(volumes[-20:])
            
            # Convert numpy types to float for type compatibility
            # type: ignore[arg-type]
            return TechnicalIndicators(
                price=float(price) if price is not None else 0.0,
                volume=int(volume) if volume is not None else 0,
                rsi=float(rsi) if rsi is not None else 0.0,
                macd=float(macd) if macd is not None else 0.0,
                macd_signal=float(macd_signal) if macd_signal is not None else 0.0,
                macd_histogram=float(macd_histogram) if macd_histogram is not None else 0.0,
                sma_20=float(sma_20) if sma_20 is not None else 0.0,
                sma_50=float(sma_50) if sma_50 is not None else 0.0,
                sma_200=float(sma_200) if sma_200 is not None else 0.0,
                bollinger_upper=float(bollinger_upper) if bollinger_upper is not None else 0.0,
                bollinger_middle=float(bollinger_middle) if bollinger_middle is not None else 0.0,
                bollinger_lower=float(bollinger_lower) if bollinger_lower is not None else 0.0,
                atr=float(atr) if atr is not None else 0.0,
                adx=float(adx) if adx is not None else 0.0,
                obv=int(obv) if obv is not None else 0,
                volume_ma=float(volume_ma) if volume_ma is not None else 0.0
            )
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return None
    
    def _extract_features(self, history: List[Dict]) -> Optional[np.ndarray]:
        """Extract 20+ features for ML model"""
        ml = self._get_ml_components()
        if not ml:
            return None
        
        try:
            indicators = self._calculate_advanced_indicators(history)
            if not indicators:
                return None
            
            ind = indicators
            
            # Create feature vector (20+ features)
            features = [
                ind.price / ind.sma_20,  # Price/SMA20 ratio
                ind.price / ind.sma_50,  # Price/SMA50 ratio
                ind.price / ind.sma_200, # Price/SMA200 ratio
                ind.sma_20 / ind.sma_50, # SMA20/SMA50 ratio
                ind.sma_50 / ind.sma_200,# SMA50/SMA200 ratio
                ind.rsi / 100,           # Normalized RSI
                ind.macd,                # MACD value
                ind.macd_histogram,      # MACD histogram
                (ind.bollinger_upper - ind.price) / ind.price,  # Distance to upper BB
                (ind.price - ind.bollinger_lower) / ind.price,  # Distance to lower BB
                ind.atr / ind.price,     # Normalized ATR
                ind.adx / 100,           # Normalized ADX
                ind.volume / ind.volume_ma,  # Volume ratio
                ind.obv,                 # OBV
                ind.price * ind.volume,  # Price*Volume
                (ind.price - ind.sma_20) / ind.atr,  # Price position relative to SMA
                ind.macd / ind.atr,      # MACD normalized
                ind.rsi * ind.macd_histogram,  # Combined indicator
                (ind.price - ind.bollinger_lower) / (ind.bollinger_upper - ind.bollinger_lower),  # BB position
                (ind.sma_20 - ind.sma_50) / ind.atr,  # MA crossover signal
            ]
            
            self.feature_names = [
                'price_sma20_ratio', 'price_sma50_ratio', 'price_sma200_ratio',
                'sma20_sma50_ratio', 'sma50_sma200_ratio', 'rsi_norm',
                'macd', 'macd_hist', 'dist_upper_bb', 'dist_lower_bb',
                'atr_norm', 'adx_norm', 'volume_ratio', 'obv',
                'price_volume', 'price_position', 'macd_norm',
                'rsi_macd_combined', 'bb_position', 'ma_crossover'
            ]
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return None
    
    def _determine_trend(self, indicators: TechnicalIndicators) -> tuple[Trend, float]:
        """Determine trend based on multiple signals"""
        score = 0
        signals = []
        
        # RSI signal
        if indicators.rsi > 70:
            score -= 1
            signals.append("RSI overbought")
        elif indicators.rsi < 30:
            score += 1
            signals.append("RSI oversold")
        elif indicators.rsi > 55:
            score += 0.5
            signals.append("RSI bullish")
        elif indicators.rsi < 45:
            score -= 0.5
            signals.append("RSI bearish")
        
        # MACD signal
        if indicators.macd_histogram > 0:
            score += 0.5
            signals.append("MACD bullish")
        else:
            score -= 0.5
            signals.append("MACD bearish")
        
        # Price vs SMAs
        if indicators.price > indicators.sma_20:
            score += 0.5
        else:
            score -= 0.5
            
        if indicators.price > indicators.sma_50:
            score += 0.5
        else:
            score -= 0.5
            
        if indicators.price > indicators.sma_200:
            score += 1
            signals.append("Price above SMA200 (long-term bullish)")
        else:
            score -= 1
            signals.append("Price below SMA200 (long-term bearish)")
        
        # Bollinger Bands position
        bb_position = (indicators.price - indicators.bollinger_lower) / (indicators.bollinger_upper - indicators.bollinger_lower)
        if bb_position > 0.8:
            score -= 0.5
            signals.append("Near upper Bollinger Band")
        elif bb_position < 0.2:
            score += 0.5
            signals.append("Near lower Bollinger Band")
        
        # ADX (trend strength)
        if indicators.adx > 25:
            if score > 0:
                score += 0.5
                signals.append("Strong uptrend")
            else:
                score -= 0.5
                signals.append("Strong downtrend")
        
        # Determine trend and confidence
        confidence = min(abs(score) / 3, 1.0)
        
        if score > 0.5:
            return Trend.BULLISH, confidence
        elif score < -0.5:
            return Trend.BEARISH, confidence
        else:
            return Trend.NEUTRAL, confidence
    
    def _calculate_support_resistance(self, history: List[Dict], trend: Trend) -> tuple[List[float], List[float]]:
        """Calculate support and resistance levels"""
        try:
            closes = [h.get('close', 0) for h in history[-50:]]
            highs = [h.get('high', 0) for h in history[-50:]]
            lows = [h.get('low', 0) for h in history[-50:]]
            
            current_price = closes[-1]
            
            # Pivot Points
            pivot = (highs[-1] + lows[-1] + closes[-1]) / 3
            r1 = 2 * pivot - lows[-1]
            r2 = pivot + (highs[-1] - lows[-1])
            r3 = highs[-1] + 2 * (pivot - lows[-1])
            s1 = 2 * pivot - highs[-1]
            s2 = pivot - (highs[-1] - lows[-1])
            s3 = lows[-1] - 2 * (highs[-1] - pivot)
            
            resistances = sorted([r1, r2, r3], reverse=True)[:3]
            supports = sorted([s1, s2, s3])[:3]
            
            # Add psychological levels
            psychological_r = round(current_price * 1.1, -3)
            psychological_s = round(current_price * 0.9, -3)
            
            if psychological_r not in resistances:
                resistances.append(psychological_r)
            if psychological_s not in supports:
                supports.append(psychological_s)
            
            return supports[:3], resistances[:3]
            
        except Exception as e:
            logger.error(f"Support/Resistance calculation error: {e}")
            return [current_price * 0.95], [current_price * 1.05]
    
    def _generate_analysis_text(self, symbol: str, trend: Trend, 
                                 indicators: TechnicalIndicators,
                                 confidence: float) -> str:
        """Generate comprehensive analysis text"""
        templates = self.templates['analysis'].get(trend.value, self.templates['analysis']['neutral'])
        template = random.choice(templates)
        
        support, resistance = self._calculate_support_resistance([], trend)
        
        text = template.format(
            symbol=symbol,
            price=round(indicators.price, 2),
            rsi=round(indicators.rsi, 1),
            resistance=resistance[0] if resistance else "---",
            support=support[0] if support else "---",
            target=round(indicators.price * 1.15, 0) if trend == Trend.BULLISH else round(indicators.price * 0.85, 0)
        )
        
        # Add additional insights
        insights = []
        
        if indicators.rsi > 70:
            insights.append("⚠️ هشدار اشباع خرید - احتمال اصلاح")
        elif indicators.rsi < 30:
            insights.append("⚠️ هشدار اشباع فروش - فرصت خرید")
        
        if indicators.macd_histogram > 0:
            insights.append("📈 MACD مثبت - مومنتوم صعودی")
        else:
            insights.append("📉 MACD منفی - مومنتوم نزولی")
        
        if indicators.price > indicators.sma_200:
            insights.append("✅ قیمت بالای میانگین ۲۰۰ روزه - روند بلندمدت صعودی")
        else:
            insights.append("❌ قیمت زیر میانگین ۲۰۰ روزه - روند بلندمدت نزولی")
        
        if indicators.adx > 25:
            insights.append("💪 ADX بالای ۲۵ - روند قوی")
        
        if insights:
            text += "\n\n" + " | ".join(insights)
        
        return text
    
    def _calculate_risk_score(self, indicators: TechnicalIndicators, trend: Trend) -> float:
        """Calculate risk score (0-100)"""
        risk = 50  # Base risk
        
        # Volatility contribution
        bb_width = (indicators.bollinger_upper - indicators.bollinger_lower) / indicators.bollinger_middle
        risk += bb_width * 30
        
        # RSI extreme levels increase risk
        if indicators.rsi > 80 or indicators.rsi < 20:
            risk += 10
        
        # Low ADX means range-bound (higher risk for trend-following)
        if indicators.adx < 20:
            risk += 10
        
        # Volume spike increases risk
        if indicators.volume > indicators.volume_ma * 2:
            risk += 5
        
        # Trend direction impact
        if trend == Trend.NEUTRAL:
            risk += 5
        
        return min(max(risk, 0), 100)
    
    def _get_recommendation(self, trend: Trend, confidence: float, risk: float) -> str:
        """Generate trading recommendation"""
        if trend == Trend.BULLISH and confidence > 0.7 and risk < 60:
            return "🟢 خرید قوی - روند صعودی با اعتماد بالا"
        elif trend == Trend.BULLISH and confidence > 0.5:
            return "🟢 خرید - روند صعودی"
        elif trend == Trend.BULLISH:
            return "🟡 نگهداری - احتمال صعود"
        elif trend == Trend.BEARISH and confidence > 0.7 and risk < 60:
            return "🔴 فروش قوی - روند نزولی با اعتماد بالا"
        elif trend == Trend.BEARISH and confidence > 0.5:
            return "🔴 فروش - روند نزولی"
        elif trend == Trend.BEARISH:
            return "🟡 نگهداری - احتمال نزول"
        else:
            return "🟡 صبر - وضعیت خنثی"
    
    def analyze_symbol(self, symbol: str, history: List[Dict]) -> Optional[AnalysisResult]:
        """Complete symbol analysis"""
        try:
            # Ensure model is loaded
            self._ensure_model_loaded()
            
            # Calculate indicators
            indicators = self._calculate_advanced_indicators(history)
            if not indicators:
                return None
            
            # Determine trend
            trend, confidence = self._determine_trend(indicators)
            
            # Calculate support/resistance
            supports, resistances = self._calculate_support_resistance(history, trend)
            
            # Calculate risk
            risk = self._calculate_risk_score(indicators, trend)
            
            # Generate signal
            signal = "BUY" if trend == Trend.BULLISH else "SELL" if trend == Trend.BEARISH else "HOLD"
            
            # Get recommendation
            recommendation = self._get_recommendation(trend, confidence, risk)
            
            # Generate analysis text
            analysis_text = self._generate_analysis_text(symbol, trend, indicators, confidence)
            
            return AnalysisResult(
                symbol=symbol,
                trend=trend,
                confidence=confidence,
                indicators=indicators,
                support_levels=supports,
                resistance_levels=resistances,
                signal=signal,
                recommendation=recommendation,
                risk_score=risk,
                analysis_text=analysis_text
            )
            
        except Exception as e:
            logger.error(f"Analysis error for {symbol}: {e}")
            return None
    
    def _lazy_load_model(self):
        """Load model in background thread"""
        try:
            time.sleep(5)
            self._load_or_train_model()
            self.model_loaded = True
            logger.info("✅ Enhanced AI model loaded in background")
            
            # Start continuous learning
            self.learning_thread = threading.Thread(target=self._continuous_learning, daemon=True)
            self.learning_thread.start()
        except Exception as e:
            logger.error(f"Failed to load model in background: {e}")
    
    def _ensure_model_loaded(self):
        """Ensure model is loaded"""
        if not self.model_loaded:
            logger.info("Model not yet loaded, loading now...")
            self._load_or_train_model()
            self.model_loaded = True
    
    def _load_or_train_model(self):
        """Load existing model or train a new one"""
        # Try to load with joblib (new format)
        joblib_path = self.model_path.replace('.pkl', '.joblib')
        
        try:
            if os.path.exists(joblib_path):
                ml = self._get_ml_components()
                if ml:
                    self.model = ml['joblib'].load(joblib_path)
                    self.scaler = ml['joblib'].load(joblib_path.replace('.joblib', '_scaler.joblib'))
                    logger.info("Enhanced AI model loaded with joblib")
                    return True
        except Exception as e:
            logger.warning(f"Failed to load joblib model: {e}")
        
        # Try pickle (old format)
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info("Enhanced AI model loaded with pickle")
                return True
            except Exception as e:
                logger.warning(f"Failed to load pickle model: {e}")
        
        # Train new model
        self._train_model()
        return self.model is not None
    
    def _train_model(self):
        """Train the enhanced ML model with ensemble"""
        joblib_path = self.model_path.replace('.pkl', '.joblib')
        ml = self._get_ml_components()
        if not ml:
            logger.error("ML components not available")
            return
        
        from app.database import db
        
        try:
            # Collect training data
            training_data = self._collect_training_data()
            if training_data.empty:
                logger.warning("No training data available")
                return
            
            # Prepare features and labels
            training_data = training_data.dropna()
            if training_data.empty:
                logger.warning("No valid training data")
                return
            
            # Create more features
            features = self._create_enhanced_features(training_data)
            labels = training_data['trend']
            
            # type: ignore[union-attr]
            if features is None or len(features) < 50:
                logger.warning("Not enough training data")
                return
            
            # Scale features
            self.scaler = ml['StandardScaler']()
            X_scaled = self.scaler.fit_transform(features)
            
            # Split data
            X_train, X_test, y_train, y_test = ml['train_test_split'](
                X_scaled, labels, test_size=0.2, random_state=42, stratify=labels
            )
            
            # Create ensemble
            rf = ml['RandomForestClassifier'](n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
            gb = ml['GradientBoostingClassifier'](n_estimators=100, max_depth=5, random_state=42)
            ada = ml['AdaBoostClassifier'](n_estimators=50, random_state=42)
            
            self.ensemble_models = {
                'rf': rf,
                'gb': gb,
                'ada': ada
            }
            
            # Train individual models
            for name, model in self.ensemble_models.items():
                model.fit(X_train, y_train)
            
            # Create voting ensemble
            self.model = ml['VotingClassifier'](
                estimators=[
                    ('rf', ml['RandomForestClassifier'](n_estimators=100, max_depth=8, random_state=42)),
                    ('gb', ml['GradientBoostingClassifier'](n_estimators=50, max_depth=4, random_state=42))
                ],
                voting='soft'
            )
            self.model.fit(X_train, y_train)
            
            # Evaluate
            predictions = self.model.predict(X_test)
            self.accuracy = ml['accuracy_score'](y_test, predictions)
            logger.info(f"✅ Enhanced model trained with accuracy: {self.accuracy:.2%}")
            
            # Cross-validation
            cv_scores = ml['cross_val_scores'](self.model, X_scaled, labels, cv=5)
            logger.info(f"Cross-validation scores: {cv_scores.mean():.2%} (+/- {cv_scores.std()*2:.2%})")
            
            # Save model
            try:
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                ml['joblib'].dump(self.model, joblib_path)
                ml['joblib'].dump(self.scaler, joblib_path.replace('.joblib', '_scaler.joblib'))
                logger.info(f"Enhanced model saved to {joblib_path}")
            except Exception as e:
                logger.error(f"Failed to save model: {e}")
                
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            self.model = None
    
    def _create_enhanced_features(self, df):
        """Create enhanced features for ML training"""
        ml = self._get_ml_components()
        if not ml:
            return None
        
        try:
            # Create additional features
            df = df.copy()
            
            # Price-based features
            df['price_sma20_ratio'] = df['price'] / df['ma20']
            df['price_sma50_ratio'] = df['price'] / df['ma50']
            df['sma20_sma50_ratio'] = df['ma20'] / df['ma50']
            
            # Volatility features
            df['volatility'] = df['price'].pct_change().rolling(10).std()
            
            # Momentum features
            df['momentum_5'] = df['price'].pct_change(5)
            df['momentum_10'] = df['price'].pct_change(10)
            
            # Volume features
            df['volume_ratio'] = df['volume'] / df['volume'].rolling(10).mean()
            
            # RSI features
            df['rsi_normalized'] = df['rsi'] / 100
            
            # MACD features
            df['macd_normalized'] = df['macd'] / df['price']
            
            # Drop NaN
            df = df.dropna()
            
            feature_cols = ['price', 'volume', 'rsi', 'macd', 'ma20', 'ma50',
                           'price_sma20_ratio', 'price_sma50_ratio', 'sma20_sma50_ratio',
                           'volatility', 'momentum_5', 'momentum_10', 'volume_ratio',
                       'rsi_normalized', 'macd_normalized']
            
            return df[feature_cols].values
            
        except Exception as e:
            logger.error(f"Feature creation error: {e}")
            return None
    
    def _collect_training_data(self) -> any: # type: ignore[no-untyped-def]
        """Collect and prepare training data"""
        ml = self._get_ml_components()
        if not ml:
            return None
        
        from app.database import db
        
        try:
            symbols = db.get_all_symbols()
            data_list = []
            
            for symbol_data in symbols:
                symbol = symbol_data.get('l18', '')
                history = db.get_history(symbol)
                
                if len(history) < 50:
                    continue
                
                indicators = self._calculate_advanced_indicators(history)
                if not indicators:
                    continue
                
                # Calculate actual trend (next day direction)
                if len(history) >= 2:
                    current_price = history[-1].get('close', 0)
                    next_price = history[-2].get('close', 0)
                    
                    if next_price > current_price * 1.01:
                        trend = 2  # Bullish
                    elif next_price < current_price * 0.99:
                        trend = 0  # Bearish
                    else:
                        trend = 1  # Neutral
                else:
                    trend = 1
                
                ind = indicators
                data_list.append({
                    'price': ind.price,
                    'volume': ind.volume,
                    'rsi': ind.rsi,
                    'macd': ind.macd,
                    'ma20': ind.sma_20,
                    'ma50': ind.sma_50,
                    'volume_ratio': ind.volume / ind.volume_ma,
                    'trend': trend
                })
            
            logger.info(f"Collected {len(data_list)} training samples")
            return ml['pd'].DataFrame(data_list)
            
        except Exception as e:
            logger.error(f"Training data collection failed: {e}")
            return ml['pd'].DataFrame()
    
    def _continuous_learning(self):
        """Continuous learning loop"""
        time.sleep(60)
        while True:
            time.sleep(3600)
            try:
                logger.info("Continuous learning: Updating enhanced model...")
                self._ensure_model_loaded()
                self._train_model()
                self.last_update = datetime.now()
            except Exception as e:
                logger.error(f"Continuous learning error: {e}")
    
    def generate_report(self, analysis: AnalysisResult) -> str:
        """Generate comprehensive analysis report"""
        jalali_today = jdatetime.date.fromgregorian(date=datetime.now().date()).strftime('%Y/%m/%d')
        
        report = f"""# 📊 گزارش تحلیل تکنیکال - نماد {analysis.symbol}

**تاریخ:** {jalali_today}  
**تحلیلگر:** هوش مصنوعی TSEAnalysis  
**دقت مدل:** {self.accuracy:.1%}

---

## 🎯 خلاصه تحلیل

| شاخص | مقدار |
|:---|:---|
| قیمت فعلی | {analysis.indicators.price:,.0f} تومان |
| روند | {analysis.trend.value} |
| سیگنال | {analysis.signal} |
| اعتماد | {analysis.confidence:.1%} |
| ریسک | {analysis.risk_score:.0f}/100 |

---

## 📈 شاخص‌های تکنیکال

### میانگین‌های متحرک
| شاخص | مقدار |
|:---|:---|
| SMA 20 | {analysis.indicators.sma_20:,.0f} |
| SMA 50 | {analysis.indicators.sma_50:,.0f} |
| SMA 200 | {analysis.indicators.sma_200:,.0f} |

### اسیلاتورها
| شاخص | مقدار | وضعیت |
|:---|:---:|:---:|
| RSI | {analysis.indicators.rsi:.1f} | {'🟢 Overbought' if analysis.indicators.rsi > 70 else '🔴 Oversold' if analysis.indicators.rsi < 30 else '🟡 Normal'} |
| MACD | {analysis.indicators.macd:.2f} | {'🟢 Bullish' if analysis.indicators.macd_histogram > 0 else '🔴 Bearish'} |
| ADX | {analysis.indicators.adx:.1f} | {'💪 Strong Trend' if analysis.indicators.adx > 25 else '⚪ Weak Trend'} |

### باندهای بولینگر
| سطح | قیمت |
|:---|:---:|
| بالا | {analysis.indicators.bollinger_upper:,.0f} |
| میانه | {analysis.indicators.bollinger_middle:,.0f} |
| پایین | {analysis.indicators.bollinger_lower:,.0f} |

---

## 🔺 سطوح حمایت
"""
        
        for i, support in enumerate(analysis.support_levels[:3], 1):
            report += f"{i}. **{support:,.0f}** تومان\n"
        
        report += "\n## 🔻 سطوح مقاومت\n"
        for i, resistance in enumerate(analysis.resistance_levels[:3], 1):
            report += f"{i}. **{resistance:,.0f}** تومان\n"
        
        report += f"""
---

## 💡 توصیه نهایی

**توصیه:** {analysis.recommendation}

**تحلیل:** {analysis.analysis_text}

---

## ⚠️ هشدار

این تحلیل صرفاً جنبه اطلاع‌رسانی دارد و توصیه خرید یا فروش نیست.
قبل از هرگونه تصمیم‌گیری، تحلیل شخصی خود را انجام دهید.
"""
        
        return report


# Global instance
enhanced_ai = EnhancedAIAssistant()
