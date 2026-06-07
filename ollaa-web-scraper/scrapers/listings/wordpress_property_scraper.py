"""
Generic WordPress property theme scraper.
BetDelala, EthiopiaRealty, EthioRealEstates, LivingEthio, RealEthio
all inherit this instead of EngochaScraper.
"""
import logging
import re
import asyncio
from datetime import datetime
from typing import List, Optional

from scrapers.base_scraper import PlaywrightScraper, ScrapedListing, ScrapeResult
from parsers.price_extractor import PriceExtractor

logger = logging.getLogger(__name__)


class WordPressPropertyScraper(PlaywrightScraper):

    base_url = ""
    source_name = ""

    CARD_SELECTORS = (
        '.property-item', '.listing-item', 'article.property',
        '.rh_prop_card', '.property-listing', '[class*="property-card"]',
        '.houzez-card', '.easy-property-listing', 'article',
    )
    TITLE_SELECTORS = (
        'h3.property-title a', '.listing-title a', 'h3.rh_prop_card__title',
        '.property-title', 'h2 a', 'h3 a', 'h4 a', '.title a', 'a.property-link',
    )
    PRICE_SELECTORS = (
        '.property-price', '.listing-price', '.rh_prop_card__price',
        '[class*="price"]', '.price',
    )
    LOCATION_SELECTORS = (
        '.property-location', '.listing-location', '.rh_prop_card__location',
        '[class*="location"]', '.address',
    )
    BED_SELECTORS = ('[class*="bed"]', '.beds', '.bedrooms', 'span[title*="Bedroom"]')
    BATH_SELECTORS = ('[class*="bath"]', '.baths', '.bathrooms', 'span[title*="Bathroom"]')
    AREA_SELECTORS = ('[class*="area"]', '[class*="size"]', '.sqm', 'span[title*="Area"]', 'span[title*="Sq"]')
    NEXT_PAGE_SELECTORS = ('a.next', '.pagination .next a', 'a[rel="next"]', '.nav-next a', 'li.next a')

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
            listing_urls = await self._find_listing_pages()
            tasks = [self._scrape_listing_page(url) for url in listing_urls]
            pages_results = await asyncio.gather(*tasks, return_exceptions=True)
            for page_listings in pages_results:
                if isinstance(page_listings, list):
                    result.listings.extend(page_listings)
                elif isinstance(page_listings, Exception):
                    self.logger.error(f"Page error: {page_listings}")
            if len(result.listings) > limit:
                result.listings = result.listings[:limit]
            result.success = True
            result.scraped_count = len(result.listings)
        except Exception as e:
            self.logger.error(f"Error during {self.source_name} scrape: {e}")
            result.errors.append(str(e))
        finally:
            await self._close_browser()
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result

    async def _find_listing_pages(self) -> List[str]:
        return [self.base_url]

    async def _scrape_listing_page(self, url: str) -> List[ScrapedListing]:
        listings = []
        current_url = url
        for page_num in range(1, 31):
            self.logger.info(f"  [{self.source_name}] page {page_num}: {current_url}")
            soup = await self._fetch_page_js(current_url)
            if not soup:
                break
            cards = []
            for sel in self.CARD_SELECTORS:
                cards = soup.select(sel)
                if cards:
                    self.logger.info(f"  Found {len(cards)} cards using '{sel}'")
                    break
            if not cards:
                self.logger.warning(f"  No cards found on {current_url}")
                break
            for card in cards:
                listing = self._parse_listing_card(card)
                if listing:
                    listings.append(listing)
            next_url = None
            for sel in self.NEXT_PAGE_SELECTORS:
                next_link = soup.select_one(sel)
                if next_link and next_link.get('href'):
                    next_url = self._get_absolute_url(next_link.get('href'))
                    break
            if next_url and next_url != current_url:
                current_url = next_url
            else:
                break
        return listings

    def _parse_listing_card(self, card) -> Optional[ScrapedListing]:
        try:
            card_text = card.get_text(' ', strip=True)
            title_elem = self._select_first(card, self.TITLE_SELECTORS)
            if not title_elem:
                title_elem = card.select_one('h2, h3, h4')
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 5:
                return None
            if title.lower() in {'home', 'for sale', 'for rent', 'search', 'filter', 'menu'}:
                return None
            link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
            if not link_elem:
                link_elem = card.select_one('a[href]')
            link = self._get_absolute_url(link_elem.get('href')) if link_elem and link_elem.get('href') else None
            price_elem = self._select_first(card, self.PRICE_SELECTORS)
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self.price_extractor.extract(price_text)
            if price is None:
                price = self.price_extractor.extract(card_text)
            loc_elem = self._select_first(card, self.LOCATION_SELECTORS)
            location = loc_elem.get_text(strip=True) if loc_elem else None
            bed_elem = self._select_first(card, self.BED_SELECTORS)
            bedrooms = None
            if bed_elem:
                candidate = self._extract_number(bed_elem.get_text(strip=True))
                if candidate and 0 < candidate <= 20:
                    bedrooms = candidate
            bath_elem = self._select_first(card, self.BATH_SELECTORS)
            bathrooms = self._extract_number(bath_elem.get_text(strip=True)) if bath_elem else None
            area_elem = self._select_first(card, self.AREA_SELECTORS)
            area = self._extract_area(area_elem.get_text(strip=True)) if area_elem else None
            if area is None:
                area = self._extract_area(card_text)
            desc_elem = card.select_one('.description, .excerpt, .property-excerpt, p')
            description = desc_elem.get_text(strip=True) if desc_elem else card_text[:600]
            listing_type = "rent" if any(kw in card_text.lower() for kw in ['rent', 'ኪራይ', 'ለኪራይ', 'ይከራያል']) else "sale"
            property_type = self._detect_property_type(title + " " + description)
            return self.create_listing(
                title=title, description=description, price=price,
                price_currency="ETB", location=location,
                property_type=property_type, area_sqm=area,
                bedrooms=bedrooms, bathrooms=bathrooms,
                images=[], posted_date=None, listing_type=listing_type,
                source_url=link or self.base_url,
                raw_data={"card_html": str(card)[:1000]}
            )
        except Exception as e:
            self.logger.error(f"Error parsing {self.source_name} card: {e}")
            return None

    def _select_first(self, element, selectors):
        for sel in selectors:
            found = element.select_one(sel)
            if found:
                return found
        return None

    def _extract_number(self, text: str) -> Optional[int]:
        m = re.search(r'(\d+)', text)
        return int(m.group(1)) if m else None

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
                    following = text[m.end():m.end() + 25]
                    if re.search(r'ብር|ETB|Birr|per sqm|/sqm|በካሬ', following):
                        continue
                    if 20 <= val <= 10000:
                        return float(val)
                except (ValueError, IndexError):
                    continue
        return None

    def _detect_property_type(self, text: str) -> Optional[str]:
        t = text.lower()
        if any(k in t for k in ['ኮንዶሚኒየም', 'condominium', 'condo', '40/60', '20/80']): return "apartment"
        if any(k in t for k in ['አፓርትማ', 'apartment', 'flat']): return "apartment"
        if any(k in t for k in ['ቪላ', 'villa', 'townhouse']): return "house"
        if any(k in t for k in ['ቤት', 'house']): return "house"
        if any(k in t for k in ['ቢሮ', 'office']): return "office"
        if any(k in t for k in ['ሱቅ', 'store', 'shop']): return "store"
        if any(k in t for k in ['ቦታ', 'land', 'plot']): return "land"
        return None
