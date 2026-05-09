"""
AddisList property scraper.
Scrapes property listings from addislist.com with source type filtering.
"""
import logging
import asyncio
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup
from scrapers.base_scraper import PlaywrightScraper, ScrapedListing, ScrapeResult
from parsers.price_extractor import PriceExtractor

logger = logging.getLogger(__name__)

class AddisListScraper(PlaywrightScraper):
    """
    Scraper for AddisList property listings.
    Filters by Bank, Court, and Government source types.
    """
    
    base_url = "https://addislist.com/properties/"
    source_name = "AddisList"
    
    def __init__(self):
        super().__init__()
        self.price_extractor = PriceExtractor()
        
    async def scrape_async(self) -> ScrapeResult:
        """
        Main scraping method for AddisList.
        """
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        try:
            await self._init_browser()
            
            source_types = ["Bank", "Court", "Government"]
            
            for st in source_types:
                self.logger.info(f"Scraping AddisList for source type: {st}")
                listings = await self._scrape_source_type(st)
                result.listings.extend(listings)
                
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during AddisList scrape: {e}")
            result.errors.append(str(e))
        finally:
            await self._close_browser()
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result

    def scrape(self) -> ScrapeResult:
        """Synchronous wrapper for scrape_async."""
        return asyncio.run(self.scrape_async())
        
    async def _scrape_source_type(self, source_type: str) -> List[ScrapedListing]:
        """Scrape listings for a specific source type using direct URL parameters."""
        listings = []
        page = await self.context.new_page()
        
        # Map source type to URL parameter
        type_param_map = {
            "Bank": "bank",
            "Court": "court",
            "Government": "government"
        }
        type_param = type_param_map.get(source_type, "bank")
        target_url = f"{self.base_url}?type={type_param}"
        
        try:
            self.logger.info(f"Navigating directly to: {target_url}")
            await asyncio.sleep(1)  # Throttling
            await page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            # Scrape the results
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Adjust selectors based on site structure
            listing_cards = soup.select(".item-listing, .property-item, .card")
            for card in listing_cards:
                listing = self._parse_listing_card(card, source_type)
                if listing:
                    listings.append(listing)
                    
        except Exception as e:
            self.logger.error(f"Error scraping source type {source_type}: {e}")
        finally:
            await page.close()
            
        return listings
        
    def _parse_listing_card(self, card, source_type: str) -> Optional[ScrapedListing]:
        """Parse a listing card from AddisList."""
        try:
            title_elem = card.select_one("h2, h3, .item-title, .title")
            price_elem = card.select_one(".item-price, .price")
            location_elem = card.select_one(".item-location, .location, address")
            link_elem = card.select_one("a[href]")
            
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self.price_extractor.extract(price_text)
            location = location_elem.get_text(strip=True) if location_elem else None
            
            link = self.base_url
            if link_elem:
                link = self._get_absolute_url(link_elem.get("href"))
                
            return self.create_listing(
                title=title,
                description=f"Source Type: {source_type}",
                price=price,
                location=location,
                source_url=link,
                raw_data={"source_type": source_type}
            )
        except Exception as e:
            self.logger.error(f"Error parsing AddisList card: {e}")
            return None
