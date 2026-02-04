"""
Training Data Extractor
- Extracts text from PDF files
- Parses markdown documentation
- Scrapes educational websites
- Creates knowledge base for AI training

Dependencies:
    - PyPDF2>=3.0.0 (PDF text extraction)
    - pdfplumber>=0.10.0 (Advanced PDF extraction)
    - beautifulsoup4>=4.9.0 (HTML parsing)
    - lxml>=4.6.0 (HTML/XML parser)

Installation:
    pip install PyPDF2 pdfplumber beautifulsoup4 lxml

For Python 3.8+ compatibility:
    pip install "PyPDF2<4.0" "pdfplumber<0.11" "beautifulsoup4<4.12"
"""

import os
import re
import json
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import hashlib

# Optional imports with graceful fallback
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    pdfplumber = None

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    PyPDF2 = None

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    BeautifulSoup = None

try:
    import lxml
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    lxml = None

logger = logging.getLogger(__name__)

# Explicit exports
__all__ = [
    'PDFExtractor',
    'EducationalWebScraper',
    'TrainingDataExtractor',
    'TrainingDataPipeline',
    'WebScraper',
    'MarkdownParser',
    'KnowledgeBaseBuilder',
    'TrainingDocument',
    'KnowledgeChunk',
    'PDFPLUMBER_AVAILABLE',
    'PYPDF2_AVAILABLE',
    'BS4_AVAILABLE',
    'LXML_AVAILABLE',
]

@dataclass
class TrainingDocument:
    """Training document extracted from source"""
    doc_id: str
    title: str
    source_type: str  # pdf, markdown, web
    source_path: str
    content: str
    extracted_at: datetime
    keywords: List[str] = field(default_factory=list)
    quality_score: float = 0.0


@dataclass
class KnowledgeChunk:
    """Knowledge chunk for AI training"""
    chunk_id: str
    document_id: str
    content: str
    chunk_type: str  # concept, definition, example, explanation
    topic: str
    confidence: float
    related_topics: List[str] = field(default_factory=list)


class PDFExtractor:
    """
    Extract text from PDF files
    Supports both text-based and OCR PDFs
    """
    
    def __init__(self, pdf_dir: str = "docs"):
        self.pdf_dir = pdf_dir
    
    @property
    def pdfplumber_available(self) -> bool:
        """Check if pdfplumber is available"""
        return PDFPLUMBER_AVAILABLE
    
    @property
    def pdf_available(self) -> bool:
        """Check if PyPDF2 is available"""
        return PYPDF2_AVAILABLE
    
    def find_pdfs(self) -> List[str]:
        """Find all PDF files in the directory"""
        pdf_files = []
        
        if not os.path.exists(self.pdf_dir):
            logger.warning(f"PDF directory not found: {self.pdf_dir}")
            return pdf_files
        
        for root, dirs, files in os.walk(self.pdf_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        return pdf_files
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from a single PDF file"""
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return ""
        
        text = ""
        
        # Try pdfplumber first (better extraction)
        if self.pdfplumber_available and pdfplumber is not None:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
                logger.info(f"Extracted {len(text)} characters from {pdf_path}")
                return text
            except Exception as e:
                logger.warning(f"pdfplumber failed for {pdf_path}: {e}")
        
        # Fallback to PyPDF2
        if self.pdf_available and PyPDF2 is not None:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
                logger.info(f"Extracted {len(text)} characters from {pdf_path}")
                return text
            except Exception as e:
                logger.error(f"PyPDF2 failed for {pdf_path}: {e}")
        
        return text
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content using simple NLP"""
        import re
        # Remove special characters and split into words
        words = re.findall(r'\b[a-zA-Zآ-ی]+\b', content.lower())
        # Filter common words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 
                     'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 
                     'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                     'from', 'as', 'into', 'through', 'during', 'before', 'after',
                     'و', 'از', 'به', 'در', 'برای', 'که', 'این', 'است', 'آن'}
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        # Return most common keywords (up to 20)
        from collections import Counter
        return [w for w, _ in Counter(keywords).most_common(20)]
    
    def extract_all(self) -> List[TrainingDocument]:
        """Extract text from all PDFs"""
        documents = []
        
        pdf_files = self.find_pdfs()
        
        for pdf_path in pdf_files:
            try:
                text = self.extract_text(pdf_path)
                
                if text.strip():
                    doc = TrainingDocument(
                        doc_id=hashlib.md5(pdf_path.encode()).hexdigest()[:12],
                        title=os.path.basename(pdf_path),
                        source_type='pdf',
                        source_path=pdf_path,
                        content=text,
                        extracted_at=datetime.now()
                    )
                    documents.append(doc)
                    logger.info(f"Extracted document: {doc.title}")
            except Exception as e:
                logger.error(f"Error extracting {pdf_path}: {e}")
        
        return documents


