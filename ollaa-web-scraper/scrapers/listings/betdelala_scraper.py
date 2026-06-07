"""
BetDelala scraper.
FIXED: Was inheriting EngochaScraper selectors. Now uses WordPressPropertyScraper.
"""
import logging
from typing import List
from scrapers.listings.wordpress_property_scraper import WordPressPropertyScraper

logger = logging.getLogger(__name__)


class BetDelalaScraper(WordPressPropertyScraper):

    base_url = "https://betdelala.com"
    source_name = "BetDelala"

    async def _find_listing_pages(self) -> List[str]:
        return [
            f"{self.base_url}/properties/",
            f"{self.base_url}/properties/?status=for-sale",
            f"{self.base_url}/properties/?status=for-rent",
            f"{self.base_url}/home-list/",
            f"{self.base_url}/ads-listing/",
        ]
