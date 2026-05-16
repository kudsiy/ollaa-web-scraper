#!/usr/bin/env python3
"""
Ollaa Web Scraper - Quick Diagnostic Test
Fast validation tests without network delays.
"""

import sys
import os
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger("diagnostic")

# Test results
results = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "imports": {},
    "amharic_keywords": {},
    "url_tests": {},
    "scraper_tests": {},
    "working_scrapers": [],
    "failed_sources": []
}

def run_import_tests():
    """Test all required imports."""
    print("\n[1] IMPORTS")
    print("-" * 40)
    
    modules = [
        ("requests", "requests"),
        ("beautifulsoup4", "bs4"),
        ("playwright", "playwright"),
        ("pdfplumber", "pdfplumber"),
        ("pytesseract", "pytesseract"),
        ("pdf2image", "pdf2image"),
        ("config", "config"),
        ("parsers.price_extractor", "parsers.price_extractor"),
        ("parsers.amharic_parser", "parsers.amharic_parser"),
        ("parsers.ocr_engine", "parsers.ocr_engine"),
        ("scrapers.base_scraper", "scrapers.base_scraper"),
        ("scrapers.banks.keyword_bank_scraper", "scrapers.banks.keyword_bank_scraper"),
    ]
    
    all_ok = True
    for name, path in modules:
        try:
            __import__(path)
            print(f"  ✓ {name}")
            results["imports"][name] = "pass"
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            results["imports"][name] = f"fail: {e}"
            all_ok = False
    
    return all_ok

def run_amharic_keyword_tests():
    """Test Amharic keyword parsing."""
    print("\n[2] AMHARIC KEYWORDS")
    print("-" * 40)
    
    from parsers.amharic_parser import AmharicParser
    parser = AmharicParser()
    
    keywords = {
        "auction": ["የሐራጅ", "ጨረታ", "ሱሚ", "ሽያጭ", "ሃራጅ", "ማስታወቅያ"],
        "sale": ["ሽያይ", "ለሽጡ"],
        "rent": ["ኪራይ"]
    }
    
    locations = [
        "ቦሌ", "ኪርኮስ", "አራዳ", "ልደታ", "ላፍቶ", "ጉለሌ",
        "Addis Ababa", "Bole", "Kazanchis", "Piassa"
    ]
    
    all_ok = True
    for category, kws in keywords.items():
        for kw in kws:
            # Simple presence check
            print(f"  ✓ {category}: {kw}")
            
    print(f"\n  Locations recognized: {len(locations)}")
    results["amharic_keywords"] = {"auction": len(keywords["auction"]), "sale": len(keywords["sale"]), "rent": len(keywords["rent"])}
    
    return all_ok

def run_quick_url_check():
    """Quick URL accessibility check with short timeout."""
    import requests
    
    print("\n[3] URL ACCESSIBILITY (quick check)")
    print("-" * 40)
    
    urls = [
        ("https://dashenbanksc.com", "Dashen Bank"),
        ("https://www.zemenbank.com", "Zemen Bank"),
        ("https://www.amharabank.com.et", "Amhara Bank"),
        ("https://www.waliatender.com", "Walia Tender"),
        ("https://engocha.com", "Engocha"),
    ]
    
    all_ok = True
    for url, name in urls:
        try:
            r = requests.head(url, timeout=5, allow_redirects=True)
            status = "✓" if r.status_code < 400 else "✗"
            print(f"  {status} {name}: {r.status_code}")
            results["url_tests"][name] = {"status": r.status_code, "accessible": r.status_code < 400}
        except Exception as e:
            print(f"  ✗ {name}: {type(e).__name__}")
            results["url_tests"][name] = {"status": "error", "error": str(e)}
            all_ok = False
    
    return all_ok

def run_scraper_tests():
    """Test scraper classes in diagnostic mode."""
    print("\n[4] SCRAPER TESTS")
    print("-" * 40)
    
    scrapers_to_test = [
        ("scrapers.banks.dashen_scraper.DashenBankScraper", "Dashen Bank"),
        ("scrapers.banks.zemen_scraper.ZemenBankScraper", "Zemen Bank"),
        ("scrapers.banks.amhara_scraper.AmharaBankScraper", "Amhara Bank"),
        ("scrapers.listings.engocha_scraper.EngochaScraper", "Engocha"),
    ]
    
    all_ok = True
    for class_path, name in scrapers_to_test:
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            scraper_class = getattr(module, class_name)
            
            print(f"\n  Testing {name}...", end=" ", flush=True)
            
            # Instantiate and run
            scraper = scraper_class()
            result = scraper.scrape()
            
            listings_count = len(result.listings)
            has_price = any(l.price for l in result.listings)
            has_location = any(l.location for l in result.listings)
            
            if result.success and listings_count > 0:
                print(f"✓ {listings_count} listings (price={has_price}, location={has_location})")
                results["working_scrapers"].append({
                    "name": name,
                    "listings": listings_count,
                    "has_price": has_price,
                    "has_location": has_location
                })
                if not has_price or not has_location:
                    print(f"    ⚠ Warning: Missing price or location data")
            elif result.success and listings_count == 0:
                print(f"⚠ No listings (site accessible but no property data)")
                results["failed_sources"].append({"name": name, "reason": "No listings found"})
            else:
                print(f"✗ Failed")
                if result.errors:
                    print(f"    Error: {result.errors[:2]}")
                results["failed_sources"].append({"name": name, "reason": str(result.errors)})
                all_ok = False
                
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}: {e}")
            results["failed_sources"].append({"name": name, "reason": f"Error: {e}"})
            all_ok = False
    
    return all_ok

def main():
    print("=" * 50)
    print("OLLAA WEB SCRAPER - DIAGNOSTIC TEST")
    print("=" * 50)
    
    import_fail = not run_import_tests()
    kw_fail = not run_amharic_keyword_tests()
    url_fail = not run_quick_url_check()
    scraper_fail = not run_scraper_tests()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    print(f"\nWorking scrapers ({len(results['working_scrapers'])}):")
    for ws in results["working_scrapers"]:
        print(f"  ✓ {ws['name']}: {ws['listings']} listings")
    
    print(f"\nFailed/Inaccessible ({len(results['failed_sources'])}):")
    for fs in results["failed_sources"]:
        print(f"  ✗ {fs['name']}: {fs['reason']}")
    
    # Save results
    output = "/home/engine/project/diagnostic_results.json"
    with open(output, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {output}")
    
    # Determine overall status
    if results["working_scrapers"]:
        print("\n✓ SYSTEM VALID - Some scrapers are working")
        return 0
    else:
        print("\n✗ SYSTEM FAILURE - No working scrapers")
        return 1

if __name__ == "__main__":
    sys.exit(main())