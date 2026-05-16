"""
eGP Ethiopia scraper.
"""
import logging
from typing import Optional
from scrapers.base_scraper import ScrapedListing
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class EGPScraper(BaseTenderScraper):
    """
    Scraper for eGP Ethiopia government portal.
    """
    
    base_url = "https://egp.gov.et/egp/bids/published"
    source_name = "eGP Ethiopia"
    item_selector = ".ant-table-tbody > tr"

    def _parse_tender_item(self, item) -> Optional[ScrapedListing]:
        """Custom parsing for eGP Ethiopia."""
        try:
            # The 3rd column is the title
            columns = item.select("td")
            if len(columns) < 3:
                return None
                
            title_td = columns[2]
            title = title_td.get_text(strip=True)
            
            if not title or len(title) < 5:
                return None
            
            # The title td usually has a click handler or a link
            # For now, we'll use the base URL since deep links are complex in this SPA
            link = self.base_url
            
            # Entity is 4th column, deadline is 8th
            entity = columns[3].get_text(strip=True) if len(columns) > 3 else ""
            deadline = columns[7].get_text(strip=True) if len(columns) > 7 else ""
            
            description = f"Entity: {entity} | Deadline: {deadline}"
            
            return self.create_listing(
                title=title,
                description=description,
                price=None,
                location=None,
                source_url=link,
                listing_type="tender",
                raw_data={"raw_html": str(item)[:500]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing eGP item: {e}")
            return None
