"""
Autonomous AI Content Generator for TSE Analysis
- Fully offline, no external AI APIs
- Generates text content from site data
- Continuous learning from successful analyses
- Uses PDF books and educational documents as training data
"""

import os
import re
import json
import random
import threading
import logging
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class ContentType(Enum):
    ANALYSIS = "analysis"
    REPORT = "report"
    SUMMARY = "summary"
    NEWS = "news"
    ALERT = "alert"
    EDUCATIONAL = "educational"


@dataclass
class ContentTemplate:
    """Template for content generation"""
    template_id: str
    content_type: ContentType
    template: str
    variables: List[str]
    success_count: int = 0
    avg_rating: float = 0.0
    keywords: List[str] = field(default_factory=list)


@dataclass
class GeneratedContent:
    """Generated content with metadata"""
    content_id: str
    content_type: ContentType
    title: str
    body: str
    symbol: Optional[str]
    keywords: List[str]
    generated_at: datetime
    rating: float = 0.0
    view_count: int = 0
    was_helpful: bool = False


class KnowledgeBase:
    """
    Knowledge Base for AI Training
    Integrates with Training Data Extractor
    """
    
    def __init__(self, data_dir: str = "data/knowledge"):
        self.data_dir = data_dir
        self.chunks = []
        self.documents = {}
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load knowledge base from files"""
        chunks_file = os.path.join(self.data_dir, "chunks.json")
        
        if os.path.exists(chunks_file):
            try:
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    self.chunks = json.load(f)
                logger.info(f"Loaded {len(self.chunks)} knowledge chunks")
            except Exception as e:
                logger.warning(f"Failed to load knowledge base: {e}")
    
    def search(self, query: str, top_k: int = 3) -> List[str]:
        """Search knowledge base for relevant content"""
        query_keywords = self._extract_keywords(query)
        
        # Score chunks by keyword match
        scored_chunks = []
        for chunk in self.chunks:
            content_keywords = self._extract_keywords(chunk.get('content', ''))
            
            # Calculate similarity
            overlap = set(query_keywords) & set(content_keywords)
            score = len(overlap) / max(len(query_keywords), 1)
            
            scored_chunks.append((score, chunk))
        
        # Sort by score
        scored_chunks.sort(key=lambda x: -x[0])
        
        # Return top results
        return [chunk['content'] for score, chunk in scored_chunks[:top_k] if score > 0]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Financial keywords
        keywords = [
            'بورس', 'سهام', 'شاخص', 'قیمت', 'حجم', 'معامله',
            'خرید', 'فروش', 'سود', 'ضرر', 'ریسک', 'بازده',
            'RSI', 'MACD', 'Bollinger', 'میانگین', 'متحرک',
            'حمایت', 'مقاومت', 'روند', 'الگو', 'کندل', 'شمعی',
            'تحلیل', 'تکنیکال', 'بنیادی', 'نمودار', 'تایم',
            'سهامدار', 'شرکت', 'صنعت', 'بازار', 'سرمایه'
        ]
        
        text_lower = text.lower()
        found = [kw for kw in keywords if kw.lower() in text_lower]
        
        return found
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        return {
            'total_chunks': len(self.chunks),
            'chunk_types': self._count_types(),
            'topics': self._extract_all_topics()
        }
    
    def _count_types(self) -> Dict[str, int]:
        """Count chunks by type"""
        types = defaultdict(int)
        for chunk in self.chunks:
            types[chunk.get('chunk_type', 'unknown')] += 1
        return dict(types)
    
    def _extract_all_topics(self) -> List[str]:
        """Extract all unique topics"""
        topics = set()
        for chunk in self.chunks:
            topics.add(chunk.get('topic', ''))
        return sorted(list(topics))


class PersianNLP:
    """
    Persian Natural Language Processing utilities
    Fully offline, no external APIs
    """
    
    # Persian punctuation and characters
    PERSIAN_NUMBERS = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    
    PERSIAN_LETTERS = {
        'ي': 'ی', 'ك': 'ک', 'ة': 'ه', 'ۀ': 'ه',
        'ؤ': 'و', 'إ': 'ا', 'أ': 'ا', 'آ': 'ا'
    }
    
    # Sentiment words
    POSITIVE_WORDS = {
        'صعودی', 'positive', 'bullish', 'خرید', 'رشد', 'سود',
        'بالا', 'قدرت', 'مثبت', 'افزایش', 'فرصت', 'استحکام',
        'پایدار', 'سالم', 'مؤثر', 'موفق', 'بهبود'
    }
    
    NEGATIVE_WORDS = {
        'نزولی', 'negative', 'bearish', 'فروش', 'کاهش', 'ضرر',
        'پایین', 'ضعف', 'منفی', 'کاهش', 'خطر', 'ریسک',
        'نوسان', 'بحران', 'افت', 'هشدار', 'زیان'
    }
    
    NEUTRAL_WORDS = {
        'خنثی', 'neutral', 'رنج', 'ثابت', 'متوسط', 'normal',
        'حالت', 'انتظار', 'صبر', 'ماندن'
    }
    
    @staticmethod
    def normalize(text: str) -> str:
        """Normalize Persian text"""
        if not text:
            return ""
        
        # Convert Persian numbers to Latin
        for persian, latin in PersianNLP.PERSIAN_NUMBERS.items():
            text = text.replace(persian, latin)
        
        # Normalize Persian characters
        for wrong, correct in PersianNLP.PERSIAN_LETTERS.items():
            text = text.replace(wrong, correct)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def analyze_sentiment(text: str) -> Dict[str, float | str]:
        """Analyze sentiment of text (returns scores 0-1)"""
        text = PersianNLP.normalize(text).lower()
        
        words = text.split()
        
        positive_count = sum(1 for w in words if w in PersianNLP.POSITIVE_WORDS)
        negative_count = sum(1 for w in words if w in PersianNLP.NEGATIVE_WORDS)
        neutral_count = sum(1 for w in words if w in PersianNLP.NEUTRAL_WORDS)
        
        total = len(words) or 1
        
        return {
            'positive': positive_count / total,
            'negative': negative_count / total,
            'neutral': neutral_count / total,
            'overall': 'positive' if positive_count > negative_count else 'negative' if negative_count > positive_count else 'neutral'
        }
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        # Common words to ignore
        stopwords = {
            'و', 'در', 'به', 'از', 'که', 'برای', 'این', 'آن', 'با', 'یا',
            'است', 'بود', 'شد', 'دارد', 'های', 'ای', 'را', 'هم', 'چه',
            'کند', 'بگیرید', 'کنید', 'شود', 'اینکه', 'بهتر', 'بیشتر'
        }
        
        words = PersianNLP.normalize(text).split()
        keywords = [w for w in words if len(w) > 2 and w not in stopwords]
        
        # Count frequency
        freq = defaultdict(int)
        for word in keywords:
            freq[word] += 1
        
        # Sort by frequency
        sorted_keywords = sorted(freq.items(), key=lambda x: -x[1])
        
        return [k for k, _ in sorted_keywords[:max_keywords]]
    
    @staticmethod
    def generate_summary(text: str, max_length: int = 200) -> str:
        """Generate a short summary of text"""
        # Simple extractive summarization
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return text[:max_length]
        
        # Score sentences by keyword presence
        keywords = PersianNLP.extract_keywords(text, 10)
        
        scored_sentences = []
        for sentence in sentences:
            score = sum(1 for kw in keywords if kw in sentence.lower())
            scored_sentences.append((score, sentence))
        
        scored_sentences.sort(key=lambda x: -x[0])
        
        summary = '. '.join(s[1] for s in scored_sentences[:3])
        
        if len(summary) > max_length:
            summary = summary[:max_length] + '...'
        
        return summary
    
    @staticmethod
    def format_number(num: float, currency: bool = True) -> str:
        """Format number in Persian style"""
        if currency:
            return f"{int(num):,} تومان"
        return f"{num:,.2f}"
    
    @staticmethod
    def format_percentage(num: float) -> str:
        """Format percentage in Persian style"""
        return f"{num:.2f}%"
    
    @staticmethod
    def format_date(date: datetime) -> str:
        """Format date in Persian style"""
        jalali = PersianNLP.to_jalali(date)
        return jalali.strftime('%Y/%m/%d')
    
    @staticmethod
    def to_jalali(date: datetime):
        """Convert Gregorian to Jalali date"""
        try:
            import jdatetime
            return jdatetime.date.fromgregorian(date=date)
        except ImportError:
            return date


class ContentGenerator:
    """
    Autonomous Content Generator
    Generates all text content from site data
    """
    
    def __init__(self, data_dir: str = "data/content"):
        self.data_dir = data_dir
        self.templates = self._load_templates()
        self.content_history = self._load_content_history()
        self.keyword_index = self._build_keyword_index()
        self.nlp = PersianNLP()
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
    
    def _load_templates(self) -> Dict[str, ContentTemplate]:
        """Load content templates"""
        templates = {}
        
        # Analysis templates
        templates['analysis_bullish'] = ContentTemplate(
            template_id='analysis_bullish',
            content_type=ContentType.ANALYSIS,
            template="""
