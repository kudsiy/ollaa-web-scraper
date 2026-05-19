"""
Ethio Real Estates listing scraper.
"""
import logging
from typing import Optional, List
from scrapers.listings.engocha_scraper import EngochaScraper
from scrapers.base_scraper import ScrapedListing

logger = logging.getLogger(__name__)

class EthioRealEstatesScraper(EngochaScraper):
    """
    Scraper for Ethio Real Estates.
    """
    
    base_url = "https://www.ethiorealestates.com"
    source_name = "Ethio Real Estates"
    
    async def _find_listing_pages(self) -> List[str]:
        """Find listing pages for Ethio Real Estates."""
        return [
            f"{self.base_url}/homes",
            f"{self.base_url}/rent",
            f"{self.base_url}/plots",
            f"{self.base_url}/commercial",
            f"{self.base_url}/property-search/",
        ]

    def _parse_listing_card(self, card) -> Optional[ScrapedListing]:
        listing = super()._parse_listing_card(card)
        if listing:
            # Ethio Real Estates specific adjustments
            if "Plots" in (listing.source_url or ""):
                listing.property_type = "land"
            elif "Commercial" in (listing.source_url or ""):
                listing.property_type = "office"
        return listing
