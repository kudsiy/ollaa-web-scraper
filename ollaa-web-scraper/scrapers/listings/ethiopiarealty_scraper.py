"""
Ethiopia Realty scraper.
FIXED: Was inheriting EngochaScraper selectors. Now uses WordPressPropertyScraper.
"""
import logging
from typing import List
from scrapers.listings.wordpress_property_scraper import WordPressPropertyScraper

logger = logging.getLogger(__name__)


class EthiopiaRealtyScraper(WordPressPropertyScraper):

    base_url = "https://ethiopiarealty.com"
    source_name = "Ethiopia Realty"

    async def _find_listing_pages(self) -> List[str]:
        return [
            f"{self.base_url}/properties/",
            f"{self.base_url}/condominium-for-sale-in-addis-ababa-ethiopia/",
            f"{self.base_url}/houses-for-rent/",
            f"{self.base_url}/apartment-for-rent/",
            f"{self.base_url}/land-for-sale/",
            f"{self.base_url}/building-for-sale/",
        ]