## 📈 تحلیل نماد {symbol}

### خلاصه وضعیت
نماد {symbol} در روند **صعودی** قرار دارد. قیمت فعلی {price} با مومنتوم مثبت همراه است.

### شاخص‌های کلیدی
- **RSI**: {rsi} - وضعیت: {rsi_status}
- **MACD**: {macd} - {macd_status}
- **روند قیمت**: {price_trend}

### حمایت و مقاومت
- **حمایت‌ها**: {supports}
- **مقاومت‌ها**: {resistances}

### توصیه
🎯 **{recommendation}**

### تحلیل تکمیلی
{analysis_text}
            """,
            variables=['symbol', 'price', 'rsi', 'macd', 'price_trend', 
                      'supports', 'resistances', 'recommendation', 'analysis_text',
                      'rsi_status', 'macd_status']
        )
        
        templates['analysis_bearish'] = ContentTemplate(
            template_id='analysis_bearish',
            content_type=ContentType.ANALYSIS,
            template="""
## 📉 تحلیل نماد {symbol}

### خلاصه وضعیت
نماد {symbol} در روند **نزولی** قرار دارد. قیمت فعلی {price} نشان‌دهنده ضعف در بازار است.

### شاخص‌های کلیدی
- **RSI**: {rsi} - وضعیت: {rsi_status}
- **MACD**: {macd} - {macd_status}
- **روند قیمت**: {price_trend}

