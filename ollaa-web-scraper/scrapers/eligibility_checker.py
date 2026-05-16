"""
Eligibility checker for validating sources in the registry.
Performs automated checks to ensure sources are reachable and contain relevant content.
"""
import logging
import requests
from typing import Dict, Any, List
from source_registry import SOURCE_REGISTRY, iter_sources

logger = logging.getLogger(__name__)

class EligibilityChecker:
    """
    Validates sources in the registry.
    """
    
    def __init__(self, user_agent: str):
        self.headers = {"User-Agent": user_agent}

    def check_source(self, source_key: str) -> Dict[str, Any]:
        """
        Check if a source is reachable and appears valid.
        """
        config = SOURCE_REGISTRY.get(source_key)
        if not config:
            return {"status": "missing", "error": "Source not found in registry"}
        
        url = config.get("url")
        if not url:
            return {"status": "invalid", "error": "No URL configured"}
            
        if config.get("category") == "telegram":
            # Basic reachability for telegram preview page
            url = f"https://t.me/s/{config.get('channel_id')}"

        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                # Check for some keywords in content to ensure it's not a landing page or block page
                content_lower = response.text.lower()
                relevant_keywords = ["property", "house", "bank", "auction", "sale", "ቤት", "ሽያጭ", "ጨረታ"]
                has_keywords = any(kw in content_lower for kw in relevant_keywords)
                
                return {
                    "status": "active" if has_keywords else "unclear",
                    "status_code": response.status_code,
                    "has_keywords": has_keywords,
                    "url": url
                }
            else:
                return {
                    "status": "error",
                    "status_code": response.status_code,
                    "url": url
                }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "url": url
            }

    def check_all_sources(self) -> Dict[str, Dict[str, Any]]:
        """Run eligibility checks on all registered sources."""
        results = {}
        for key, _ in iter_sources():
            logger.info(f"Checking eligibility for {key}...")
            results[key] = self.check_source(key)
        return results

if __name__ == "__main__":
    from config import get_config
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    checker = EligibilityChecker(config.scraper.user_agent)
    report = checker.check_all_sources()
    
    for source, res in report.items():
        print(f"{source}: {res['status']} ({res.get('status_code', 'N/A')})")
