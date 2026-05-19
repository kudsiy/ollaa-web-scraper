
"""
Commercial Bank of Ethiopia auction scraper.
Uses Playwright to bypass blocks and handle dynamic content.
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
    
    base_url = "https://www.combanketh.et"
    source_name = "Commercial Bank of Ethiopia"
    
    def __init__(self):
        super().__init__()
        self.price_extractor = PriceExtractor()
        
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
            
            # Paths to check for auction notices - prioritize known working paths
            auction_paths = [
                "/en/notices",
                "/notices",
                "/am/notices",
                "/ማስታወቂያዎች",
                "/en/notices/auction",
                "/en/notices/property"
            ]
            
            for path in auction_paths:
                if len(result.listings) >= limit:
                    break
                    
                url = self._get_absolute_url(path)
                self.logger.info(f"Navigating to CBE Notices: {url}")
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                    await asyncio.sleep(3)  # Allow time for dynamic content
                    
                    content = await page.content()
                    soup = BeautifulSoup(content, "html.parser")
                    
                    # Extract from structured elements - broad selectors
                    items = soup.select("article, .notice-item, .auction-card, tr, li.list-group-item, div[class*='notice'], div[class*='auction'], div[class*='tender'], .listing-item, .item")
                    found_count = 0
                    
                    for item in items:
                        if len(result.listings) >= limit:
                            break
                        text = item.get_text(separator=" ", strip=True)
                        # Keywords for property auctions
                        if any(kw in text for kw in ["ሐራጅ", "የሐራጅ", "ጨረታ", "Auction", "Foreclosure", "Tender", "Sale", "ሽያጭ", "ቤት"]):
                            listing = self._parse_item(item, url)
                            if listing:
                                result.listings.append(listing)
                                found_count += 1
                    
                    # Also look for PDF links specifically
                    pdf_links = soup.find_all("a", href=re.compile(r"\.pdf$", re.IGNORECASE))
                    for link in pdf_links:
                        if len(result.listings) >= limit:
                            break
                        link_text = link.get_text(strip=True)
                        href = link.get("href")
                        if any(kw in link_text for kw in ["ሐራጅ", "ጨረታ", "Auction", "Notice", "Tender", "Sale", "ሽያጭ"]):
                            pdf_url = self._get_absolute_url(href)
                            result.listings.append(self.create_listing(
                                title=f"Auction Notice: {link_text}",
                                description=f"Auction notice found in PDF: {link_text}",
                                source_url=pdf_url,
                                listing_type="auction",
                                raw_data={"pdf_url": pdf_url}
                            ))
                            found_count += 1
                            
                    self.logger.info(f"Found {found_count} potential listings on {url}")
                    
                except Exception as e:
                    self.logger.warning(f"Error scraping path {path}: {e}")
                    continue
            
            # If no listings found via paths, try known CBE auction notice landing page
            if len(result.listings) == 0:
                fallback_urls = [
                    "https://www.combanketh.et/en/notices/auction",
                    "https://www.combanketh.et/en/notices/property-sale",
                ]
                for fallback_url in fallback_urls:
                    if len(result.listings) >= limit:
                        break
                    try:
                        self.logger.info(f"Trying CBE fallback URL: {fallback_url}")
                        await page.goto(fallback_url, wait_until="networkidle", timeout=timeout_ms)
                        await asyncio.sleep(2)
                        content = await page.content()
                        soup = BeautifulSoup(content, "html.parser")
                        items = soup.select("article, .notice-item, li, div[class*='notice'], div[class*='listing']")
                        for item in items:
                            text = item.get_text(separator=" ", strip=True)
                            if any(kw in text for kw in ["ሐራጅ", "ጨረታ", "Auction", "Sale", "ቤት", "ሽያጭ"]):
                                listing = self._parse_item(item, fallback_url)
                                if listing:
                                    result.listings.append(listing)
                    except Exception as e:
                        self.logger.warning(f"CBE fallback URL failed: {e}")
                        continue
            
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during CBE scrape: {e}")
            result.errors.append(str(e))
        finally:
            await self._close_browser()
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result

    def scrape(self) -> ScrapeResult:
        """Synchronous wrapper for scrape_async."""
        return asyncio.run(self.scrape_async())
        
    def _parse_item(self, item, current_url: str) -> Optional[ScrapedListing]:
        """Parse an auction item element."""
        try:
            title_elem = item.select_one("h1, h2, h3, h4, .title, .notice-title, a")
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if len(title) < 10:  # Skip too short titles
                return None
                
            link_elem = item.select_one("a[href]")
            source_url = current_url
            if link_elem:
                source_url = self._get_absolute_url(link_elem.get("href"))
                
            text = item.get_text(separator=" ", strip=True)
            price = self.price_extractor.extract(text)
            
            return self.create_listing(
                title=title,
                description=text[:1000],
                price=price,
                source_url=source_url,
                listing_type="auction",
                raw_data={"raw_html": str(item)[:1000]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing CBE item: {e}")
            return None
