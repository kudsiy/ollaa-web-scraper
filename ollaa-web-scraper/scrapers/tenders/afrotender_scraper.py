"""
AfroTender scraper.
"""
import logging
import asyncio
from typing import Optional
from scrapers.base_scraper import ScrapedListing, ScrapeResult
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class AfroTenderScraper(BaseTenderScraper):
    """
    Scraper for AfroTender notices.
    """
    item_selector = ".col-lg-6.mb-4, .tender-card, article.tender"

    def scrape(self) -> ScrapeResult:
        return asyncio.run(self.scrape_async())
    
    base_url = "https://afrotender.com/publictenders"
    source_name = "AfroTender"

    def _parse_tender_item(self, item) -> Optional[ScrapedListing]:
        """Custom parsing for AfroTender."""
        try:
            title_elem = item.select_one("h4")
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None
            
            # Link is usually the parent or contains the title
            link_elem = item.select_one("a")
            link = self._get_absolute_url(link_elem.get("href")) if link_elem else self.base_url
            
            description = item.get_text(separator=" | ", strip=True)
            
            return self.create_listing(
                title=title,
                description=description[:1000],
                price=None,
                location=None,
                source_url=link,
                listing_type="tender",
                raw_data={"raw_html": str(item)[:500]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing AfroTender item: {e}")
            return None
