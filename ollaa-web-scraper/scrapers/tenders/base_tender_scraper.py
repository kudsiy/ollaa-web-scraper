"""
Base tender scraper.
Provides common functionality for tender scrapers.
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


class BaseTenderScraper(PlaywrightScraper):
    """
    Base scraper for tender notices.
    Uses Playwright for JS-rendered content.
    """
    
    base_url = "https://example.com"
    source_name = "Tender"
    item_selector = ".tender-item, .tender-card, .list-group-item, article, .post, .entry"
    
    def __init__(self):
        super().__init__()
        self.price_extractor = PriceExtractor()
        
    async def scrape_async(self) -> ScrapeResult:
        """
        Main scraping method for tender notices.
        """
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        timeout_ms = self.config.scraper.request_timeout * 1000
        
        try:
            await self._init_browser()
            
            page = await self.context.new_page()
            
            try:
                await page.goto(self.base_url, wait_until="networkidle", timeout=timeout_ms)
            except Exception as e:
                error_str = str(e).lower()
                if "err_name_not_resolved" in error_str or "err_connection" in error_str or "dns" in error_str:
                    self.logger.warning(f"Domain resolution failed for {self.source_name}: {e}")
                else:
                    self.logger.warning(f"Navigation timeout, trying load event: {e}")
                try:
                    await page.goto(self.base_url, wait_until="load", timeout=timeout_ms)
                except Exception as e2:
                    error_str2 = str(e2).lower()
                    if "err_name_not_resolved" in error_str2 or "err_connection" in error_str2 or "dns" in error_str2:
                        self.logger.error(f"Domain resolution failed for {self.source_name}: {e2}")
                        result.errors.append(f"Domain resolution failed - the site may have moved or be temporarily unavailable")
                    else:
                        self.logger.error(f"Failed to load page: {e2}")
                        result.errors.append(f"Navigation failed: {e2}")
                    await page.close()
                    await self._close_browser()
                    result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
                    return result
            
            await asyncio.sleep(2)
            
            if self.item_selector:
                try:
                    await page.wait_for_selector(self.item_selector.split(',')[0].strip(), timeout=10000)
                except Exception:
                    self.logger.warning(f"Selector {self.item_selector} not found within timeout")
            
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            tender_items = soup.select(self.item_selector)
            self.logger.info(f"Found {len(tender_items)} potential tender items on {self.source_name}")
            
            for item in tender_items:
                listing = self._parse_tender_item(item)
                if listing:
                    result.listings.append(listing)
                    
            result.success = True
            result.scraped_count = len(result.listings)
            await page.close()
            
        except Exception as e:
            self.logger.error(f"Error during {self.source_name} scrape: {e}")
            result.errors.append(str(e))
        finally:
            await self._close_browser()
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result

    def scrape(self) -> ScrapeResult:
        """Synchronous wrapper for scrape_async."""
        return asyncio.run(self.scrape_async())
        
    def _parse_tender_item(self, item) -> Optional[ScrapedListing]:
        """Parse a tender item."""
        try:
            title_elem = item.select_one("h3, h4, h2, .title, .tender-title, a")
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            
            if not title or len(title) < 5:
                return None
            
            desc_elem = item.select_one(".description, .tender-details, p, .content")
            location_elem = item.select_one(".location, .region, .address")
            date_elem = item.select_one(".date, .deadline, .closing-date, time")
            price_elem = item.select_one(".price, .amount, .cost")
            
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            location = location_elem.get_text(strip=True) if location_elem else None
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            
            if price_text:
                price = self.price_extractor.extract(price_text)
            else:
                price = self.price_extractor.extract(description)
                
            link_elem = item.select_one("a[href]")
            link = self.base_url
            if link_elem:
                href = link_elem.get("href")
                if href:
                    if href.startswith('http'):
                        link = href
                    else:
                        link = self._get_absolute_url(href)
                
            return self.create_listing(
                title=title,
                description=description,
                price=price,
                location=location,
                source_url=link,
                listing_type="tender",
                raw_data={"raw_html": str(item)[:1000]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing tender item: {e}")
            return None
