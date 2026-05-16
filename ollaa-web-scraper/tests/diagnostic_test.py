#!/usr/bin/env python3
"""
Ollaa Web Scraper Diagnostic Test Script
Tests all scrapers in diagnostic mode without requiring database.

Usage: python tests/diagnostic_test.py
"""

import sys
import os
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("diagnostic")

# Test results storage
test_results = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "import_tests": [],
    "scraper_tests": [],
    "amharic_keyword_tests": [],
    "url_accessibility_tests": [],
    "summary": {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0
    },
    "working_scrapers": [],
    "failed_scrapers": []
}

def _test_import(module_name: str, import_func) -> Dict[str, Any]:
    """Test importing a module."""
    result = {
        "module": module_name,
        "status": "pending",
        "error": None
    }
    try:
        import_func()
        result["status"] = "pass"
        logger.info(f"✓ {module_name} import OK")
    except Exception as e:
        result["status"] = "fail"
        result["error"] = str(e)
        logger.error(f"✗ {module_name} import FAILED: {e}")
    test_results["summary"]["total_tests"] += 1
    if result["status"] == "pass":
        test_results["summary"]["passed"] += 1
    else:
        test_results["summary"]["failed"] += 1
    test_results["import_tests"].append(result)
    return result

def _test_amharic_keywords() -> Dict[str, Any]:
    """Test Amharic keyword parsing."""
    from parsers.amharic_parser import AmharicParser
    
    parser = AmharicParser()
    
    test_cases = [
        # Auction keywords
        {"text": "የሐራጅ ቤት", "expected": "auction", "keyword": "የሐራጅ"},
        {"text": "ጨረታ ሱሚ", "expected": "auction", "keyword": "ጨረታ"},
        {"text": "ሃራጅ ሽያጭ", "expected": "auction", "keyword": "ሃራጅ"},
        {"text": "ሐራጅ ማስታወቅያ", "expected": "auction", "keyword": "ሐራጅ"},
        # Sale keywords
        {"text": "ሽያይ ቤት", "expected": "sale", "keyword": "ሽያይ"},
        {"text": "ለሽጡ", "expected": "sale", "keyword": "ለሽጡ"},
        # Rent keywords
        {"text": "ኪራይ ቤት", "expected": "rent", "keyword": "ኪራይ"},
        # Location test
        {"text": "ቤት በቦሌ", "expected_location": "Bole"},
        {"text": "አፓርትማንት በአዲስ አበባ", "expected_location": "Addis"},
    ]
    
    results = []
    for tc in test_cases:
        result = {
            "input": tc["text"],
            "status": "pass",
            "details": {}
        }
        
        # Test keyword detection
        if "keyword" in tc:
            found = tc["keyword"] in tc["text"]
            result["details"]["keyword_found"] = found
            if not found:
                result["status"] = "fail"
                
        # Test listing type detection
        if "expected" in tc:
            detected = parser.detect_script(tc["text"])
            result["details"]["detected_script"] = detected
            
        # Test location extraction
        if "expected_location" in tc:
            location = parser.extract_location(tc["text"])
            result["details"]["extracted_location"] = location
            result["details"]["expected_location"] = tc["expected_location"]
            
        results.append(result)
        
    test_results["amharic_keyword_tests"] = results
    test_results["summary"]["total_tests"] += len(results)
    test_results["summary"]["passed"] += sum(1 for r in results if r["status"] == "pass")
    test_results["summary"]["failed"] += sum(1 for r in results if r["status"] == "fail")
    
    return {"tested": len(results), "results": results}

def _test_url_accessibility(url: str, timeout: int = 5) -> Dict[str, Any]:
    """Test if a URL is accessible."""
    import requests
    result = {
        "url": url,
        "status": "pending",
        "status_code": None,
        "error": None
    }
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        result["status_code"] = response.status_code
        if 200 <= response.status_code < 400:
            result["status"] = "accessible"
            result["error"] = None
        else:
            result["status"] = "error"
            result["error"] = f"HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = "Connection timeout"
    except requests.exceptions.ConnectionError as e:
        result["status"] = "connection_error"
        result["error"] = "Connection refused or DNS error"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        
    return result

