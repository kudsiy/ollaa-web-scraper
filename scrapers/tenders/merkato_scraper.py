"""
2Merkato Tenders scraper.
"""
import logging
from typing import Optional
from scrapers.base_scraper import ScrapedListing
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class MerkatoScraper(BaseTenderScraper):
    """
    Scraper for 2Merkato Tender notices.
    Specifically targets Land Lease and Real Estate.
    """
    
    base_url = "https://tender.2merkato.com/tenders"
    source_name = "2Merkato"
    item_selector = "div.bg-white.rounded-lg.p-4"

    def _parse_tender_item(self, item) -> Optional[ScrapedListing]:
        """Custom parsing for 2Merkato."""
        try:
            # Selector for 2Merkato titles
            title_elem = item.select_one("a.hover\\:text-blue-600.hover\\:underline")
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None
            
            # The link is the title itself
            link = self._get_absolute_url(title_elem.get("href"))
            
            # Metadata is usually in divs below the title
            metadata_divs = item.select("div.mt-2.text-sm.text-gray-600 div")
            description = ""
            for div in metadata_divs:
                description += div.get_text(strip=True) + " | "
                
            return self.create_listing(
                title=title,
                description=description.strip(" | "),
                price=None, # Usually not visible without subscription
                location=None,
                source_url=link,
                listing_type="tender",
                raw_data={"raw_html": str(item)[:500]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing 2Merkato item: {e}")
            return None
