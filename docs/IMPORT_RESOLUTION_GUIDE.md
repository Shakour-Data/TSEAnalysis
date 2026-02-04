# راهنمای حل مشکلات Import در Pylance

## فهرست مطالب

1. [خلاصه مشکل](#۱-خلاصه-مشکل)
2. [تحلیل پیکربندی فعلی](#۲-تحلیل-پیکربندی-فعلی)
3. [راه‌اندازی محیط مجازی](#۳-راه‌اندازی-محیط-مجازی)
4. [دستورات نصب بسته‌ها](#۴-دستورات-نصب-بستهها)
5. [تغییرات کد انجام شده](#۵-تغییرات-کد-انجام-شده)
6. [بسته‌های جایگزین](#۶-بستههای-جایگزین)
7. [عیب‌یابی](#۷-عیبیابی)

---

## ۱. خلاصه مشکل

### مشکلات شناسایی شده

| بسته | وضعیت در requirements.txt | وضعیت در pyproject.toml | مشکل Pylance |
|------|--------------------------|------------------------|--------------|
| PyPDF2 | ✅ 3.0.1 | ❌ وجود ندارد | ImportNotResolved |
| pdfplumber | ✅ 0.11.4 | ❌ وجود ندارد | ImportNotResolved |
| beautifulsoup4 | ✅ 4.12.3 | ⚠️ 4.9.0 (نسخه قدیمی‌تر) | ImportNotResolved |
| lxml | ⚠️ در requirements.txt | ⚠️ 4.6.0 | ImportNotResolved |

### علت اصلی مشکل

Pylance در Visual Studio Code برای تشخیص صحیح Importها به موارد زیر نیاز دارد:

1. **تعریف صریح در pyproject.toml** - Pylance از این فایل برای شناسایی وابستگی‌ها استفاده می‌کند
2. **Import در سطح ماژول** - Importهای داخل توابع با try/except توسط Pylance شناسایی نمی‌شوند
3. **Virtual Environment فعال** - بدون محیط مجازی فعال، Pylance نمی‌تواند بسته‌ها را پیدا کند

---

## ۲. تحلیل پیکربندی فعلی

### نسخه Python مورد نیاز

```toml
requires-python = ">=3.8"
```

### نسخه‌های سازگار بسته‌ها با Python 3.8+

| بسته | نسخه سازگار | نسخه موجود | توصیه |
|------|------------|------------|-------|
| PyPDF2 | 3.0.1 (سازگار) | 3.0.1 | ✅ نصب شده |
| pdfplumber | 0.11.x | 0.11.4 | ✅ سازگار |
| beautifulsoup4 | 4.12.x | 4.12.3 | ✅ سازگار |
| lxml | 4.9.x | در requirements.txt | ✅ نیاز به نصب |

---

## ۳. راه‌اندازی محیط مجازی

### مرحله ۱: ایجاد محیط مجازی

```bash
# روش ۱: با venv (پیشنهادی)
python -m venv venv

# روش ۲: با virtualenv
pip install virtualenv
virtualenv venv
```

### مرحله ۲: فعال‌سازی محیط مجازی

```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### مرحله ۳: تأیید فعال‌سازی

```bash
# باید مسف پایتون محیط مجازی را نشان دهد
where python
# یا
which python
```

---

## ۴. دستورات نصب بسته‌ها

### نصب تمام وابستگی‌ها

```bash
# روش ۱: از pyproject.toml (پیشنهادی)
pip install -e .

# روش ۲: از requirements.txt
pip install -r requirements.txt

# روش ۳: نصب دستی بسته‌های خاص
pip install PyPDF2==3.0.1
pip install pdfplumber==0.11.4
pip install beautifulsoup4==4.12.3
pip install lxml
```

### نصب برای توسعه

```bash
pip install -e ".[dev]"
```

### تأیید نصب صحیح

```python
# تست import بسته‌ها
import PyPDF2
import pdfplumber
from bs4 import BeautifulSoup
import lxml

print("✅ تمام بسته‌ها نصب شدند!")
```

---

## ۵. تغییرات کد انجام شده

### ۵.۱ به‌روزرسانی ماژول training_data_extractor.py

#### تغییر ۱: Import سطح ماژول

```python
# قبل (مشکل‌دار)
class PDFExtractor:
    def _ensure_dependencies(self):
        try:
            import PyPDF2
            self.pdf_available = True
        except ImportError:
            self.pdf_available = False

# بعد (اصلاح شده)
# Optional imports with graceful fallback
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    PyPDF2 = None

class PDFExtractor:
    @property
    def pdf_available(self) -> bool:
        return PYPDF2_AVAILABLE
```

#### تغییر ۲: استفاده از Properties

```python
class PDFExtractor:
    @property
    def pdfplumber_available(self) -> bool:
        return PDFPLUMBER_AVAILABLE
    
    @property
    def pdf_available(self) -> bool:
        return PYPDF2_AVAILABLE
```

#### تغییر ۳: مستندسازی وابستگی‌ها

```python
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
```

### ۵.۲ به‌روزرسانی pyproject.toml

```toml
[project]
dependencies = [
    "flask>=2.0.0",
    "requests>=2.25.0",
    "pandas>=1.3.0",
    "numpy>=1.20.0",
    "scikit-learn>=1.0.0",
    "joblib>=1.0.0",
    "pytest>=6.0.0",
    "pytest-cov>=2.0.0",
    "beautifulsoup4>=4.9.0",
    "lxml>=4.6.0",
    "PyPDF2>=3.0.0",
    "pdfplumber>=0.10.0",
    "jdatetime>=4.0.0",
]
```

---

## ۶. بسته‌های جایگزین

### ۶.۱ جایگزین‌های PyPDF2

| بسته | مزایا | معایب | زمان استفاده |
|------|-------|-------|--------------|
| **pypdf** (جدیدتر) | نسخه جدید PyPDF2، بهینه‌تر | تغییر API | پروژه‌های جدید |
| **pdfminer.six** | استخراج داده‌های ساختاریافته | کندتر | PDF با جدول |
| **pdftotext** | سریع‌ترین | نیاز به سیستم | فایل‌های بزرگ |
| **pdfplumber** | بهترین برای جداول و متن | سنگین‌تر | PDF مالی |

### ۶.۲ جایگزین‌های beautifulsoup4

| بسته | مزایا | معایب | زمان استفاده |
|------|-------|-------|--------------|
| **lxml** | بسیار سریع | پیچیده‌تر | وب اسکرپینگ حجیم |
| **selectolax** | سریع‌تر از bs4 | کمتر شناخته شده | جایگزین سریع |
| **parsel** | با Scrapy یکپارچه | نیاز به Scrapy | پروژه‌های Scrapy |
| **htmllib6** | استاندارد پایتون | محدود | HTML ساده |

### ۶.۳ نصب جایگزین‌ها (اختیاری)

```bash
# جایگزین PyPDF2 با pypdf
pip uninstall PyPDF2
pip install pypdf

# جایگزین bs4 با selectolax
pip uninstall beautifulsoup4
pip install selectolax

# نصب pdfminer.six
pip install pdfminer.six
```

---

## ۷. عیب‌یابی

### مشکل ۱: Pylance همچنان خطا نشان می‌دهد

**راه‌حل:**

```bash
# ۱. ری‌استارت کردن Python Language Server
# در VS Code: Ctrl+Shift+P > "Python: Restart Language Server"

# ۲. پاک کردن کش Pylance
# در VS Code: Ctrl+Shift+P > "Developer: Reload Window"

# ۳. انتخاب interpreter صحیح
# در VS Code: Ctrl+Shift+P > "Python: Select Interpreter"
```

### مشکل ۲: ImportError در زمان اجرا

**راه‌حل:**

```bash
# بررسی نصب بسته
pip show PyPDF2
pip show pdfplumber
pip show beautifulsoup4
pip show lxml

# نصب مجدد در صورت نیاز
pip uninstall PyPDF2 pdfplumber beautifulsoup4 lxml
pip install PyPDF2==3.0.1 pdfplumber==0.11.4 beautifulsoup4==4.12.3 lxml
```

### مشکل ۳: ناسازگاری نسخه Python

**راه‌حل:**

```bash
# بررسی نسخه Python
python --version

# اگر نسخه پایین است، Python 3.8+ نصب کنید
# از سایت python.org یا Windows Store
```

### مشکل ۴: خطا در Virtual Environment

**راه‌حل:**

```bash
# حذف و ایجاد مجدد venv
deactivate
rmdir /s venv  # Windows
# یا
rm -rf venv    # Linux/macOS

# ایجاد مجدد
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# نصب وابستگی‌ها
pip install -e .
```

### مشکل ۵: تداخل با بسته‌های سیستمی

**راه‌حل:**

```bash
# استفاده از --user
pip install --user PyPDF2 pdfplumber beautifulsoup4 lxml

# یا استفاده از pipenv
pip install pipenv
pipenv install PyPDF2 pdfplumber beautifulsoup4 lxml
```

---

## خلاصه دستورات

```bash
# راه‌اندازی کامل
python -m venv venv
venv\Scripts\activate
pip install -e .
pip install PyPDF2==3.0.1 pdfplumber==0.11.4 beautifulsoup4==4.12.3 lxml

# تست
python -c "from app.services.training_data_extractor import PDFExtractor, EducationalWebScraper; print('✅ Imports OK')"

# ری‌استارت VS Code
# Ctrl+Shift+P > "Developer: Reload Window"
```

---

## نتیجه

با انجام تغییرات زیر، مشکلات Pylance حل می‌شوند:

1. ✅ Importهای سطح ماژول اضافه شدند
2. ✅ pyproject.toml به‌روزرسانی شد
3. ✅ Properties جایگزین instance variables شدند
4. ✅ مستندسازی کامل اضافه شد
5. ✅ بسته‌های جایگزین معرفی شدند

برای اطلاعات بیشتر به مستندات [process chains](PROCESS_CHAINS_COMPLETE.md) مراجعه کنید.