class MarkdownParser:
    """
    Parse markdown files for training data
    Extracts headers, code blocks, definitions, etc.
    """
    
    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = docs_dir
    
    def find_markdown_files(self) -> List[str]:
        """Find all markdown files"""
        md_files = []
        
        if not os.path.exists(self.docs_dir):
            return md_files
        
        for root, dirs, files in os.walk(self.docs_dir):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
            
            for file in files:
                if file.lower().endswith(('.md', '.markdown')):
                    md_files.append(os.path.join(root, file))
        
        logger.info(f"Found {len(md_files)} markdown files")
        return md_files
    
    def extract_content(self, md_path: str) -> str:
        """Extract clean text from markdown"""
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove code blocks
        content = re.sub(r'```[\s\S]*?```', '', content)
        
        # Remove inline code
        content = re.sub(r'`[^`]+`', '', content)
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove links but keep text
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        
        # Remove images
        content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', content)
        
        # Normalize whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def extract_sections(self, md_path: str) -> List[Dict]:
        """Extract sections from markdown"""
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        sections = []
        lines = content.split('\n')
        
        current_section = {'title': 'Introduction', 'content': [], 'level': 0}
        
        for line in lines:
            # Check for headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if header_match:
                # Save previous section
                if current_section['content']:
                    sections.append(current_section)
                
                current_section = {
                    'title': header_match.group(2).strip(),
                    'content': [],
                    'level': len(header_match.group(1))
                }
            else:
                # Skip code blocks and very short lines
                if not line.startswith('```') and len(line.strip()) > 2:
                    current_section['content'].append(line.strip())
        
        # Don't forget last section
        if current_section['content']:
            sections.append(current_section)
        
        return sections
    
    def extract_all(self) -> List[TrainingDocument]:
        """Extract content from all markdown files"""
        documents = []
        
        md_files = self.find_markdown_files()
        
        for md_path in md_files:
            try:
                content = self.extract_content(md_path)
                
                if content.strip():
                    # Get relative path
                    rel_path = os.path.relpath(md_path, self.docs_dir)
                    
                    doc = TrainingDocument(
                        doc_id=hashlib.md5(md_path.encode()).hexdigest()[:12],
                        title=os.path.basename(md_path).replace('.md', '').replace('_', ' ').title(),
                        source_type='markdown',
                        source_path=rel_path,
                        content=content,
                        extracted_at=datetime.now()
                    )
                    documents.append(doc)
            except Exception as e:
                logger.error(f"Error processing {md_path}: {e}")
        
        return documents


