"""
Living Ethio real estate listing scraper.
"""
import logging
from typing import Optional
from scrapers.listings.engocha_scraper import EngochaScraper
from scrapers.base_scraper import ScrapedListing

logger = logging.getLogger(__name__)

class LivingEthioScraper(EngochaScraper):
    """
    Scraper for Living Ethio real estate listings.
    """
    
    base_url = "https://livingethio.com"
    source_name = "Living Ethio"
    
    def _find_listing_pages(self):
        return [
            f"{self.base_url}/properties-2/",
            f"{self.base_url}/property-type/apartment/",
            f"{self.base_url}/property-type/house/",
            f"{self.base_url}/property-status/for-sale/",
            f"{self.base_url}/property-status/for-rent/",
        ]
    
    def _parse_listing_card(self, card) -> Optional[ScrapedListing]:
        """
        Custom parsing for Living Ethio.
        """
        listing = super()._parse_listing_card(card)
        if listing:
            # Clean up title
            listing.title = listing.title.replace("Addis Ababa Ethiopia", "").replace("Addis Ababa", "").strip()
            
            # Detect location if not found
            if not listing.location:
                # Often location is in the title after "in"
                import re
                match = re.search(r'in\s+([^,]+)', listing.title)
                if match:
                    listing.location = match.group(1).strip()
        
        return listing
