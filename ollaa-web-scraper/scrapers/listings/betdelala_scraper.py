"""
BetDelala real estate listing scraper.
"""
import logging
from typing import Optional, List
from scrapers.listings.engocha_scraper import EngochaScraper
from scrapers.base_scraper import ScrapedListing

logger = logging.getLogger(__name__)

class BetDelalaScraper(EngochaScraper):
    """
    Scraper for BetDelala real estate listings.
    """
    
    base_url = "https://betdelala.com"
    source_name = "BetDelala"
    
    async def _find_listing_pages(self) -> List[str]:
        """Find listing pages for BetDelala."""
        return [
            f"{self.base_url}/home-list",
            f"{self.base_url}/home-list?type=sale",
            f"{self.base_url}/home-list?type=rent",
            f"{self.base_url}/ads-listing",
        ]

    def _parse_listing_card(self, card) -> Optional[ScrapedListing]:
        """
        Custom parsing for BetDelala cards.
        """
        listing = super()._parse_listing_card(card)
        if listing:
            # BetDelala specific adjustments
            if "Condominium" in listing.title:
                listing.property_type = "apartment"
            
            # Clean up title if it contains "Add to favorites" etc.
            listing.title = listing.title.replace("Add to favorites", "").replace("Add to compare", "").strip()
            
        return listing
