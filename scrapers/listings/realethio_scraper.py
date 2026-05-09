"""
Real Ethio listing scraper.
"""
import logging
from scrapers.listings.engocha_scraper import EngochaScraper

logger = logging.getLogger(__name__)

class RealEthioScraper(EngochaScraper):
    """
    Scraper for Real Ethio listings.
    """
    
    base_url = "https://realethio.com"
    source_name = "Real Ethio"
    
    def _find_listing_pages(self):
        return [
            f"{self.base_url}/property-listings/",
        ]
