"""
Berhan Bank auction scraper.
"""
import logging
import re
from scrapers.base_scraper import BaseScraper, ScrapedListing, ScrapeResult
from datetime import datetime

logger = logging.getLogger(__name__)


class BerhanBankScraper(BaseScraper):
    """
    Scraper for Berhan Bank foreclosure auctions.
    """
    
    base_url = "https://berhanbanksc.com"
    source_name = "Berhan Bank"
    
    def scrape(self) -> ScrapeResult:
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        try:
            self.logger.info("Starting Berhan Bank scrape")
            
            auction_paths = ["/auctions", "/category/auction", "/የሐራጅ-ሽያጭ"]
            
            for path in auction_paths:
                url = self._get_absolute_url(path)
                self.logger.info(f"Fetching {url}")
                soup = self.scrape_page(url)
                if soup:
                    self._extract_listings_from_page(soup, result)
            
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during Berhan Bank scrape: {e}")
            result.errors.append(str(e))
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result
    
    def _extract_listings_from_page(self, soup, result):
        """Extract listings from a page."""
        cards = soup.select('article, .post, .entry, tr, .tender-item, .auction-item')
        
        for card in cards:
            text = card.get_text()
            if "ሐራጅ" in text or "Auction" in text or "auction" in text.lower():
                listing = self._parse_card_element(card)
                if listing:
                    result.listings.append(listing)
    
    def _parse_card_element(self, card) -> ScrapedListing:
        """Parse a card element into a ScrapedListing."""
        try:
            title_elem = card.select_one('h1, h2, h3, h4, .title, a')
            title = title_elem.get_text(strip=True) if title_elem else "Berhan Bank Auction"
            
            price_elem = card.select_one('.price, .amount, .cost')
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self._extract_price(price_text)
            
            desc_elem = card.select_one('p, .description, .content')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            location_elem = card.select_one('.location, .address, .region')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            link_elem = card.select_one('a[href]')
            source_url = self.base_url
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if href.startswith('http'):
                    source_url = href
                else:
                    source_url = self._get_absolute_url(href)
            
            return self.create_listing(
                title=title,
                description=description,
                price=price,
                location=location,
                source_url=source_url,
                listing_type="auction",
                raw_data={"card_html": str(card)}
            )
        except Exception as e:
            self.logger.error(f"Error parsing card: {e}")
            return None
    
    def _extract_price(self, text: str) -> float:
        """Extract price from text."""
        if not text:
            return None
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