### حمایت و مقاومت
- **حمایت‌ها**: {supports}
- **مقاومت‌ها**: {resistances}

### توصیه
🎯 **{recommendation}**

### تحلیل تکمیلی
{analysis_text}
            """,
            variables=['symbol', 'price', 'rsi', 'macd', 'price_trend', 
                      'supports', 'resistances', 'recommendation', 'analysis_text',
                      'rsi_status', 'macd_status']
        )
        
        templates['analysis_neutral'] = ContentTemplate(
            template_id='analysis_neutral',
            content_type=ContentType.ANALYSIS,
            template="""
## ➡️ تحلیل نماد {symbol}

### خلاصه وضعیت
نماد {symbol} در فاز **خنثی** قرار دارد. قیمت فعلی {price} است.

### شاخص‌های کلیدی
- **RSI**: {rsi} - وضعیت: {rsi_status}
- **MACD**: {macd} - {macd_status}
- **روند قیمت**: {price_trend}

### حمایت و مقاومت
- **حمایت‌ها**: {supports}
- **مقاومت‌ها**: {resistances}

### توصیه
🎯 **{recommendation}**

### تحلیل تکمیلی
{analysis_text}
            """,
            variables=['symbol', 'price', 'rsi', 'macd', 'price_trend', 
                      'supports', 'resistances', 'recommendation', 'analysis_text',
                      'rsi_status', 'macd_status']
        )
        
        # Summary template
        templates['market_summary'] = ContentTemplate(
            template_id='market_summary',
            content_type=ContentType.SUMMARY,
            template="""
