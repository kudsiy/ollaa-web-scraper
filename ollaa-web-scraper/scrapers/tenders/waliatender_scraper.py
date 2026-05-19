"""
Walia Tender scraper.
Includes fallback domains for ERR_NAME_NOT_RESOLVED and ERR_CONNECTION_TIMED_OUT.
"""
import logging
import asyncio
from datetime import datetime
from typing import Optional, List

from scrapers.base_scraper import ScrapedListing, ScrapeResult
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class WaliaTenderScraper(BaseTenderScraper):
    """
    Scraper for Walia Tender notices.
    Includes fallback to alternate mirrors when domain resolution fails.
    """
    
    base_url = "https://www.waliatender.com"
    source_name = "Walia Tender"
    
    # Fallback domains/mirrors for when primary domain fails
    fallback_domains = [
        ("https://waliatender.com", "Walia Tender (no www)"),
    ]
    
    async def scrape_async(self) -> ScrapeResult:
        """
        Main scraping method with fallback for DNS resolution failures.
        """
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        try:
            await self._init_browser()
            
            page = await self.context.new_page()
            timeout_ms = self.config.scraper.request_timeout * 1000
            
            # Try primary URL first
            urls_to_try = [(self.base_url, self.source_name)] + self.fallback_domains
            
            page_loaded = False
            for url, name in urls_to_try:
                if page_loaded:
                    break
                    
                try:
                    self.logger.info(f"Attempting to load {name}: {url}")
                    await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                    page_loaded = True
                    self.base_url = url  # Update base URL for relative link resolution
                except Exception as e:
                    error_str = str(e).lower()
                    if "err_name_not_resolved" in error_str or "err_connection" in error_str or "dns" in error_str:
                        self.logger.warning(f"Domain resolution failed for {name}: {e}, trying alternative...")
                    else:
                        self.logger.warning(f"Navigation failed for {name}: {e}")
                    continue
            
            if not page_loaded:
                self.logger.error("All Walia Tender domains failed to load")
                result.errors.append("All domains failed for Walia Tender")
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
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            
            # Try multiple selectors for finding tender items
            selectors_to_try = [
                self.item_selector,
                ".tender-item, .tender-card, .list-group-item, article, .post, .entry",
                "tr, .listing, .item, div[class*='tender'], div[class*='listing']",
                "table tr, ul li"
            ]
            
            tender_items = []
            for selector in selectors_to_try:
                items = soup.select(selector)
                if items:
                    tender_items = items
                    self.logger.info(f"Found {len(tender_items)} items with selector: {selector}")
                    break
            
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

    def _parse_tender_item(self, item) -> Optional[ScrapedListing]:
        # Use logging instead of print to avoid encoding issues in Windows console
        if not hasattr(self, '_first_item_printed'):
            self.logger.info("First item HTML captured for debug")
            self._first_item_printed = True

        try:
            # Based on common tender site structures in Ethiopia
            title_elem = item.select_one(".tender-title, .title, h3, h4, a.tender-link, td:nth-child(2), a[href]")
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None

            # Extract other fields
            price_elem = item.select_one(".price, .cost, .amount, td:nth-child(4)")
            location_elem = item.select_one(".location, .region, .city, td:nth-child(3)")
            date_elem = item.select_one(".date, .deadline, .closing, td:nth-child(5)")
            
            description = item.get_text(strip=True)
            price = self.price_extractor.extract(price_elem.get_text(strip=True)) if price_elem else None
            location = location_elem.get_text(strip=True) if location_elem else None
            
            link_elem = item.select_one("a[href]")
            source_url = self._get_absolute_url(link_elem.get("href")) if link_elem else self.base_url
            
            return self.create_listing(
                title=title,
                description=description[:1000],
                price=price,
                location=location,
                source_url=source_url,
                listing_type="tender",
                raw_data={"raw_html": str(item)[:500]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing Walia item: {e}")
            return None