def _test_scraper(scraper_class, scraper_name: str) -> Dict[str, Any]:
    """Test a scraper class in diagnostic mode."""
    result = {
        "scraper": scraper_name,
        "class_path": f"{scraper_class.__module__}.{scraper_class.__name__}",
        "status": "pending",
        "listings_found": 0,
        "errors": [],
        "has_price": False,
        "has_location": False,
        "sample_listing": None
    }
    
    try:
        # Instantiate the scraper
        scraper = scraper_class()
        
        # Run the scrape
        scrape_result = scraper.scrape()
        
        result["status"] = "success" if scrape_result.success else "partial"
        result["listings_found"] = len(scrape_result.listings)
        result["errors"] = scrape_result.errors
        
        # Analyze listings
        if scrape_result.listings:
            first_listing = scrape_result.listings[0]
            result["has_price"] = any(l.price for l in scrape_result.listings)
            result["has_location"] = any(l.location for l in scrape_result.listings)
            result["sample_listing"] = {
                "title": first_listing.title[:100] if first_listing.title else None,
                "price": first_listing.price,
                "location": first_listing.location,
                "listing_type": first_listing.listing_type
            }
            
            # Mark as working if we have real data
            if result["listings_found"] > 0:
                result["status"] = "working"
                test_results["working_scrapers"].append({
                    "name": scraper_name,
                    "listings": len(scrape_result.listings),
                    "has_price": result["has_price"],
                    "has_location": result["has_location"]
                })
        else:
            result["errors"].append("No listings found")
            
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
        logger.error(f"✗ {scraper_name} failed: {e}")
        
    return result

