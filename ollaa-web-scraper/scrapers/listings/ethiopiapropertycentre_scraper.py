"""
Ethiopia Property Centre scraper.
FIXED: Was inheriting Engocha selectors. EPC runs the RealHomes/Houzez
WordPress theme which has its own class names (.rh_prop_card__title etc).
Needs its own dedicated scraper, not the generic WordPress base.
"""
import logging
import re
import asyncio
from datetime import datetime
from typing import List, Optional

from scrapers.base_scraper import PlaywrightScraper, ScrapedListing, ScrapeResult
from parsers.price_extractor import PriceExtractor

logger = logging.getLogger(__name__)


class EthiopiaPropertyCentreScraper(PlaywrightScraper):

    base_url = "https://ethiopiapropertycentre.com"
    source_name = "Ethiopia Property Centre"

    def __init__(self):
        super().__init__()
        self.price_extractor = PriceExtractor()

    def scrape(self) -> ScrapeResult:
        return asyncio.run(self.scrape_async())

    async def scrape_async(self) -> ScrapeResult:
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        limit = self.config.scraper.fetch_limit
        try:
            self.logger.info(f"Starting {self.source_name} scrape (limit: {limit})")
            await self._init_browser()
            for url in await self._find_listing_pages():
                page_listings = await self._scrape_listing_page(url)
                result.listings.extend(page_listings)
            if len(result.listings) > limit:
                result.listings = result.listings[:limit]
            result.success = True
            result.scraped_count = len(result.listings)
        except Exception as e:
            self.logger.error(f"EPC scrape error: {e}")
            result.errors.append(str(e))
        finally:
            await self._close_browser()
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result

    async def _find_listing_pages(self) -> List[str]:
        return [
            f"{self.base_url}/for-sale/",
            f"{self.base_url}/for-rent/",
            f"{self.base_url}/for-sale/apartments/",
            f"{self.base_url}/for-sale/houses/",
            f"{self.base_url}/for-sale/commercial/",
            f"{self.base_url}/for-sale/land/",
        ]

    async def _scrape_listing_page(self, url: str) -> List[ScrapedListing]:
        listings = []
        current_url = url
        for _ in range(30):
            self.logger.info(f"Scraping EPC: {current_url}")
            soup = await self._fetch_page_js(current_url)
            if not soup:
                break
            cards = soup.select(
                '.property-item, .rh_prop_card, .listing-item, '
                '[class*="property-card"], article.property, article'
            )
            if not cards:
                break
            for card in cards:
                listing = self._parse_listing_card(card)
                if listing:
                    listings.append(listing)
            next_link = soup.select_one('a.next, .pagination .next a, a[rel="next"]')
            if next_link and next_link.get('href'):
                current_url = self._get_absolute_url(next_link.get('href'))
            else:
                break
        return listings

    def _parse_listing_card(self, card) -> Optional[ScrapedListing]:
        try:
            card_text = card.get_text(' ', strip=True)
            title_elem = card.select_one(
                'h3.rh_prop_card__title, .listing-title, .property-title, h3 a, h4 a, h2 a'
            )
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None
            link_elem = title_elem if title_elem.name == 'a' else card.select_one('a[href]')
            link = self._get_absolute_url(link_elem.get('href')) if link_elem and link_elem.get('href') else None
            price_elem = card.select_one('.rh_prop_card__price, .property-price, [class*="price"]')
            price = self.price_extractor.extract(
                price_elem.get_text(strip=True) if price_elem else ""
            ) or self.price_extractor.extract(card_text)
            loc_elem = card.select_one('.rh_prop_card__location, .property-location, [class*="location"]')
            location = loc_elem.get_text(strip=True) if loc_elem else None
            bed_elem = card.select_one('[class*="bed"], .beds')
            bedrooms = None
            if bed_elem:
                n = re.search(r'(\d+)', bed_elem.get_text())
                if n:
                    v = int(n.group(1))
                    bedrooms = v if v <= 20 else None
            bath_elem = card.select_one('[class*="bath"], .baths')
            bathrooms = None
            if bath_elem:
                n = re.search(r'(\d+)', bath_elem.get_text())
                bathrooms = int(n.group(1)) if n else None
            area_elem = card.select_one('[class*="area"], [class*="size"], .sqm')
            area = self._extract_area(area_elem.get_text(strip=True)) if area_elem else None
            if area is None:
                area = self._extract_area(card_text)
            desc_elem = card.select_one('.description, .excerpt, p')
            description = desc_elem.get_text(strip=True) if desc_elem else card_text[:600]
            listing_type = "rent" if any(k in card_text.lower() for k in ['rent', 'ኪራይ']) else "sale"
            return self.create_listing(
                title=title, description=description, price=price,
                price_currency="ETB", location=location,
                property_type=self._detect_property_type(title + " " + description),
                area_sqm=area, bedrooms=bedrooms, bathrooms=bathrooms,
                images=[], posted_date=None, listing_type=listing_type,
                source_url=link or self.base_url,
                raw_data={"card_html": str(card)[:1000]}
            )
        except Exception as e:
            self.logger.error(f"EPC card parse error: {e}")
            return None

    def _extract_area(self, text: str) -> Optional[float]:
        if not text:
            return None
        for pat in [
            r'(\d{2,5})\s*ካሬ(?:\s*ሜትር)?',
            r'(\d{2,5})\s*[Mm][²2]',
            r'(\d{2,5})\s*(?:sqm|sq\.?m|m2)',
            r'(?:[Aa]rea|ስፋት)\s*[:\-=\s]+(\d{2,5})',
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    val = int(m.group(1))
                    if re.search(r'ብር|ETB|Birr|per sqm|በካሬ', text[m.end():m.end() + 25]):
                        continue
                    if 20 <= val <= 10000:
                        return float(val)
                except (ValueError, IndexError):
                    continue
        return None

    def _detect_property_type(self, text: str) -> Optional[str]:
        t = text.lower()
        if any(k in t for k in ['ኮንዶሚኒየም', 'condo', '40/60']): return "apartment"
        if any(k in t for k in ['አፓርትማ', 'apartment', 'flat']): return "apartment"
        if any(k in t for k in ['ቪላ', 'villa']): return "house"
        if any(k in t for k in ['ቤት', 'house']): return "house"
        if any(k in t for k in ['ቢሮ', 'office']): return "office"
        if any(k in t for k in ['ቦታ', 'land', 'plot']): return "land"
        return None
