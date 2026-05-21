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
            "description": ".item-description, .description, .excerpt, p, .property-excerpt, .item-body, .listing-description",
            "date": ".item-date, .date, .time, .posted-on, .property-date, .listing-date, .post-date, .entry-date"
        }
        
        # Override with site-specific selectors if provided in registry (future enhancement)
        if "selectors" in config:
            self.selectors.update(config["selectors"])

    def scrape(self) -> ScrapeResult:
        """
        Scrape the site using the configured selectors and multi-page pagination.
        """
        start_time = datetime.now(timezone.utc)
        result = ScrapeResult(success=False)
        
        limit = self.config.scraper.fetch_limit
        max_pages = 50 # Safe upper limit for deep crawling
        reached_start_date = False
        
        try:
            # Try a few common paths if base_url is just the homepage
            paths = ["/", "/properties", "/listings", "/tenders", "/auctions", "/property-search", "/houses", "/all-properties"]
            
            # If the URL already has a path or query, just use it
            if "?" in self.base_url or (len(self.base_url.split("/")) > 4):
                paths = [""]
                
            for path in paths:
                if len(result.listings) >= limit or reached_start_date:
                    break
                    
                base_path_url = self._get_absolute_url(path)
                
                for page in range(1, max_pages + 1):
                    if len(result.listings) >= limit or reached_start_date:
                        break
                        
                    # Handle pagination
                    if page == 1:
                        url = base_path_url
                    else:
                        # Try common pagination patterns
                        if "?" in base_path_url:
                            url = f"{base_path_url}&page={page}"
                        else:
                            url = f"{base_path_url.rstrip('/')}/page/{page}/"

                    self.logger.info(f"Fetching {url}")
                    soup = self.scrape_page(url)
                    
                    if not soup:
                        break # Stop if page fails to load
                        
                    cards = soup.select(self.selectors["card"])
                    if not cards:
                        self.logger.info(f"No more cards found on {url}")
                        break # Stop if no cards found
                        
                    self.logger.info(f"Found {len(cards)} cards on {url}")
                    
                    page_listings_count = 0
                    for card in cards:
                        if len(result.listings) >= limit:
                            break
                            
                        listing = self.parse_listing_card(card, self.selectors)
                        if listing:
                            # Check if we should continue based on date
                            if listing.posted_date and not self.should_continue_crawling(listing.posted_date):
                                self.logger.info(f"Reached start_date limit at {listing.posted_date}")
                                reached_start_date = True
                                break
                                
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
                            page_listings_count += 1
                    
                    if page_listings_count == 0 and page > 1:
                        # If no valid listings on this page and it's not the first page, might be done
                        break
                        
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during generic scrape for {self.source_name}: {e}")
            result.errors.append(str(e))
            
        result.duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        return result
