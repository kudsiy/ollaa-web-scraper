"""
Reporter Tenders scraper.
"""
import logging
from typing import Optional
from scrapers.base_scraper import ScrapedListing
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class ReporterTendersScraper(BaseTenderScraper):
    """
    Scraper for Reporter Tenders notices.
    """
    
    base_url = "https://reportertenders.com/all-tenders/"
    source_name = "Reporter Tenders"
    item_selector = ".rtcl-listing-item"

    def _parse_tender_item(self, item) -> Optional[ScrapedListing]:
        """Custom parsing for Reporter Tenders."""
        try:
            title_elem = item.select_one(".rtin-title a, h3 a")
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None
            
            link = self._get_absolute_url(title_elem.get("href"))
            
            # Metadata usually in .rtin-meta or similar
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
            self.logger.debug(f"Error parsing Reporter Tenders item: {e}")
            return None
