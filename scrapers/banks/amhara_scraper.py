"""
Amhara Bank scraper.
Scrapes property listings from Amhara Bank (Facebook page).
"""
import logging
from scrapers.base_scraper import BaseScraper, ScrapedListing, ScrapeResult
from datetime import datetime

logger = logging.getLogger(__name__)


class AmharaBankScraper(BaseScraper):
    """
    Scraper for Amhara Bank property listings.
    """
    
    base_url = "https://www.amharabank.com.et"
    source_name = "Amhara Bank"
    
    def scrape(self) -> ScrapeResult:
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        try:
            self.logger.info("Starting Amhara Bank scrape")
            
            pages_to_try = [
                f"{self.base_url}/news",
                f"{self.base_url}/notice",
            ]
            
            for url in pages_to_try:
                self.logger.info(f"Fetching {url}")
                soup = self.scrape_page(url)
                if soup:
                    cards = soup.select('.post, article, .userContentWrapper, [data-ad-preview]')
                    self.logger.info(f"Found {len(cards)} cards on {url}")
                    
                    for card in cards:
                        listing = self._parse_card(card)
                        if listing:
                            result.listings.append(listing)
            
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during Amhara Bank scrape: {e}")
            result.errors.append(str(e))
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result
    
    def _parse_card(self, card) -> ScrapedListing:
        """Parse a card element."""
        try:
            title_elem = card.select_one('h2, h3, h4, a')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                text_content = card.get_text()[:200]
                if text_content:
                    title = text_content.split('\n')[0][:100]
                else:
                    return None
            
            price_elem = card.select_one('.price, [data-ad-price], .amount')
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self._extract_price(price_text) if price_text else None
            
            location_elem = card.select_one('.location, .address, [data-ad-location]')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            link_elem = card.select_one('a[href]')
            source_url = self.base_url
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if href.startswith('http'):
                    source_url = href
            
            return self.create_listing(
                title=title,
                description="",
                price=price,
                location=location,
                source_url=source_url,
                listing_type="auction",
                raw_data={"source": "amhara_bank"}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing card: {e}")
            return None
    
    def _extract_price(self, text: str) -> float:
        """Extract price from text."""
        if not text:
            return None
        import re
        patterns = [
            r'([\d,]+(?:\.\d{2})?)\s*(?:ETB|Birr|ብር|Br)?',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    pass
        return None
