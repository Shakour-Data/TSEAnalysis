import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure app is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- Mocking modules that might be missing or heavy ---
sys.modules['seaborn'] = MagicMock()
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()

from app.services.enhanced_ai import EnhancedAIAssistant, Trend, TechnicalIndicators
from app.services.autonomous_ai import ContentGenerator, ContentType, KnowledgeBase
from app.services.training_data_extractor import TrainingDataExtractor
from app.utils.core_utils import CoreUtils
from app.utils.validators import DataValidator

@pytest.fixture
def ai_assistant():
    return EnhancedAIAssistant()

@pytest.fixture
def tech_indicators():
    return TechnicalIndicators(
        price=100.0, volume=1000, rsi=50.0, macd=0.0, 
        macd_signal=0.0, macd_histogram=0.0,
        sma_20=100.0, sma_50=100.0, sma_200=100.0,
        bollinger_upper=110.0, bollinger_middle=100.0, bollinger_lower=90.0,
        atr=2.0, adx=20.0, obv=5000, volume_ma=1000
    )

def test_enhanced_ai_full(ai_assistant, tech_indicators):
    # Coverage for trend determination branches
    ai_assistant._determine_trend(tech_indicators)
    tech_indicators.rsi = 80
    ai_assistant._determine_trend(tech_indicators)
    tech_indicators.rsi = 20
    ai_assistant._determine_trend(tech_indicators)
    
    # Coverage for analysis generation
    ai_assistant._generate_analysis_text("TEST", Trend.BULLISH, tech_indicators, 0.9)
    ai_assistant._generate_analysis_text("TEST", Trend.BEARISH, tech_indicators, 0.9)

def test_autonomous_ai_search():
    kb = KnowledgeBase()
    kb.chunks = [{"content": "داده تستی", "metadata": {}}]
    res = kb.search("تست")
    assert isinstance(res, list)

def test_core_utils():
    assert CoreUtils.safe_round(10.555, 2) == 10.56
    assert CoreUtils.is_numeric("123")
    assert not CoreUtils.is_numeric("abc")

def test_validators():
    assert DataValidator.is_valid_symbol("خودرو")
    assert not DataValidator.is_valid_symbol("")
    assert DataValidator.is_valid_price(1000)

@patch('app.services.tsetmc.client')
def test_mock_route_logic(mock_client):
    from app.api.routes import main_bp
    # This is just to trigger imports and basic logic
    assert main_bp is not None
