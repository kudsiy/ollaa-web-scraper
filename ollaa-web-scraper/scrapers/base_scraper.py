"""
Base scraper abstract class that all site-specific scrapers inherit from.
Provides common functionality for HTTP requests, rate limiting, and error handling.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, ClassVar
import logging
import random
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import get_config
from parsers.ocr_engine import OCREngine


logger = logging.getLogger(__name__)


@dataclass
class ScrapedListing:
    """Represents a single scraped property listing."""
    source_url: str
    source_name: str
    title: str
    source_key: Optional[str] = None
    description: str = ""
    price: Optional[float] = None
    price_currency: str = "ETB"
    property_type: Optional[str] = None
    location: Optional[str] = None
    area_sqm: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    images: List[str] = field(default_factory=list)
    posted_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    listing_type: str = "auction"
    raw_data: Dict[str, Any] = field(default_factory=dict)
    scraped_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ScrapeResult:
    """Result of a scraping operation."""
    success: bool
    listings: List[ScrapedListing] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    scraped_count: int = 0
    new_count: int = 0
    duration_seconds: float = 0.0


class BaseScraper(ABC):
    """
    Abstract base class for all web scrapers.
    
    Inherited by:
    - Bank scrapers (CBE, Awash, etc.)
    - Tender scrapers (PPAA, etc.)
    - Listing scrapers (Engocha, etc.)
    """
    
    base_url: ClassVar[str] = ""
    source_name: ClassVar[str] = ""
    
    def __init__(self):
        self.config = get_config()
        self.session = self._create_session()
        self.ocr_engine = OCREngine()
        self.logger = logging.getLogger(self.source_name)
        
    def _create_session(self) -> requests.Session:
        """Create a configured requests session."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.config.scraper.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        })
        return session
    
    def _rate_limit(self) -> None:
        """Apply random delay between requests to avoid blocking."""
        delay = random.uniform(
            self.config.scraper.request_delay_min,
            self.config.scraper.request_delay_max
        )
        time.sleep(delay)
    
    def _fetch_page(self, url: str, retries: Optional[int] = None) -> Optional[BeautifulSoup]:
        """
        Fetch a URL and parse it with BeautifulSoup.
        
        Args:
            url: The URL to fetch
            retries: Number of retry attempts (defaults to config.max_retries)
            
        Returns:
            BeautifulSoup object or None if fetch failed
        """
        if retries is None:
            retries = self.config.scraper.max_retries
            
        for attempt in range(retries + 1):
            try:
                self._rate_limit()
                response = self.session.get(
                    url,
                    timeout=self.config.scraper.request_timeout
                )
                response.raise_for_status()
                
                # Try to use lxml if available for better parsing
                parser = "lxml"
                try:
                    import lxml
                except ImportError:
                    parser = "html.parser"
                    
                return BeautifulSoup(response.content, parser)
            except requests.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries:
                    time.sleep(self.config.scraper.retry_delay)
                else:
                    self.logger.error(f"Failed to fetch {url} after {retries + 1} attempts")
                    return None
        return None
    
    def _get_absolute_url(self, relative_url: str, base: Optional[str] = None) -> str:
        """Convert relative URL to absolute URL."""
        return urljoin(base or self.base_url, relative_url)
    
    @abstractmethod
    def scrape(self) -> ScrapeResult:
        """
        Main scraping method - must be implemented by subclasses.
        
        Returns:
            ScrapeResult containing scraped listings and metadata
        """
        pass
    
    def scrape_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Convenience method to fetch a specific page.
        
        Args:
            url: The URL to fetch
            
        Returns:
            BeautifulSoup object or None if fetch failed
        """
        return self._fetch_page(url)
    
    def parse_listing_card(self, card_element, selectors: Dict[str, str]) -> Optional[ScrapedListing]:
        """
        Parse a listing card/element using CSS selectors.
        
        Args:
            card_element: BeautifulSoup element representing a listing
            selectors: Dict mapping field names to CSS selectors
            
        Returns:
            ScrapedListing or None if parsing failed
        """
        try:
            title_elem = card_element.select_one(selectors.get("title", ""))
            price_elem = card_element.select_one(selectors.get("price", ""))
            location_elem = card_element.select_one(selectors.get("location", ""))
            desc_elem = card_element.select_one(selectors.get("description", ""))
            
            title = title_elem.get_text(strip=True) if title_elem else "Untitled"
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            
            from parsers.price_extractor import PriceExtractor
            extractor = PriceExtractor()
            price = extractor.extract(price_text)
            
            listing = ScrapedListing(
                source_url=self.base_url,
                source_name=self.source_name,
                title=title,
                description=desc_elem.get_text(strip=True) if desc_elem else "",
                price=price,
                location=location_elem.get_text(strip=True) if location_elem else None,
                raw_data={"raw_html": str(card_element)}
            )
            return listing
        except Exception as e:
            self.logger.error(f"Error parsing listing card: {e}")
            return None
    
    def create_listing(self, **kwargs) -> ScrapedListing:
        """Factory method to create a ScrapedListing with defaults."""
        data = {
            "source_url": self.base_url,
            "source_name": self.source_name,
            "scraped_at": datetime.utcnow()
        }
        data.update(kwargs)
        return ScrapedListing(**data)


class PlaywrightScraper(BaseScraper):
    """
    Base scraper using Playwright for JavaScript-rendered pages.
    Used for sites that require client-side rendering.
    """
    
    def __init__(self):
        super().__init__()
        self.browser = None
        self.context = None
    
    async def _init_browser(self):
        """Initialize Playwright browser (to be called from async context)."""
        from playwright.async_api import async_playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent=self.config.scraper.user_agent,
            ignore_https_errors=True
        )
    
    async def _close_browser(self):
        """Close Playwright browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def _fetch_page_js(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL using Playwright for JS rendering."""
        page = await self.context.new_page()
        try:
            timeout_ms = self.config.scraper.request_timeout * 1000
            await page.goto(url, timeout=timeout_ms)
            try:
                await page.wait_for_load_state("networkidle", timeout=timeout_ms)
            except Exception:
                self.logger.debug(f"networkidle timeout on {url}, continuing with loaded content")
                pass
            content = await page.content()
            return BeautifulSoup(content, "html.parser")
        except Exception as e:
            self.logger.error(f"Playwright fetch failed for {url}: {e}")
            return None
        finally:
            await page.close()

    def _try_alternate_domains(self, url: str, alt_domains: list = None) -> Optional[BeautifulSoup]:
        """
        Try fetching a URL with alternate domains if the primary fails.
        Handles ERR_NAME_NOT_RESOLVED by trying known working mirrors/alternates.
        
        Args:
            url: The original URL that failed
            alt_domains: List of (alt_url, alt_name) tuples to try
            
        Returns:
            BeautifulSoup object or None
        """
        if not alt_domains:
            return None
            
        for alt_url, alt_name in alt_domains:
            self.logger.info(f"Trying alternate domain: {alt_name} -> {alt_url}")
            result = self._fetch_page(alt_url)
            if result:
                self.logger.info(f"Alternate domain {alt_name} succeeded")
                return result
                
        return None