"""
Ethiopian Tender scraper.
"""
import logging
from typing import Optional
from scrapers.base_scraper import ScrapedListing
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class EthiopianTenderScraper(BaseTenderScraper):
    """
    Scraper for Ethiopian Tender notices.
    """
    
    base_url = "https://www.ethiopiantender.com"
    source_name = "Ethiopian Tender"
    item_selector = "div.tender-table-wrapper"

    def _parse_tender_item(self, item) -> Optional[ScrapedListing]:
        """Custom parsing for Ethiopian Tender."""
        try:
            title_elem = item.select_one("a.tender-title-link")
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None
            
            link = self._get_absolute_url(title_elem.get("href"))
            
            # Metadata is in divs
            metadata_divs = item.select("div")
            description = ""
            for div in metadata_divs:
                text = div.get_text(strip=True)
                if text:
                    description += text + " | "
                
            return self.create_listing(
                title=title,
                description=description.strip(" | "),
                price=None,
                location=None,
                source_url=link,
                listing_type="tender",
                raw_data={"raw_html": str(item)[:500]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing Ethiopian Tender item: {e}")
            return None