# 📊 خلاصه وضعیت بازار - {date}

## overview
بورس تهران در تاریخ {date} با وضعیت **{market_status}** همراه بود.

### آمار کلی
- **تعداد نمادها**: {total_symbols}
- **نمادهای صعودی**: {bullish_count}
- **نمادهای نزولی**: {bearish_count}
- **نمادهای خنثی**: {neutral_count}

### نمادهای برتر
**بیشترین رشد:**
{top_gainers}

**بیشترین کاهش:**
{top_losers}

### تحلیل کلی
{overall_analysis}
            """,
            variables=['date', 'market_status', 'total_symbols', 'bullish_count',
                      'bearish_count', 'neutral_count', 'top_gainers', 'top_losers',
                      'overall_analysis']
        )
        
        # News template
        templates['market_news'] = ContentTemplate(
            template_id='market_news',
            content_type=ContentType.NEWS,
            template="""
# 📰 اخبار بازار - {date}

## رویدادهای مهم
{events}

## تحلیل اخبار
{news_analysis}
            """,
            variables=['date', 'events', 'news_analysis']
        )
        
        # Educational template
        templates['educational'] = ContentTemplate(
            template_id='educational',
            content_type=ContentType.EDUCATIONAL,
            template="""
# 📚 آموزش: {title}

## مقدمه
{introduction}

## توضیحات اصلی
{main_content}

## نکات کلیدی
{key_points}

## نتیجه‌گیری
{conclusion}

---
*این مطلب صرفاً جنبه آموزشی دارد و توصیه سرمایه‌گذاری نیست.*
            """,
            variables=['title', 'introduction', 'main_content', 'key_points', 'conclusion']
        )
        
        # Alert template
        templates['alert'] = ContentTemplate(
            template_id='alert',
            content_type=ContentType.ALERT,
            template="""
# ⚠️ هشدار: {alert_title}

## وضعیت
{alert_status}

## توضیحات
{alert_description}

## اقدامات پیشنهادی
{recommended_actions}

