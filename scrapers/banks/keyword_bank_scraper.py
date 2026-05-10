
"""
Unified scraper for banks using specific Amharic auction notice paths.
"""
import logging
import re
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper, ScrapedListing, ScrapeResult

logger = logging.getLogger(__name__)

class KeywordBankScraper(BaseScraper):
    """
    Generic scraper for banks that look for auction keywords in specific paths.
    """
    
    def __init__(self, source_name: str, base_url: str, auction_paths: List[str]):
        self.source_name = source_name
        self.base_url = base_url
        self.auction_paths = auction_paths
        super().__init__()
        
    def scrape(self) -> ScrapeResult:
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        try:
            self.logger.info(f"Starting {self.source_name} scrape")
            
            for path in self.auction_paths:
                url = self._get_absolute_url(path)
                self.logger.info(f"Fetching {url}")
                soup = self.scrape_page(url)
                if soup:
                    self._extract_listings_from_page(soup, result, url)
            
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during {self.source_name} scrape: {e}")
            result.errors.append(str(e))
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result
    
    def _extract_listings_from_page(self, soup: BeautifulSoup, result: ScrapeResult, current_url: str):
        """Extract listings from a page based on keywords."""
        # Common containers for bank notices
        containers = soup.select('article, .post, .entry, tr, .tender-item, .auction-item, .card, .notice-item, li')
        
        # Keywords: የሐራጅ (auction) or ሽያጭ (sale) or ቤት (house/property)
        keywords = ["የሐራጅ", "ሽያጭ", "ቤት"]
        
        for container in containers:
            text = container.get_text()
            if any(kw in text for kw in keywords):
                listing = self._parse_keyword_element(container, current_url)
                if listing:
                    result.listings.append(listing)

    def _parse_keyword_element(self, element, current_url: str) -> Optional[ScrapedListing]:
        """Parse an element into a ScrapedListing."""
        try:
            title_elem = element.select_one('h1, h2, h3, h4, .title, a, b, strong')
            title = title_elem.get_text(strip=True) if title_elem else f"{self.source_name} Auction"
            
            # Clean up title if it's too long
            if len(title) > 200:
                title = title[:197] + "..."
                
            # Skip if title is too short or just a generic word
            if len(title) < 5:
                return None
                
            price = self._extract_price(element.get_text())
            
            # Look for location (often near keywords like 'አድራሻ' or city names)
            location = None
            text = element.get_text()
            loc_match = re.search(r'(?:አድራሻ|ቦታ)[:\s]+([^,\n\.]+)', text)
            if loc_match:
                location = loc_match.group(1).strip()
            
            link_elem = element.select_one('a[href]')
            source_url = current_url
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                source_url = self._get_absolute_url(href)
            
            return self.create_listing(
                title=title,
                description=text[:500], # Keep first 500 chars as description
                price=price,
                location=location,
                source_url=source_url,
                listing_type="auction",
                raw_data={"element_html": str(element)[:1000]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing element: {e}")
            return None

    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text."""
        if not text:
            return None
        # Look for numbers followed by ETB, Birr, or Amharic equivalents
        patterns = [
            r'([\d,]+(?:\.\d{2})?)\s*(?:ETB|Birr|ብር|Br)',
            r'(?:ዋጋ|ብር)[:\s]+([\d,]+(?:\.\d{2})?)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    pass
        return None