class EducationalWebScraper:
    """
    Scrape educational websites for financial content
    """
    
    # List of known financial educational websites
    KNOWN_SOURCES = [
        {
            'name': 'TSE Educational',
            'url': 'https://www.tse.ir/categories/education.html',
            'category': 'stock_market'
        },
        {
            'name': 'Financial Literacy',
            'url': 'https://www.irbourse.com/education',
            'category': 'trading'
        },
        {
            'name': 'Technical Analysis Guide',
            'url': 'https://www.technical-analysis.ir',
            'category': 'technical_analysis'
        }
    ]
    
    def __init__(self):
        self.session = None
    
    @property
    def beautifulsoup_available(self) -> bool:
        """Check if BeautifulSoup4 is available"""
        return BS4_AVAILABLE
    
    @property
    def lxml_available(self) -> bool:
        """Check if lxml is available"""
        return LXML_AVAILABLE
    
    @property
    def requests_available(self) -> bool:
        """Check if requests library is available"""
        try:
            import requests
            return True
        except ImportError:
            return False
    
    def _get_session(self):
        """Get HTTP session"""
        if not self.session:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        return self.session
    
    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page"""
        if not self.requests_available or not self.beautifulsoup_available:
            logger.warning("Web scraping dependencies not available")
            return None
        
        try:
            session = self._get_session()
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch {url}: Status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_educational_content(self, html: str, url: str) -> List[Dict]:
        """Parse educational content from HTML"""
        if not self.beautifulsoup_available or BeautifulSoup is None:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        
        content_blocks = []
        
        # Extract paragraphs
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if len(text) > 50:  # Skip short paragraphs
                content_blocks.append({
                    'type': 'paragraph',
                    'content': text,
                    'source': url
                })
        
        # Extract headings
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = h.get_text(strip=True)
            if len(text) > 3:
                content_blocks.append({
                    'type': 'heading',
                    'content': text,
                    'source': url
                })
        
        # Extract list items
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            if len(text) > 10:
                content_blocks.append({
                    'type': 'list_item',
                    'content': text,
                    'source': url
                })
        
        return content_blocks
    
    def fetch_known_sources(self) -> List[TrainingDocument]:
        """Fetch content from known educational sources"""
        documents = []
        
        for source in self.KNOWN_SOURCES:
            try:
                html = self.fetch_page(source['url'])
                
                if html:
                    content_blocks = self.parse_educational_content(html, source['url'])
                    
                    if content_blocks:
                        content = '\n\n'.join([b['content'] for b in content_blocks])
                        
                        doc = TrainingDocument(
                            doc_id=hashlib.md5(source['url'].encode()).hexdigest()[:12],
                            title=source['name'],
                            source_type='web',
                            source_path=source['url'],
                            content=content,
                            extracted_at=datetime.now(),
                            keywords=[source['category']]
                        )
                        documents.append(doc)
                        
            except Exception as e:
                logger.error(f"Error fetching {source['name']}: {e}")
        
        return documents

    def scrape_article(self, url: str) -> Optional[str]:
        """Scrape a single article from URL"""
        html = self.fetch_page(url)
        
        if not html:
            return None
        
        # Parse content
        if BeautifulSoup is None:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove scripts and styles
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        # Get main content
        content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
        
        if content:
            # Extract text
            text = content.get_text(separator='\n', strip=True)
            return text
        
        # Fallback to body
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)
        
        return None


class KnowledgeBaseBuilder:
    """
    Build knowledge base from extracted training data
    Creates chunks, indexes content, and prepares for AI training
    """
    
    def __init__(self, data_dir: str = "data/knowledge"):
        self.data_dir = data_dir
        self.documents: List[TrainingDocument] = []
        self.chunks: List[KnowledgeChunk] = []
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(f"{data_dir}/extracted", exist_ok=True)
    
    def add_document(self, doc: TrainingDocument):
        """Add a document to the knowledge base"""
        self.documents.append(doc)
        
        # Save document
        doc_file = f"{self.data_dir}/extracted/{doc.doc_id}.json"
        with open(doc_file, 'w', encoding='utf-8') as f:
            json.dump({
                'doc_id': doc.doc_id,
                'title': doc.title,
                'source_type': doc.source_type,
                'source_path': doc.source_path,
                'content': doc.content,
                'extracted_at': doc.extracted_at.isoformat(),
                'keywords': doc.keywords
            }, f, ensure_ascii=False, indent=2)
    
    def chunk_document(self, doc: TrainingDocument, chunk_size: int = 1000) -> List[KnowledgeChunk]:
        """Split document into knowledge chunks"""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = doc.content.split('\n\n')
        
        current_chunk = ""
        chunk_count = 0
        
        for para in paragraphs:
            para = para.strip()
            
            # Skip very short paragraphs
            if len(para) < 50:
                continue
            
            # Check if adding this paragraph would exceed chunk size
            if len(current_chunk) + len(para) > chunk_size:
                if current_chunk:
                    chunk = self._create_chunk(current_chunk, doc, chunk_count)
                    if chunk:
                        chunks.append(chunk)
                        chunk_count += 1
                
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += '\n\n' + para
                else:
                    current_chunk = para
        
        # Don't forget last chunk
        if current_chunk:
            chunk = self._create_chunk(current_chunk, doc, chunk_count)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, content: str, doc: TrainingDocument, chunk_num: int) -> Optional[KnowledgeChunk]:
        """Create a knowledge chunk from content"""
        content = content.strip()
        
        if len(content) < 50:
            return None
        
        # Determine chunk type
        chunk_type = 'explanation'
        
        if content.startswith('#'):
            chunk_type = 'section'
        elif '?' in content and len(content) < 200:
            chunk_type = 'question'
        elif 'Example:' in content or 'مثال:' in content:
            chunk_type = 'example'
        elif 'Definition:' in content or 'تعریف:' in content:
            chunk_type = 'definition'
        elif len(content) < 300:
            chunk_type = 'concept'
        
        # Extract keywords
        keywords = self._extract_keywords(content)
        
        # Generate chunk ID
        chunk_id = f"{doc.doc_id}_{chunk_num}"
        
        return KnowledgeChunk(
            chunk_id=chunk_id,
            document_id=doc.doc_id,
            content=content,
            chunk_type=chunk_type,
            topic=keywords[0] if keywords else 'General',
            confidence=0.8,
            related_topics=keywords[1:5]
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Persian financial keywords
        financial_terms = [
            'بورس', 'سهام', 'شاخص', 'قیمت', 'حجم', 'معامله',
            'خرید', 'فروش', 'سود', 'زیان', 'ریسک', 'بازده',
            'RSI', 'MACD', 'Bollinger', 'میانگین', 'متحرک',
            'حمایت', 'مقاومت', 'روند', 'الگو', 'کندل', 'شمعی',
            'تحلیل', 'تکنیکال', 'بنیادی', 'نمودار', 'تایم',
            'سهامدار', 'شرکت', 'صنعت', 'بازار', 'سرمایه'
        ]
        
        keywords = []
        text_lower = text.lower()
        
        for term in financial_terms:
            if term.lower() in text_lower:
                keywords.append(term)
        
        return keywords[:10]
    
    def build_all(self, docs_dir: str = "docs") -> Dict:
        """Build complete knowledge base from all sources"""
        logger.info("Starting knowledge base build...")
        
        # 1. Extract PDF documents
        logger.info("Extracting PDF files...")
        pdf_extractor = PDFExtractor(docs_dir)
        pdf_docs = pdf_extractor.extract_all()
        
        for doc in pdf_docs:
            self.add_document(doc)
            chunks = self.chunk_document(doc)
            self.chunks.extend(chunks)
        
        # 2. Extract markdown documents
        logger.info("Extracting markdown files...")
        md_parser = MarkdownParser(docs_dir)
        md_docs = md_parser.extract_all()
        
        for doc in md_docs:
            self.add_document(doc)
            chunks = self.chunk_document(doc)
            self.chunks.extend(chunks)
        
        # 3. Save chunks
        logger.info(f"Saving {len(self.chunks)} knowledge chunks...")
        self._save_chunks()
        
        # 4. Build index
        logger.info("Building search index...")
        index = self._build_index()
        self._save_index(index)
        
        # 5. Return statistics
        stats = {
            'total_documents': len(self.documents),
            'pdf_documents': len([d for d in self.documents if d.source_type == 'pdf']),
            'markdown_documents': len([d for d in self.documents if d.source_type == 'markdown']),
            'web_documents': len([d for d in self.documents if d.source_type == 'web']),
            'total_chunks': len(self.chunks),
            'chunk_types': self._count_chunk_types(),
            'keywords': self._extract_all_keywords()
        }
        
        logger.info(f"Knowledge base build complete: {stats}")
        
        return stats
    
    def _save_chunks(self):
        """Save all chunks to files"""
        chunks_data = []
        
        for chunk in self.chunks:
            chunks_data.append({
                'chunk_id': chunk.chunk_id,
                'document_id': chunk.document_id,
                'content': chunk.content,
                'chunk_type': chunk.chunk_type,
                'topic': chunk.topic,
                'confidence': chunk.confidence,
                'related_topics': chunk.related_topics
            })
        
        chunks_file = f"{self.data_dir}/chunks.json"
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
    
    def _build_index(self) -> Dict[str, List[str]]:
        """Build inverted index for search"""
        index = {}
        
        for chunk in self.chunks:
            # Index by topic
            if chunk.topic not in index:
                index[chunk.topic] = []
            index[chunk.topic].append(chunk.chunk_id)
            
            # Index by related topics
            for related in chunk.related_topics:
                if related not in index:
                    index[related] = []
                if chunk.chunk_id not in index[related]:
                    index[related].append(chunk.chunk_id)
            
            # Index by keywords in content
            keywords = self._extract_keywords(chunk.content)
            for keyword in keywords:
                if keyword not in index:
                    index[keyword] = []
                if chunk.chunk_id not in index[keyword]:
                    index[keyword].append(chunk.chunk_id)
        
        return index
    
    def _save_index(self, index: Dict):
        """Save search index"""
        index_file = f"{self.data_dir}/index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _count_chunk_types(self) -> Dict[str, int]:
        """Count chunks by type"""
        counts = {}
        for chunk in self.chunks:
            counts[chunk.chunk_type] = counts.get(chunk.chunk_type, 0) + 1
        return counts
    
    def _extract_all_keywords(self) -> List[str]:
        """Extract all unique keywords"""
        keywords = set()
        for chunk in self.chunks:
            keywords.add(chunk.topic)
            keywords.update(chunk.related_topics)
        return sorted(list(keywords))
    
    def search(self, query: str, top_k: int = 5) -> List[KnowledgeChunk]:
        """Search knowledge base"""
        # Load index
        index_file = f"{self.data_dir}/index.json"
        
        if not os.path.exists(index_file):
            return []
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Find matching chunks
        query_keywords = self._extract_keywords(query)
        matching_chunks = set()
        
        for keyword in query_keywords:
            if keyword in index:
                matching_chunks.update(index[keyword])
        
        # Load and return matching chunks
        chunks_file = f"{self.data_dir}/chunks.json"
        
        if not os.path.exists(chunks_file):
            return []
        
        with open(chunks_file, 'r', encoding='utf-8') as f:
            all_chunks = {c['chunk_id']: c for c in json.load(f)}
        
        results = []
        for chunk_id in list(matching_chunks)[:top_k]:
            if chunk_id in all_chunks:
                c = all_chunks[chunk_id]
                results.append(KnowledgeChunk(
                    chunk_id=c['chunk_id'],
                    document_id=c['document_id'],
                    content=c['content'],
                    chunk_type=c['chunk_type'],
                    topic=c['topic'],
                    confidence=c['confidence'],
                    related_topics=c['related_topics']
                ))
        
        return results


class TrainingDataPipeline:
    """
    Main pipeline for training data extraction and processing
    Runs periodically to update knowledge base
    """
    
    def __init__(self, docs_dir: str = "docs", data_dir: str = "data/knowledge"):
        self.docs_dir = docs_dir
        self.knowledge_base = KnowledgeBaseBuilder(data_dir)
        self.web_scraper = EducationalWebScraper()
    
    def run_full_pipeline(self) -> Dict:
        """Run complete training data pipeline"""
        logger.info("Starting training data pipeline...")
        
        # Build knowledge base from local documents
        stats = self.knowledge_base.build_all(self.docs_dir)
        
        # Fetch web content (optional, can be disabled)
        # web_docs = self.web_scraper.fetch_known_sources()
        # for doc in web_docs:
        #     self.knowledge_base.add_document(doc)
        
        logger.info(f"Pipeline complete: {stats}")
        
        return stats
    
    def run_periodic_update(self):
        """Run periodic update in background thread"""
        def update_loop():
            while True:
                try:
                    logger.info("Running periodic training data update...")
                    self.run_full_pipeline()
                except Exception as e:
                    logger.error(f"Update error: {e}")
                
                # Wait 24 hours
                import time
                time.sleep(24 * 3600)
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        logger.info("Periodic training data update started")
    
    def build_knowledge_base(self) -> Dict:
        """Alias for run_full_pipeline for API compatibility"""
        return self.run_full_pipeline()
    
    def get_status(self) -> Dict:
        """Get current status of training data pipeline"""
        try:
            # Check if knowledge base exists
            chunks_file = f"{self.knowledge_base.data_dir}/chunks.json"
            has_chunks = os.path.exists(chunks_file)
            
            if has_chunks:
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    chunks_data = json.load(f)
                chunk_count = len(chunks_data)
                
                # Get document count
                extracted_dir = f"{self.knowledge_base.data_dir}/extracted"
                if os.path.exists(extracted_dir):
                    doc_count = len([f for f in os.listdir(extracted_dir) if f.endswith('.json')])
                else:
                    doc_count = 0
            else:
                chunk_count = 0
                doc_count = 0
            
            return {
                "status": "ready" if has_chunks else "empty",
                "total_documents": doc_count,
                "total_chunks": chunk_count,
                "last_updated": self._get_last_update_time(),
                "data_directory": self.knowledge_base.data_dir
            }
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def list_sources(self) -> List[Dict]:
        """List all available document sources"""
        sources = []
        
        # PDF sources
        pdf_extractor = PDFExtractor(self.docs_dir)
        pdf_files = pdf_extractor.find_pdfs()
        for pdf in pdf_files:
            sources.append({
                "type": "pdf",
                "path": pdf,
                "filename": os.path.basename(pdf)
            })
        
        # Markdown sources
        md_parser = MarkdownParser(self.docs_dir)
        md_files = md_parser.find_markdown_files()
        for md in md_files:
            sources.append({
                "type": "markdown", 
                "path": md,
                "filename": os.path.basename(md)
            })
        
        return sources
    
    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """Extract content from a specific PDF file"""
        try:
            pdf_extractor = PDFExtractor(self.docs_dir)
            content = pdf_extractor.extract_text(pdf_path)
            
            # Create document
            doc_id = f"pdf_{os.path.basename(pdf_path).replace('.pdf', '')}"
            doc = TrainingDocument(
                doc_id=doc_id,
                title=os.path.basename(pdf_path),
                source_type="pdf",
                source_path=pdf_path,
                content=content,
                extracted_at=datetime.now(),
                keywords=pdf_extractor._extract_keywords(content)
            )
            
            # Chunk the document
            chunks = self.knowledge_base.chunk_document(doc)
            
            return {
                "success": True,
                "document": {
                    "id": doc.doc_id,
                    "title": doc.title,
                    "content_length": len(doc.content),
                    "chunks_created": len(chunks)
                },
                "chunks": [
                    {
                        "id": chunk.chunk_id,
                        "type": chunk.chunk_type,
                        "topic": chunk.topic,
                        "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                    }
                    for chunk in chunks
                ]
            }
            
        except Exception as e:
            logger.error(f"PDF extraction error for {pdf_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_last_update_time(self) -> Optional[str]:
        """Get last update time from chunks file"""
        try:
            chunks_file = f"{self.knowledge_base.data_dir}/chunks.json"
            if os.path.exists(chunks_file):
                return datetime.fromtimestamp(os.path.getmtime(chunks_file)).isoformat()
        except:
            pass
        return None


# Usage example
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    pipeline = TrainingDataPipeline()
    stats = pipeline.run_full_pipeline()
    
    print(f"\n📊 Training Data Statistics:")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"PDF Documents: {stats['pdf_documents']}")
    print(f"Markdown Documents: {stats['markdown_documents']}")
    print(f"Total Chunks: {stats['total_chunks']}")
    print(f"Chunk Types: {stats['chunk_types']}")
    print(f"Unique Keywords: {len(stats['keywords'])}")


# Aliases for easier import
TrainingDataExtractor = TrainingDataPipeline
WebScraper = EducationalWebScraper
