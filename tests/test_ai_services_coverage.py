import pytest
import os
from unittest.mock import MagicMock, patch
from app.services.enhanced_ai import EnhancedAIAssistant, Trend, TechnicalIndicators
from app.services.autonomous_ai import ContentGenerator, ContentType, KnowledgeBase
from app.services.training_data_extractor import TrainingDataExtractor

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

def test_enhanced_ai_logic(ai_assistant, tech_indicators):
    # Test trend determination
    trend, conf = ai_assistant._determine_trend(tech_indicators)
    assert isinstance(trend, Trend)
    assert 0 <= conf <= 1.0
    
    # Test bullish signals
    tech_indicators.rsi = 35.0
    tech_indicators.price = 105.0
    trend, _ = ai_assistant._determine_trend(tech_indicators)
    
    # Test bearish signals
    tech_indicators.rsi = 75.0
    tech_indicators.price = 95.0
    trend, _ = ai_assistant._determine_trend(tech_indicators)

def test_autonomous_ai_knowledge(tmp_path):
    kb_dir = tmp_path / "knowledge"
    kb_dir.mkdir()
    kb = KnowledgeBase(data_dir=str(kb_dir))
    
    # Mock some chunks
    kb.chunks = [
        {"content": "آموزش بورس و تحلیل تکنیکال برای مبتدیان", "metadata": {"source": "book1"}},
        {"content": "اندیکاتور RSI و کاربرد آن در اشباع خرید", "metadata": {"source": "book2"}}
    ]
    
    results = kb.search("RSI")
    assert len(results) > 0
    assert "RSI" in results[0]

def test_content_generator():
    generator = ContentGenerator()
    assert generator is not None

def test_training_extractor(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    extractor = TrainingDataExtractor(docs_dir=str(docs_dir), data_dir=str(data_dir))
    assert extractor.docs_dir == str(docs_dir)
    
    # Test basic utility methods in extractor
    clean_text = extractor._clean_text("  متن  نمونه \n ")  # type: ignore[attr-defined]
    assert "متن" in clean_text
    assert "\n" not in clean_text
