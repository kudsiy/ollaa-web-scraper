"""
Generic scraper that uses configuration for site-specific parsing.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, ScrapedListing, ScrapeResult
from source_registry import SOURCE_REGISTRY

logger = logging.getLogger(__name__)

class GenericScraper(BaseScraper):
    """
    A configurable scraper that can handle multiple sites using standard patterns.
    """
    
    def __init__(self, source_key: str):
        if source_key not in SOURCE_REGISTRY:
            raise ValueError(f"Unknown source key: {source_key}")
            
        config = SOURCE_REGISTRY[source_key]
        self.source_key = source_key
        self.base_url = config["url"]
        self.source_name = config["name"]
        super().__init__()
        
        # Default selectors that work for many WordPress/Houzez based sites in Ethiopia
        self.selectors = {
            "card": ".item-listing, .property-item, .card, article, .post, .listing-item, .property-card, .list-item, .item-wrap, .property-item-card",
            "title": "h2 a, h3 a, .item-title a, .title a, a.link, .listing-title a, .property-title a, .item-title, h4 a",
            "price": ".item-price, .price, .listing-price, .amount, .property-price, .text-price, .price-tag, .item-price-text",
            "location": ".item-address, address, .location, .area, .property-location, .item-location, .location-text, .item-sub-title",
            "description": ".item-description, .description, .excerpt, p, .property-excerpt, .item-body, .listing-description"
        }
        
        # Override with site-specific selectors if provided in registry (future enhancement)
        if "selectors" in config:
            self.selectors.update(config["selectors"])

    def scrape(self) -> ScrapeResult:
        """
        Scrape the site using the configured selectors.
        """
        start_time = datetime.now(timezone.utc)
        result = ScrapeResult(success=False)
        
        try:
            # Try a few common paths if base_url is just the homepage
            paths = ["/", "/properties", "/listings", "/tenders", "/auctions", "/property-search", "/houses", "/all-properties"]
            
            # If the URL already has a path or query, just use it
            if "?" in self.base_url or (len(self.base_url.split("/")) > 4):
                paths = [""]
                
            for path in paths:
                url = self._get_absolute_url(path)
                self.logger.info(f"Fetching {url}")
                soup = self.scrape_page(url)
                
                if not soup:
                    continue
                    
                cards = soup.select(self.selectors["card"])
                self.logger.info(f"Found {len(cards)} cards on {url}")
                
                for card in cards:
                    listing = self.parse_listing_card(card, self.selectors)
                    if listing:
                        # Ensure we have a valid source URL
                        if listing.source_url == self.base_url or not listing.source_url:
                            # Try to find a link in the card
                            link_elem = card.select_one("a[href]")
                            if link_elem:
                                listing.source_url = self._get_absolute_url(link_elem.get("href"))
                        
                        # Add metadata
                        listing.raw_data["source_key"] = self.source_key
                        listing.raw_data["filter_url"] = url
                        
                        # Determine listing type
                        config = SOURCE_REGISTRY[self.source_key]
                        if config["valuation_signal"] in ["liquidation_value", "primary_auction"]:
                            listing.listing_type = "auction"
                        else:
                            listing.listing_type = "market"
                            
                        result.listings.append(listing)
                        
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during generic scrape for {self.source_name}: {e}")
            result.errors.append(str(e))
            
        result.duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        return result
