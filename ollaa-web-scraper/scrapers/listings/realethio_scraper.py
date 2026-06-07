"""
Real Ethio scraper.
FIXED: Was inheriting EngochaScraper selectors. Now uses WordPressPropertyScraper.
"""
import logging
from typing import List
from scrapers.listings.wordpress_property_scraper import WordPressPropertyScraper

logger = logging.getLogger(__name__)


class RealEthioScraper(WordPressPropertyScraper):

    base_url = "https://realethio.com"
    source_name = "Real Ethio"

    async def _find_listing_pages(self) -> List[str]:
        return [
            f"{self.base_url}/properties/",
            f"{self.base_url}/property-type/apartment-for-sale/",
            f"{self.base_url}/property-type/house-for-sale/",
            f"{self.base_url}/property-type/land-for-sale/",
            f"{self.base_url}/property-type/apartment-for-rent/",
            f"{self.base_url}/property-type/house-for-rent/",
            f"{self.base_url}/property-type/office-for-rent/",
        ]