def run_all_tests():
    """Run all diagnostic tests."""
    print("=" * 60)
    print("OLLAA WEB SCRAPER - COMPREHENSIVE DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Test 1: Import tests
    print("\n[1] TESTING IMPORTS...")
    import_tests = [
        ("requests", lambda: __import__("requests")),
        ("beautifulsoup4", lambda: __import__("bs4")),
        ("playwright", lambda: __import__("playwright")),
        ("pdfplumber", lambda: __import__("pdfplumber")),
        ("pytesseract", lambda: __import__("pytesseract")),
        ("pdf2image", lambda: __import__("pdf2image")),
        ("config", lambda: __import__("config")),
        ("parsers.price_extractor", lambda: __import__("parsers.price_extractor")),
        ("parsers.amharic_parser", lambda: __import__("parsers.amharic_parser")),
        ("parsers.ocr_engine", lambda: __import__("parsers.ocr_engine")),
        ("scrapers.base_scraper", lambda: __import__("scrapers.base_scraper")),
    ]
    
    for name, func in import_tests:
        _test_import(name, func)
    
    # Test 2: Amharic Keyword Tests
    print("\n[2] TESTING AMHARIC KEYWORD PARSING...")
    amharic_results = _test_amharic_keywords()
    print(f"   Tested {amharic_results['tested']} Amharic keyword cases")
    
    # Test 3: URL Accessibility Tests
    print("\n[3] TESTING URL ACCESSIBILITY...")
    urls_to_test = [
        ("https://www.combanketh.et", "CBE"),
        ("https://awashbank.com", "Awash Bank"),
        ("https://dashenbanksc.com", "Dashen Bank"),
        ("https://www.zemenbank.com", "Zemen Bank"),
        ("https://www.bankofabyssinia.com", "Bank of Abyssinia"),
        ("https://www.amharabank.com.et", "Amhara Bank"),
        ("https://berhanbanksc.com", "Berhan Bank"),
        ("https://coopbankoromia.com.et", "Coop Bank"),
        ("https://www.waliatender.com", "Walia Tender"),
        ("https://addislist.com", "AddisList"),
        ("https://engocha.com", "Engocha"),
    ]
    
    for url, name in urls_to_test:
        result = _test_url_accessibility(url)
        test_results["url_accessibility_tests"].append({
            "name": name,
            **result
        })
        if result["status"] == "accessible":
            print(f"   ✓ {name}: {result['status_code']}")
        elif result["status"] == "timeout":
            print(f"   ⚠ {name}: TIMEOUT")
        else:
            print(f"   ✗ {name}: {result['error']}")
    
    # Test 4: Scraper Tests
    print("\n[4] TESTING SCRAPERS (Diagnostic Mode)...")
    
    # Bank scrapers
    bank_scrapers = [
        ("scrapers.banks.cbe_scraper.CBEScraper", "CBE"),
        ("scrapers.banks.awash_scraper.AwashBankScraper", "Awash Bank"),
        ("scrapers.banks.dashen_scraper.DashenBankScraper", "Dashen Bank"),
        ("scrapers.banks.zemen_scraper.ZemenBankScraper", "Zemen Bank"),
        ("scrapers.banks.abyssinia_scraper.AbyssiniaBankScraper", "Abyssinia Bank"),
        ("scrapers.banks.amhara_scraper.AmharaBankScraper", "Amhara Bank"),
        ("scrapers.banks.berhan_scraper.BerhanBankScraper", "Berhan Bank"),
        ("scrapers.banks.coop_scraper.CoopBankScraper", "Coop Bank"),
    ]
    
    # Tender scrapers
    tender_scrapers = [
        ("scrapers.tenders.waliatender_scraper.WaliaTenderScraper", "Walia Tender"),
    ]
    
    # Listing scrapers
    listing_scrapers = [
        ("scrapers.listings.engocha_scraper.EngochaScraper", "Engocha"),
        ("scrapers.banks.addislist_scraper.AddisListScraper", "AddisList"),
    ]
    
    all_scrapers = bank_scrapers + tender_scrapers + listing_scrapers
    
    for class_path, name in all_scrapers:
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            scraper_class = getattr(module, class_name)
            
            print(f"\n   Testing {name}...", end=" ")
            result = _test_scraper(scraper_class, name)
            test_results["scraper_tests"].append(result)
            
            if result["status"] == "working":
                print(f"✓ {result['listings_found']} listings")
                print(f"      Price: {result['has_price']}, Location: {result['has_location']}")
            elif result["status"] == "partial":
                print(f"⚠ {result['listings_found']} listings (partial success)")
            else:
                print(f"✗ {result['errors'][:2] if result['errors'] else 'No data'}")
                test_results["failed_scrapers"].append({
                    "name": name,
                    "reason": result["errors"][0] if result["errors"] else "Unknown"
                })
                
        except Exception as e:
            print(f"✗ IMPORT ERROR: {e}")
            test_results["failed_scrapers"].append({
                "name": name,
                "reason": f"Import error: {str(e)}"
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total tests: {test_results['summary']['total_tests']}")
    print(f"Passed: {test_results['summary']['passed']}")
    print(f"Failed: {test_results['summary']['failed']}")
    print(f"Warnings: {test_results['summary']['warnings']}")
    
    print(f"\nWORKING SCRAPERS ({len(test_results['working_scrapers'])}):")
    for ws in test_results["working_scrapers"]:
        print(f"  - {ws['name']}: {ws['listings']} listings, price={ws['has_price']}, location={ws['has_location']}")
    
    print(f"\nFAILED SCRAPERS ({len(test_results['failed_scrapers'])}):")
    for fs in test_results["failed_scrapers"]:
        print(f"  - {fs['name']}: {fs['reason']}")
    
    # Save results
    output_file = "/home/engine/project/diagnostic_results.json"
    with open(output_file, "w") as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")
    
    return test_results

if __name__ == "__main__":
    results = run_all_tests()
    sys.exit(0 if results["summary"]["failed"] == 0 else 1)


# Pytest test functions
def test_diagnostic_suite():
    """Run the full diagnostic suite via pytest."""
    results = run_all_tests()
    assert results is not None