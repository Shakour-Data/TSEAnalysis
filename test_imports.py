#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script for training_data_extractor imports."""

import sys

# Import all classes at module level for access by test_functionality
from app.services.training_data_extractor import (
    PDFExtractor,
    EducationalWebScraper,
    TrainingDataExtractor,
    WebScraper,
    TrainingDocument,
    KnowledgeChunk,
    PDFPLUMBER_AVAILABLE,
    PYPDF2_AVAILABLE,
    BS4_AVAILABLE,
    LXML_AVAILABLE,
)

def test_imports():
    """Test all imports from training_data_extractor module."""
    print("Testing imports from training_data_extractor...")
    
    try:
        print("[OK] All classes imported successfully at module level!")
        print("  - PDFExtractor: " + str(PDFExtractor))
        print("  - EducationalWebScraper: " + str(EducationalWebScraper))
        print("  - TrainingDataExtractor: " + str(TrainingDataExtractor))
        print("  - WebScraper: " + str(WebScraper))
        print("  - PDFPLUMBER_AVAILABLE: " + str(PDFPLUMBER_AVAILABLE))
        print("  - PYPDF2_AVAILABLE: " + str(PYPDF2_AVAILABLE))
        print("  - BS4_AVAILABLE: " + str(BS4_AVAILABLE))
        print("  - LXML_AVAILABLE: " + str(LXML_AVAILABLE))
        return True
    except ImportError as e:
        print("[ERROR] Import failed: " + str(e))
        return False
    except Exception as e:
        print("[ERROR] Unexpected error: " + str(e))
        return False

def test_functionality():
    """Test basic functionality of the imported classes."""
    print("\nTesting basic functionality...")
    
    try:
        # Test PDFExtractor
        extractor = PDFExtractor()
        print("[OK] PDFExtractor instantiated: " + str(extractor))
        print("  - pdf_available: " + str(extractor.pdf_available))
        print("  - pdfplumber_available: " + str(extractor.pdfplumber_available))
        
        # Test EducationalWebScraper
        scraper = EducationalWebScraper()
        print("[OK] EducationalWebScraper instantiated: " + str(scraper))
        print("  - beautifulsoup_available: " + str(scraper.beautifulsoup_available))
        print("  - lxml_available: " + str(scraper.lxml_available))
        
        # Test TrainingDataExtractor
        tde = TrainingDataExtractor()
        print("[OK] TrainingDataExtractor instantiated: " + str(tde))
        
        print("\n[OK] All functionality tests passed!")
        return True
    except Exception as e:
        print("[ERROR] Functionality test failed: " + str(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TSE Analysis - Training Data Extractor Import Tests")
    print("=" * 60)
    
    imports_ok = test_imports()
    functionality_ok = test_functionality()
    
    print("\n" + "=" * 60)
    if imports_ok and functionality_ok:
        print("ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)
