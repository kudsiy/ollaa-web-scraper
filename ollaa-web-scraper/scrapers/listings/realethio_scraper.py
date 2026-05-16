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
            f"{self.base_url}/property-type/apartment-for-sale/",
            f"{self.base_url}/property-type/house-for-sale/",
            f"{self.base_url}/property-type/land-for-sale/",
            f"{self.base_url}/property-type/building-for-sale/",
            f"{self.base_url}/property-type/apartment-for-rent/",
            f"{self.base_url}/property-type/house-for-rent/",
            f"{self.base_url}/property-type/office-for-rent/",
            f"{self.base_url}/property-type/store-for-rent/",
        ]
