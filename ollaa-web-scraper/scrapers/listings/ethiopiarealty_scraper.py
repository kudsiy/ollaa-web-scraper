"""
Ethiopia Realty listing scraper.
Inherits from EngochaScraper but targets ethiopiarealty.com.
"""
import logging
from typing import List
from scrapers.listings.engocha_scraper import EngochaScraper

logger = logging.getLogger(__name__)

class EthiopiaRealtyScraper(EngochaScraper):
    """
    Scraper for Ethiopia Realty listings.
    """
    
    base_url = "https://ethiopiarealty.com"
    source_name = "Ethiopia Realty"
    
    async def _find_listing_pages(self) -> List[str]:
        """Find listing pages for Ethiopia Realty."""
        return [
            f"{self.base_url}/condominium-for-sale-in-addis-ababa-ethiopia/",
            f"{self.base_url}/houses-for-rent/",
            f"{self.base_url}/apartment-for-rent/",
            f"{self.base_url}/land-for-sale/",
            f"{self.base_url}/building-for-sale/",
            f"{self.base_url}/condominium-for-rent-2/",
            f"{self.base_url}/guest-house-for-rent/",
        ]
