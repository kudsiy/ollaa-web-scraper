
"""
Jiji Ethiopia real estate listing scraper.
Uses Playwright to handle infinite scroll and JS rendering.
"""
import logging
import asyncio
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from scrapers.base_scraper import PlaywrightScraper, ScrapedListing, ScrapeResult
from parsers.price_extractor import PriceExtractor

logger = logging.getLogger(__name__)

class JijiScraper(PlaywrightScraper):
    """
    Scraper for Jiji Ethiopia property listings.
    Handles infinite scroll and dynamic content.
    """
    
    base_url = "https://jiji.com.et/real-estate"
    source_name = "Jiji Ethiopia"
    
    def __init__(self):
        super().__init__()
        self.price_extractor = PriceExtractor()
        
    async def scrape_async(self) -> ScrapeResult:
        """
        Main scraping method for Jiji.
        """
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        try:
            await self._init_browser()
            page = await self.context.new_page()
            
            # Use stealth-like headers and settings
            await page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/"
            })
            
            self.logger.info(f"Navigating to Jiji Real Estate: {self.base_url}")
            await page.goto(self.base_url, wait_until="networkidle", timeout=60000)
            
            # Wait for content to load, handle possible cloudflare check
            await asyncio.sleep(5)
            
            # Infinite scroll to load more listings
            self.logger.info("Performing infinite scroll to load more listings")
            last_height = await page.evaluate("document.body.scrollHeight")
            for i in range(5):  # Scroll 5 times to get a decent amount of data
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                self.logger.debug(f"Scroll iteration {i+1} complete")

            # Scrape the results
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Select listing cards
            listing_cards = soup.select(".b-list-advert-base, .qa-advert-list-item")
            self.logger.info(f"Found {len(listing_cards)} potential listing cards")
            
            for card in listing_cards:
                listing = self._parse_listing_card(card)
                if listing:
                    result.listings.append(listing)
                    
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during Jiji scrape: {e}")
            result.errors.append(str(e))
        finally:
            await self._close_browser()
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result

    def scrape(self) -> ScrapeResult:
        """Synchronous wrapper for scrape_async."""
        return asyncio.run(self.scrape_async())
        
    def _parse_listing_card(self, card) -> Optional[ScrapedListing]:
        """Parse a single listing card from Jiji."""
        try:
            # Jiji often uses classes starting with 'qa-' for key elements
            title_elem = card.select_one(".qa-advert-title, .b-advert-title-inner, .b-list-advert-base__title")
            price_elem = card.select_one(".qa-advert-price, .b-list-advert-base__price")
            location_elem = card.select_one(".b-list-advert-base__location, .b-list-advert-base__region")
            link_elem = card.select_one("a.js-handle-click-advert, a[href*='/ad/']")
            
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self.price_extractor.extract(price_text)
            location = location_elem.get_text(strip=True) if location_elem else None
            
            link = self.base_url
            if link_elem:
                href = link_elem.get("href")
                if href:
                    link = self._get_absolute_url(href)
                
            # Attempt to extract more details from the title/text
            text_context = title + " " + (card.get_text(strip=True) or "")
            
            return self.create_listing(
                title=title,
                description=f"Property listing on Jiji: {title}",
                price=price,
                location=location,
                source_url=link,
                listing_type="sale",
                raw_data={"raw_text": card.get_text(separator=" ", strip=True)}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing Jiji card: {e}")
            return None
