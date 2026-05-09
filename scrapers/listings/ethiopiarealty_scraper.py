"""
Ethiopia Realty listing scraper.
"""
import logging
from scrapers.listings.engocha_scraper import EngochaScraper

logger = logging.getLogger(__name__)

class EthiopiaRealtyScraper(EngochaScraper):
    """
    Scraper for Ethiopia Realty listings.
    """
    
    base_url = "https://ethiopiarealty.com"
    source_name = "Ethiopia Realty"
    
    def _find_listing_pages(self):
        return [
            f"{self.base_url}/properties/",
        ]
