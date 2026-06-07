"""
Living Ethio scraper.
FIXED: Was inheriting EngochaScraper selectors. Now uses WordPressPropertyScraper.
"""
import logging
import re
from typing import List, Optional
from scrapers.listings.wordpress_property_scraper import WordPressPropertyScraper
from scrapers.base_scraper import ScrapedListing

logger = logging.getLogger(__name__)


class LivingEthioScraper(WordPressPropertyScraper):

    base_url = "https://livingethio.com"
    source_name = "Living Ethio"

    async def _find_listing_pages(self) -> List[str]:
        return [
            f"{self.base_url}/properties/",
            f"{self.base_url}/properties/?status=for-sale",
            f"{self.base_url}/properties/?status=for-rent",
            f"{self.base_url}/property-type/apartment/",
            f"{self.base_url}/property-type/house/",
        ]

    def _parse_listing_card(self, card) -> Optional[ScrapedListing]:
        listing = super()._parse_listing_card(card)
        if listing:
            listing.title = re.sub(
                r'\s*[-|]\s*(?:Addis Ababa(?:\s+Ethiopia)?|Ethiopia)\s*$',
                '', listing.title, flags=re.IGNORECASE
            ).strip()
        return listing
