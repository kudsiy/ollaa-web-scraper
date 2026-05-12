"""
Auction Ethiopia scraper.
"""
import logging
import asyncio
from typing import Optional
from scrapers.base_scraper import ScrapedListing, ScrapeResult
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class AuctionEthiopiaScraper(BaseTenderScraper):
    """
    Scraper for Auction Ethiopia (auction.et).
    """
    
    base_url = "https://auction.et"
    source_name = "Auction Ethiopia"
    item_selector = "div.grid-item, div.auction-item, h3" # Fallback selectors

    async def scrape_async(self) -> ScrapeResult:
        """Override to handle popups and view switching."""
        start_time = self.utcnow()
        result = ScrapeResult(success=False)
        
        try:
            await self._init_browser()
            page = await self.context.new_page()
            
            # Navigate to the list view directly if possible, or just the homepage
            await page.goto(self.base_url, wait_until="networkidle", timeout=60000)
            
            # Handle the potential video popup
            try:
                # Look for close button or "No, Thanks"
                close_button = await page.get_by_text("No, Thanks", exact=False)
                if await close_button.is_visible():
                    await close_button.click()
                else:
                    # Try clicking outside or pressing Escape
                    await page.keyboard.press("Escape")
            except Exception:
                pass
                
            await asyncio.sleep(2)
            
            # Identify items - the site structure is a bit dynamic
            content = await page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            
            # The browser subagent found that titles are in h3 tags
            # We'll look for containers that have h3 tags
            auction_items = []
            for h3 in soup.select("h3"):
                parent = h3.find_parent("div")
                if parent:
                    auction_items.append(parent)
            
            self.logger.info(f"Found {len(auction_items)} potential auction items on {self.source_name}")
            
            for item in auction_items:
                listing = self._parse_tender_item(item)
                if listing:
                    result.listings.append(listing)
                    
            result.success = True
            result.scraped_count = len(result.listings)
            await page.close()
            
        except Exception as e:
            self.logger.error(f"Error during {self.source_name} scrape: {e}")
            result.errors.append(str(e))
        finally:
            await self._close_browser()
            
        result.duration_seconds = (self.utcnow() - start_time).total_seconds()
        return result

    def _parse_tender_item(self, item) -> Optional[ScrapedListing]:
        """Custom parsing for Auction Ethiopia."""
        try:
            title_elem = item.select_one("h3")
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None
            
            # Link is usually a "Details" button or similar
            link_elem = item.select_one("a, button")
            link = self.base_url
            if link_elem and link_elem.name == "a":
                link = self._get_absolute_url(link_elem.get("href"))
            
            # Extract price if possible
            description = item.get_text(separator=" | ", strip=True)
            price = self.price_extractor.extract(description)
            
            return self.create_listing(
                title=title,
                description=description[:1000],
                price=price,
                location=None,
                source_url=link,
                listing_type="auction",
                raw_data={"raw_html": str(item)[:500]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing Auction Ethiopia item: {e}")
            return None

    def utcnow(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc)
