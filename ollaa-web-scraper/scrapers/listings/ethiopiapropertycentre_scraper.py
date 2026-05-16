"""
Ethiopia Property Centre listing scraper.
"""
import logging
from typing import Optional
from scrapers.listings.engocha_scraper import EngochaScraper
from scrapers.base_scraper import ScrapedListing

logger = logging.getLogger(__name__)

class EthiopiaPropertyCentreScraper(EngochaScraper):
    """
    Scraper for Ethiopia Property Centre listings.
    """
    
    base_url = "https://ethiopiapropertycentre.com"
    source_name = "Ethiopia Property Centre"
    
    def _find_listing_pages(self):
        return [
            f"{self.base_url}/for-sale",
            f"{self.base_url}/for-rent",
            f"{self.base_url}/for-sale/apartments",
            f"{self.base_url}/for-sale/houses",
        ]

    def _parse_listing_card(self, card) -> Optional[ScrapedListing]:
        listing = super()._parse_listing_card(card)
        if listing:
            # Custom parsing for Ethiopia Property Centre
            # They often have "Added on" or "Updated on" in the text
            if listing.description:
                import re
                date_match = re.search(r'Added on\s+([\d\s\w,]+)', listing.description)
                if date_match:
                    # We could parse the date here if needed
                    pass
        return listing
