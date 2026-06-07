"""
Ethio Real Estates scraper.
FIXED: Was inheriting EngochaScraper selectors. Now uses WordPressPropertyScraper.
"""
import logging
from typing import List
from scrapers.listings.wordpress_property_scraper import WordPressPropertyScraper

logger = logging.getLogger(__name__)


class EthioRealEstatesScraper(WordPressPropertyScraper):

    base_url = "https://www.ethiorealestates.com"
    source_name = "Ethio Real Estates"

    async def _find_listing_pages(self) -> List[str]:
        return [
            f"{self.base_url}/properties/",
            f"{self.base_url}/homes/",
            f"{self.base_url}/rent/",
            f"{self.base_url}/plots/",
            f"{self.base_url}/commercial/",
        ]