**تاریخ انتشار**: {publish_date}
            """,
            variables=['alert_title', 'alert_status', 'alert_description', 
                      'recommended_actions', 'publish_date']
        )
        
        return templates
    
    def _load_content_history(self) -> Dict[str, List[GeneratedContent]]:
        """Load content history for learning"""
        history_file = os.path.join(self.data_dir, "content_history.pkl")
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load content history: {e}")
        
        return {ct.value: [] for ct in ContentType}
    
    def _save_content_history(self):
        """Save content history"""
        history_file = os.path.join(self.data_dir, "content_history.pkl")
        
        try:
            with open(history_file, 'wb') as f:
                pickle.dump(self.content_history, f)
        except Exception as e:
            logger.error(f"Failed to save content history: {e}")
    
    def _build_keyword_index(self) -> Dict[str, List[str]]:
        """Build keyword index for fast lookup"""
        index = defaultdict(list)
        
        for template_id, template in self.templates.items():
            for keyword in template.keywords:
                index[keyword].append(template_id)
        
        return dict(index)
    
    def generate_analysis(self, symbol: str, trend: str, 
                          indicators: Dict, 
                          supports: List[float],
                          resistances: List[float],
                          recommendation: str,
                          analysis_text: str) -> GeneratedContent:
        """Generate analysis content"""
        
        # Select template based on trend
        template_id = f"analysis_{trend.lower()}"
        if template_id not in self.templates:
            template_id = 'analysis_neutral'
        
        template = self.templates[template_id]
        
        # Prepare variables
        price = indicators.get('price', 0)
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', 0)
        
        # RSI status
        if rsi > 70:
            rsi_status = "🟢 اشباع خرید"
        elif rsi < 30:
            rsi_status = "🔴 اشباع فروش"
        else:
            rsi_status = "🟡 خنثی"
        
        # MACD status
        macd_status = "📈 صعودی" if indicators.get('macd_histogram', 0) > 0 else "📉 نزولی"
        
        # Price trend
        if trend.upper() == 'BULLISH':
            price_trend = "افزایشی"
        elif trend.upper() == 'BEARISH':
            price_trend = "کاهشی"
        else:
            price_trend = "رنج"
        
        variables = {
            'symbol': symbol,
            'price': self.nlp.format_number(price),
            'rsi': self.nlp.format_percentage(rsi),
            'macd': f"{macd:.2f}",
            'rsi_status': rsi_status,
            'macd_status': macd_status,
            'price_trend': price_trend,
            'supports': ', '.join(self.nlp.format_number(s) for s in supports[:3]),
            'resistances': ', '.join(self.nlp.format_number(r) for r in resistances[:3]),
            'recommendation': recommendation,
            'analysis_text': analysis_text
        }
        
        # Generate content
        body = template.template
        for var, value in variables.items():
            body = body.replace(f'{{{var}}}', str(value))
        
        # Clean up extra whitespace
        body = re.sub(r'\n{3,}', '\n\n', body)
        body = body.strip()
        
        # Extract keywords
        keywords = self.nlp.extract_keywords(body, 10)
        
        # Create content ID
        content_id = hashlib.md5(f"{symbol}{trend}{datetime.now()}".encode()).hexdigest()[:12]
        
        content = GeneratedContent(
            content_id=content_id,
            content_type=ContentType.ANALYSIS,
            title=f"تحلیل تکنیکال نماد {symbol} - {self.nlp.format_date(datetime.now())}",
            body=body,
            symbol=symbol,
            keywords=keywords,
            generated_at=datetime.now()
        )
        
        # Save to history
        self.content_history[ContentType.ANALYSIS.value].append(content)
        self._save_content_history()
        
        # Update template success
        template.success_count += 1
        
        return content
    
    def generate_market_summary(self, stats: Dict) -> GeneratedContent:
        """Generate daily market summary"""
        
        template = self.templates['market_summary']
        
        total = stats.get('total_symbols', 0)
        bullish = stats.get('bullish_count', 0)
        bearish = stats.get('bearish_count', 0)
        neutral = stats.get('neutral_count', 0)
        
        # Determine market status
        if bullish > bearish * 1.5:
            market_status = "صعودی"
        elif bearish > bullish * 1.5:
            market_status = "نزولی"
        else:
            market_status = "خنثی"
        
        # Overall analysis
        if market_status == "صعودی":
            overall = "بازار با قدرت در حال صعود است. اکثر نمادها روند مثبتی دارند."
        elif market_status == "نزولی":
            overall = "بازار تحت فشار فروش است. اکثر نمادها روند منفی دارند."
        else:
            overall = "بازار در تعادل قرار دارد. نمادهای مختلف روندهای متفاوتی دارند."
        
        variables = {
            'date': self.nlp.format_date(datetime.now()),
            'market_status': market_status,
            'total_symbols': total,
            'bullish_count': bullish,
            'bearish_count': bearish,
            'neutral_count': neutral,
            'top_gainers': stats.get('top_gainers', 'اطلاعات موجود نیست'),
            'top_losers': stats.get('top_losers', 'اطلاعات موجود نیست'),
            'overall_analysis': overall
        }
        
        body = template.template
        for var, value in variables.items():
            body = body.replace(f'{{{var}}}', str(value))
        
        body = re.sub(r'\n{3,}', '\n\n', body)
        body = body.strip()
        
        keywords = self.nlp.extract_keywords(body, 10)
        
        content_id = hashlib.md5(f"summary{datetime.now()}".encode()).hexdigest()[:12]
        
        content = GeneratedContent(
            content_id=content_id,
            content_type=ContentType.SUMMARY,
            title=f"خلاصه وضعیت بازار - {self.nlp.format_date(datetime.now())}",
            body=body,
            symbol=None,
            keywords=keywords,
            generated_at=datetime.now()
        )
        
        self.content_history[ContentType.SUMMARY.value].append(content)
        self._save_content_history()
        
        return content
    
    def generate_educational(self, title: str, topic: str, 
                             content: str) -> GeneratedContent:
        """Generate educational content"""
        
        template = self.templates['educational']
        
        # Extract key points
        sentences = re.split(r'[.!?]', content)
        key_points = [s.strip() for s in sentences if len(s.strip()) > 30][:5]
        
        variables = {
            'title': title,
            'introduction': f"در این مطلب به بررسی موضوع {topic} می‌پردازیم.",
            'main_content': content,
            'key_points': '\n'.join(f"- {kp}" for kp in key_points),
            'conclusion': f"امیدواریم این مطلب درباره {topic} برای شما مفید بوده باشد."
        }
        
        body = template.template
        for var, value in variables.items():
            body = body.replace(f'{{{var}}}', str(value))
        
        body = re.sub(r'\n{3,}', '\n\n', body)
        body = body.strip()
        
        keywords = self.nlp.extract_keywords(body, 10)
        
        content_id = hashlib.md5(f"edu{title}{datetime.now()}".encode()).hexdigest()[:12]
        
        # type: ignore[assignment]
        generated_content = GeneratedContent(
            content_id=content_id,
            content_type=ContentType.EDUCATIONAL,
            title=f"📚 آموزش: {title}",
            body=body,
            symbol=None,
            keywords=keywords,
            generated_at=datetime.now()
        )
        
        # type: ignore[arg-type]
        self.content_history[ContentType.EDUCATIONAL.value].append(generated_content)
        self._save_content_history()
        
        # type: ignore[return-value]
        return generated_content
    
    def rate_content(self, content_id: str, rating: float, was_helpful: bool):
        """Rate generated content for learning"""
        for content_list in self.content_history.values():
            for content in content_list:
                if content.content_id == content_id:
                    content.rating = rating
                    content.was_helpful = was_helpful
                    self._save_content_history()
                    return True
        return False
    
    def get_popular_content(self, content_type: Optional[ContentType] = None, 
                           limit: int = 10) -> List[GeneratedContent]:
        """Get most popular/viewed content"""
        if content_type:
            contents = self.content_history.get(content_type.value, [])
        else:
            contents = [c for lst in self.content_history.values() for c in lst]
        
        return sorted(contents, key=lambda x: -x.view_count)[:limit]
    
    def get_best_rated_content(self, content_type: Optional[ContentType] = None,
                              min_ratings: int = 5,
                              limit: int = 10) -> List[GeneratedContent]:
        """Get highest rated content"""
        if content_type:
            contents = self.content_history.get(content_type.value, [])
        else:
            contents = [c for lst in self.content_history.values() for c in lst]
        
        filtered = [c for c in contents if c.rating >= 4.0 and c.rating > 0]
        return sorted(filtered, key=lambda x: -x.rating)[:limit]


class ContinuousLearning:
    """
    Continuous Learning System
    Learns from site data, user feedback, and analysis results
    """
    
    def __init__(self, data_dir: str = "data/learning"):
        self.data_dir = data_dir
        self.learned_patterns = self._load_patterns()
        self.successful_phrases = self._load_phrases()
        self.user_feedback = self._load_feedback()
        
        os.makedirs(data_dir, exist_ok=True)
        
        # Start learning thread
        self._start_learning_thread()
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load learned patterns"""
        patterns_file = os.path.join(self.data_dir, "patterns.pkl")
        
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")
        
        return {
            'successful_intros': [],
            'successful_phrases': defaultdict(list),
            'trend_correlations': {},
            'phrase_effectiveness': defaultdict(float)
        }
    
    def _save_patterns(self):
        """Save learned patterns"""
        patterns_file = os.path.join(self.data_dir, "patterns.pkl")
        
        try:
            with open(patterns_file, 'wb') as f:
                pickle.dump(self.learned_patterns, f)
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def _load_phrases(self) -> Dict[str, List[str]]:
        """Load successful phrases"""
        phrases_file = os.path.join(self.data_dir, "phrases.pkl")
        
        if os.path.exists(phrases_file):
            try:
                with open(phrases_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load phrases: {e}")
        
        return defaultdict(list)
    
    def _save_phrases(self):
        """Save successful phrases"""
        phrases_file = os.path.join(self.data_dir, "phrases.pkl")
        
        try:
            with open(phrases_file, 'wb') as f:
                pickle.dump(self.successful_phrases, f)
        except Exception as e:
            logger.error(f"Failed to save phrases: {e}")
    
    def _load_feedback(self) -> List[Dict]:
        """Load user feedback"""
        feedback_file = os.path.join(self.data_dir, "feedback.json")
        
        if os.path.exists(feedback_file):
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load feedback: {e}")
        
        return []
    
    def _save_feedback(self):
        """Save user feedback"""
        feedback_file = os.path.join(self.data_dir, "feedback.json")
        
        try:
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_feedback, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
    
    def _start_learning_thread(self):
        """Start continuous learning thread"""
        def learning_loop():
            while True:
                try:
                    # Learn from feedback every hour
                    self._analyze_feedback()
                    self._update_patterns()
                    self._save_patterns()
                    self._save_phrases()
                except Exception as e:
                    logger.error(f"Learning error: {e}")
                
                # Sleep for 1 hour
                import time
                time.sleep(3600)
        
        thread = threading.Thread(target=learning_loop, daemon=True)
        thread.start()
    
    def _analyze_feedback(self):
        """Analyze user feedback to learn"""
        # Group feedback by content type
        by_type = defaultdict(list)
        for feedback in self.user_feedback:
            by_type[feedback.get('content_type', 'unknown')].append(feedback)
        
        # Analyze which phrases work best
        for content_type, feedbacks in by_type.items():
            # High rated content
            high_rated = [f for f in feedbacks if f.get('rating', 0) >= 4]
            
            # Extract patterns
            for feedback in high_rated:
                if 'phrases' in feedback:
                    for phrase in feedback['phrases']:
                        self.learned_patterns['phrase_effectiveness'][phrase] += 0.1
    
    def _update_patterns(self):
        """Update learned patterns"""
        # Update successful intro patterns
        successful_intros = self.learned_patterns['successful_intros']
        
        # Add new patterns from successful content
        # This would analyze high-rated content to extract patterns
    
    def record_feedback(self, content_id: str, content_type: str, 
                        rating: float, was_helpful: bool,
                        user_comment: Optional[str] = None):
        """Record user feedback"""
        feedback = {
            'content_id': content_id,
            'content_type': content_type,
            'rating': rating,
            'was_helpful': was_helpful,
            'comment': user_comment,
            'timestamp': datetime.now().isoformat()
        }
        
        self.user_feedback.append(feedback)
        self._save_feedback()
    
    def get_learning_stats(self) -> Dict:
        """Get learning statistics"""
        return {
            'total_feedback': len(self.user_feedback),
            'avg_rating': sum(f.get('rating', 0) for f in self.user_feedback) / len(self.user_feedback) if self.user_feedback else 0,
            'helpful_count': sum(1 for f in self.user_feedback if f.get('was_helpful')),
            'patterns_count': len(self.learned_patterns.get('successful_intros', [])),
            'phrases_count': sum(len(v) for v in self.successful_phrases.values())
        }


# Global instances
content_generator = ContentGenerator()
continuous_learning = ContinuousLearning()
