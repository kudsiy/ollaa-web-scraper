"""
Auction Ethiopia scraper.
Scrapes property listings from auction.et.
"""
import logging
from scrapers.base_scraper import BaseScraper, ScrapedListing, ScrapeResult
from datetime import datetime

logger = logging.getLogger(__name__)


class AuctionEthiopiaScraper(BaseScraper):
    """
    Scraper for Auction Ethiopia property listings.
    """
    
    base_url = "https://auction.et"
    source_name = "Auction Ethiopia"
    
    def scrape(self) -> ScrapeResult:
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        try:
            self.logger.info("Starting Auction Ethiopia scrape")
            
            pages_to_try = [
                f"{self.base_url}/",
                f"{self.base_url}/properties",
                f"{self.base_url}/listings",
                f"{self.base_url}/tenders",
                f"{self.base_url}/auctions",
                f"{self.base_url}/property-search",
            ]
            
            for url in pages_to_try:
                self.logger.info(f"Fetching {url}")
                soup = self.scrape_page(url)
                if soup:
                    cards = soup.select('.listing-card, .property-card, .auction-item, article, .item')
                    self.logger.info(f"Found {len(cards)} cards on {url}")
                    
                    for card in cards:
                        listing = self._parse_card(card)
                        if listing:
                            result.listings.append(listing)
            
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during Auction Ethiopia scrape: {e}")
            result.errors.append(str(e))
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result
    
    def _parse_card(self, card) -> ScrapedListing:
        """Parse a card element."""
        try:
            title_elem = card.select_one('h2, h3, h4, .title, .listing-title, a')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                return None
            
            price_elem = card.select_one('.price, .listing-price, [class*="price"]')
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self._extract_price(price_text) if price_text else None
            
            location_elem = card.select_one('.location, .address, [class*="location"]')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            desc_elem = card.select_one('.description, p')
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
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
                description=description[:500] if description else "",
                price=price,
                location=location,
                source_url=source_url,
                listing_type="auction",
                raw_data={"source": "auction_ethiopia"}
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
