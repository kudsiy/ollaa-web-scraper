
"""
Jiji Ethiopia real estate listing scraper.
Uses Playwright to handle infinite scroll and JS rendering.
"""
import logging
import asyncio
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from scrapers.base_scraper import PlaywrightScraper, ScrapedListing, ScrapeResult
from parsers.price_extractor import PriceExtractor

logger = logging.getLogger(__name__)

class JijiScraper(PlaywrightScraper):
    """
    Scraper for Jiji Ethiopia property listings.
    Handles infinite scroll and dynamic content.
    """
    
    base_url = "https://jiji.com.et/real-estate"
    source_name = "Jiji Ethiopia"
    
    def __init__(self):
        super().__init__()
        self.price_extractor = PriceExtractor()
        
    async def scrape_async(self) -> ScrapeResult:
        """
        Main scraping method for Jiji.
        """
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        limit = self.config.scraper.fetch_limit
        start_date_str = self.config.scraper.start_date
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        timeout_ms = self.config.scraper.request_timeout * 1000
        
        try:
            await self._init_browser()
            page = await self.context.new_page()
            
            # Use stealth-like headers and settings
            await page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/"
            })
            
            self.logger.info(f"Navigating to Jiji Real Estate: {self.base_url}")
            await page.goto(self.base_url, wait_until="networkidle", timeout=timeout_ms)
            
            # Wait for content to load, handle possible cloudflare check
            await asyncio.sleep(5)
            
            # Check if we got a non-empty page
            content = await page.content()
            if "jiji" not in content.lower() and len(content) < 500:
                self.logger.warning("Jiji page appears empty or blocked, trying alternate approaches")
                # Try adding a referer and retry
                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=timeout_ms)
                await asyncio.sleep(5)
            
            # Infinite scroll to load more listings
            self.logger.info(f"Performing infinite scroll to load listings (limit: {limit})")
            last_height = await page.evaluate("document.body.scrollHeight")
            
            # Improved infinite scroll with progressive loading
            scroll_attempts = 0
            max_scroll_attempts = max(limit // 10, 20)
            no_change_count = 0
            
            for i in range(max_scroll_attempts):
                # Scroll down smoothly
                await page.evaluate("""
                    window.scrollTo({
                        top: document.body.scrollHeight,
                        behavior: 'smooth'
                    });
                """)
                await asyncio.sleep(2.5)  # Longer wait for content to load
                
                # Try clicking any "Load More" buttons if present
                try:
                    load_more_btn = await page.query_selector("button:has-text('Load More'), button:has-text('Show More'), a:has-text('Load More')")
                    if load_more_btn:
                        await load_more_btn.click()
                        await asyncio.sleep(2)
                except Exception:
                    pass
                
                # Check current count
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                listing_cards = soup.select(
                    ".b-list-advert-base, .qa-advert-list-item, "
                    "[data-testid='listing-card'], .advert-card, "
                    "a[class*='advert'], div[class*='listing'], "
                    "div[class*='advert-item'], .listing-card, "
                    ".col-md-12, .listing-item"
                )
                
                if len(listing_cards) >= limit:
                    self.logger.info(f"Reached fetch_limit {limit} with {len(listing_cards)} cards found")
                    break
                
                self.logger.debug(f"Scroll iteration {i+1} complete, found {len(listing_cards)} cards (changed from {len(listing_cards)})")
                
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count += 1
                    if no_change_count >= 3:
                        self.logger.info("No more content loading, stopping scroll")
                        break
                else:
                    no_change_count = 0
                last_height = new_height
                scroll_attempts = i + 1
            
            # Scrape the results
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Broader listing card selectors
            listing_cards = soup.select(
                ".b-list-advert-base, .qa-advert-list-item, "
                "[data-testid='listing-card'], .advert-card, "
                "a[class*='advert'], div[class*='listing'], "
                "div[class*='advert-item'], .listing-card, "
                ".col-md-12, .listing-item"
            )
            self.logger.info(f"Found {len(listing_cards)} potential listing cards after {scroll_attempts+1} scroll attempts")
            
            for card in listing_cards:
                if len(result.listings) >= limit:
                    break
                    
                listing = self._parse_listing_card(card)
                if listing:
                    result.listings.append(listing)
                    
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during Jiji scrape: {e}")
            result.errors.append(str(e))
        finally:
            await self._close_browser()
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result

    def scrape(self) -> ScrapeResult:
        """Synchronous wrapper for scrape_async."""
        return asyncio.run(self.scrape_async())
        
    def _parse_listing_card(self, card) -> Optional[ScrapedListing]:
        """Parse a single listing card from Jiji."""
        try:
            # Jiji often uses classes starting with 'qa-' for key elements
            # Also try modern Jiji selectors
            title_elem = (
                card.select_one(".qa-advert-title, .b-advert-title-inner, .b-list-advert-base__title, "
                                "a[class*='title'], h3, h4, [data-testid='listing-title'], "
                                "a[href*='/ad/']")
            )
            price_elem = card.select_one(
                ".qa-advert-price, .b-list-advert-base__price, "
                "[class*='price'], [class*='Price'], .advert-price"
            )
            location_elem = card.select_one(
                ".b-list-advert-base__location, .b-list-advert-base__region, "
                "[class*='location'], [class*='region'], "
                "[class*='Location'], span[class*='text-secondary']"
            )
            link_elem = card.select_one(
                "a.js-handle-click-advert, a[href*='/ad/'], "
                "a[href*='/real-estate/'], a.qa-advert-link"
            )
            
            if not title_elem:
                # Try broader approach: any heading with a link
                title_elem = card.select_one("h2 a, h3 a, h4 a, a strong, a[href]")
                if not title_elem:
                    return None
                
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 3:
                return None
                
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self.price_extractor.extract(price_text)
            location = location_elem.get_text(strip=True) if location_elem else None
            
            link = self.base_url
            if link_elem:
                href = link_elem.get("href")
                if href:
                    link = self._get_absolute_url(href)
            elif title_elem:
                href = title_elem.get("href")
                if href:
                    link = self._get_absolute_url(href)
                
            # Attempt to extract more details from the title/text
            text_context = title + " " + (card.get_text(strip=True) or "")
            
            return self.create_listing(
                title=title,
                description=f"Property listing on Jiji: {title}",
                price=price,
                location=location,
                source_url=link,
                listing_type="sale",
                raw_data={"raw_text": card.get_text(separator=" ", strip=True)[:2000]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing Jiji card: {e}")
            return None
