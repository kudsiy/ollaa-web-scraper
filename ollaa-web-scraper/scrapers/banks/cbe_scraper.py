"""
Commercial Bank of Ethiopia auction scraper.
Uses Playwright to bypass blocks and handle dynamic content.

FIX APPLIED:
  - base_url changed from combanketh.et (dead — ERR_NAME_NOT_RESOLVED) to combanketh.com
  - Added /en/auction-notice and /en/property-auction as top-priority paths
  - Reduced path list to avoid wasting 30s timeout × 8 dead paths per run
"""
import logging
import asyncio
import re
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from scrapers.base_scraper import PlaywrightScraper, ScrapedListing, ScrapeResult
from parsers.price_extractor import PriceExtractor

logger = logging.getLogger(__name__)

class CBEScraper(PlaywrightScraper):
    """
    Scraper for Commercial Bank of Ethiopia (CBE) foreclosure auctions.
    """
    
    # FIX: was "https://www.combanketh.et" — DNS dead as of May 2026
    base_url = "https://www.combanketh.com"
    source_name = "Commercial Bank of Ethiopia"
    
    def __init__(self):
        super().__init__()
        self.price_extractor = PriceExtractor()

    def scrape(self) -> ScrapeResult:
        """Synchronous wrapper required by base class."""
        import asyncio
        return asyncio.run(self.scrape_async())
        
    async def scrape_async(self) -> ScrapeResult:
        """
        Main scraping method for CBE.
        """
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        limit = self.config.scraper.fetch_limit
        timeout_ms = self.config.scraper.request_timeout * 1000
        
        try:
            await self._init_browser()
            page = await self.context.new_page()
            
            # Prioritized paths — most likely first to fail fast if wrong
            # TODO: verify correct path by visiting combanketh.com manually
            auction_paths = [
                "/en/auction-notice",
                "/en/property-auction",
                "/en/notices",
                "/en/foreclosure",
                "/en/notices/auction",
                "/notices",
            ]
            
            for path in auction_paths:
                if len(result.listings) >= limit:
                    break
                    
                url = self._get_absolute_url(path)
                self.logger.info(f"Navigating to CBE Notices: {url}")
                
                try:
                    response = await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                    if not response or response.status >= 400:
                        self.logger.warning(f"HTTP {response.status if response else 'N/A'} for {url}")
                        continue

                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    listings = self._extract_auction_listings(soup, url)
                    result.listings.extend(listings)
                    
                    if listings:
                        self.logger.info(f"Found {len(listings)} listings at {url}")
                        break  # Stop at first path that returns results

                except Exception as e:
                    self.logger.warning(f"Error scraping path {path}: {e}")
                    continue

            # Try fallback URLs if nothing found
            if not result.listings:
                fallback_urls = [
                    "https://www.combanketh.com/en/auction-notice",
                    "https://combanketh.com/en/notices",
                ]
                for fallback_url in fallback_urls:
                    try:
                        response = await page.goto(fallback_url, timeout=timeout_ms, wait_until="domcontentloaded")
                        if response and response.status == 200:
                            content = await page.content()
                            soup = BeautifulSoup(content, 'html.parser')
                            listings = self._extract_auction_listings(soup, fallback_url)
                            if listings:
                                result.listings.extend(listings)
                                break
                    except Exception:
                        continue
            
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"CBE scraper error: {e}")
            result.errors.append(str(e))
        finally:
            await self._close_browser()
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result
    
    def _extract_auction_listings(self, soup: BeautifulSoup, source_url: str) -> List[ScrapedListing]:
        """Extract auction listing items from page."""
        listings = []
        
        # Common container selectors for bank notice pages
        containers = soup.select(
            'article, .post, .entry, .notice-item, .auction-item, '
            '.tender-item, tr, .card, li.post, div[class*="notice"]'
        )
        
        keywords = ["የሐራጅ", "ሽያጭ", "ቤት", "ጨረታ", "ሐራጅ", "foreclosure", "auction", "property sale"]
        
        for container in containers:
            text = container.get_text()
            if any(kw in text for kw in keywords):
                title_el = container.select_one('h1, h2, h3, h4, a, .title')
                title = title_el.get_text(strip=True) if title_el else "CBE Auction Notice"
                
                desc = container.get_text(' ', strip=True)
                price = self.price_extractor.extract(desc)
                
                link_el = container.select_one('a[href]')
                link = self._get_absolute_url(link_el['href']) if link_el and link_el.get('href') else source_url
                
                listings.append(self.create_listing(
                    title=title,
                    description=desc[:1000],
                    price=price,
                    price_currency="ETB",
                    listing_type="auction",
                    source_url=link,
                    raw_data={"source_page": source_url}
                ))
        
        # Also collect PDF links with auction-related anchor text
        for link in soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE)):
            link_text = link.get_text().lower()
            if any(kw in link_text for kw in ["auction", "ሐራጅ", "ጨረታ", "notice", "sale"]):
                pdf_url = self._get_absolute_url(link.get('href'))
                listings.append(self.create_listing(
                    title=f"Auction Notice PDF: {link.get_text(strip=True)}",
                    description=f"CBE auction notice PDF: {pdf_url}",
                    listing_type="auction",
                    source_url=pdf_url,
                    raw_data={"pdf_url": pdf_url}
                ))
        
        return listings
