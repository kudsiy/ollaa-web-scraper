"""
Engocha real estate listing scraper.
Scrapes property listings from Ethiopian real estate websites.
Uses Playwright to handle possible site blocks and JS rendering.

FIX APPLIED:
  - Added _find_listing_pages() method (was missing — caused AttributeError crash on every run)
  - Enhanced _extract_area() to include ካሬ / ካሬ ሜትር patterns (actual Amharic usage)
  - Enhanced _detect_property_type() with Amharic property keywords
"""
import logging
import re
import asyncio
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from scrapers.base_scraper import PlaywrightScraper, ScrapedListing, ScrapeResult
from parsers.price_extractor import PriceExtractor
from config import get_config


logger = logging.getLogger(__name__)


class EngochaScraper(PlaywrightScraper):
    """
    Scraper for Engocha.com real estate listings.
    Also serves as the base class for RealEthioScraper and EthiopiaRealtyScraper.
    """
    
    base_url = "https://www.engocha.com"
    source_name = "Engocha"
    
    def __init__(self):
        super().__init__()
        self.price_extractor = PriceExtractor()
        
    def scrape(self) -> ScrapeResult:
        """Synchronous wrapper for scrape_async."""
        return asyncio.run(self.scrape_async())
        
    async def scrape_async(self) -> ScrapeResult:
        """
        Main scraping method for Engocha listings.
        """
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        limit = self.config.scraper.fetch_limit
        
        try:
            self.logger.info(f"Starting {self.source_name} listing scrape (limit: {limit})")
            await self._init_browser()
            
            listing_urls = await self._find_listing_pages()
            self.logger.info(f"Found {len(listing_urls)} listing categories/pages")
            
            # Scrape listing categories in parallel
            tasks = [self._scrape_listing_page(url) for url in listing_urls]
            pages_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for page_listings in pages_results:
                if isinstance(page_listings, list):
                    result.listings.extend(page_listings)
                elif isinstance(page_listings, Exception):
                    self.logger.error(f"Error scraping a listing page: {page_listings}")
                
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
        """
        Return the category/listing-type URLs to scrape for this source.
        FIXED: was missing — caused AttributeError crash on every Engocha run.
        Subclasses (RealEthioScraper, EthiopiaRealtyScraper) override this.
        """
        return [
            f"{self.base_url}/real-estate/residential/for-sale/",
            f"{self.base_url}/real-estate/residential/for-rent/",
            f"{self.base_url}/real-estate/land/for-sale/",
            f"{self.base_url}/real-estate/commercial/for-sale/",
            f"{self.base_url}/real-estate/commercial/for-rent/",
        ]

    async def _scrape_listing_page(self, url: str) -> List[ScrapedListing]:
        """Scrape individual listing page and its pagination sequentially."""
        listings = []
        current_url = url
        max_pages = 50
        reached_start_date = False
        
        for page_num in range(1, max_pages + 1):
            if reached_start_date:
                break
                
            self.logger.info(f"Scraping {self.source_name} page {page_num}: {current_url}")
            soup = await self._fetch_page_js(current_url)
            
            if not soup:
                break
                
            listing_cards = soup.select(
                '.listing, .listing-card, .property-card, .listing-item, .property-item, '
                '[class*="listing"], [class*="property"], article, .item'
            )
            
            if not listing_cards:
                break
                
            for card in listing_cards:
                listing = self._parse_listing_card(card)
                if listing:
                    if listing.posted_date and not self.should_continue_crawling(listing.posted_date):
                        self.logger.info(f"Reached start_date limit at {listing.posted_date}")
                        reached_start_date = True
                        break
                    listings.append(listing)
            
            if reached_start_date:
                break

            # Find next page link
            next_link = soup.select_one('.pagination .next a, .pagination a.next, a[rel="next"], .next-page a')
            if next_link and next_link.get('href'):
                current_url = self._get_absolute_url(next_link.get('href'))
            else:
                pagination_links = soup.select('.pagination a, .page-link, a[class*="page"]')
                found_next = False
                for link in pagination_links:
                    try:
                        text = link.get_text(strip=True)
                        if text.isdigit() and int(text) == page_num + 1:
                            current_url = self._get_absolute_url(link.get('href'))
                            found_next = True
                            break
                    except (ValueError, TypeError):
                        continue
                
                if not found_next:
                    break
                            
        return listings
    
    def _get_pagination_pages(self, soup, base_url: str) -> List[str]:
        """Get paginated listing pages."""
        pages = []
        pagination = soup.select('.pagination a, .page-link, a[class*="page"]')
        
        for link in pagination:
            href = link.get('href')
            if href:
                page_url = self._get_absolute_url(href)
                if page_url not in pages:
                    pages.append(page_url)
                    
        return pages
    
    def _parse_listing_card(self, card) -> Optional[ScrapedListing]:
        """Parse a listing card element."""
        try:
            title_elem = card.select_one('h2, h3, h4, .title, .listing-title, .property-title, a')
            price_elem = card.select_one('.price, .listing-price, [class*="price"]')
            location_elem = card.select_one('.location, .address, [class*="location"], [class*="address"]')
            bedrooms_elem = card.select_one('.bedrooms, .beds, [class*="bedroom"], [class*="bed"]')
            bathrooms_elem = card.select_one('.bathrooms, .baths, [class*="bathroom"], [class*="bath"]')
            area_elem = card.select_one('.area, .size, .sqm, [class*="area"]')
            desc_elem = card.select_one('.description, .desc, .excerpt, p')
            link_elem = card.select_one('a[href]')
            date_elem = card.select_one('.date, .posted-on, .time, .listing-date, .post-date')
            
            title = title_elem.get_text(strip=True) if title_elem else "Property Listing"
            if title_elem and title_elem.name == 'a':
                title = title_elem.get_text(strip=True)

            # Build full text blob for extraction fallback
            card_full_text = card.get_text(' ', strip=True)
                
            # Try price from dedicated element first, fall back to full card text
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self.price_extractor.extract(price_text)
            if price is None:
                price = self.price_extractor.extract(card_full_text)
            
            listing_type = self._detect_listing_type(title + " " + price_text)
            
            location = location_elem.get_text(strip=True) if location_elem else None
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            posted_date = None
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                try:
                    from dateutil import parser as date_parser
                    posted_date = date_parser.parse(date_text, fuzzy=True)
                except Exception:
                    pass

            bedrooms = None
            if bedrooms_elem:
                bedrooms = self._extract_number(bedrooms_elem.get_text(strip=True))
                
            bathrooms = None
            if bathrooms_elem:
                bathrooms = self._extract_number(bathrooms_elem.get_text(strip=True))
                
            area = None
            if area_elem:
                area = self._extract_area(area_elem.get_text(strip=True))
            # Fall back to full card text for area
            if area is None:
                area = self._extract_area(card_full_text)
                
            link = None
            if link_elem:
                href = link_elem.get('href')
                if href:
                    link = self._get_absolute_url(href)
                
            images = []
            img_elem = card.select_one('img[src]')
            if img_elem:
                img_src = img_elem.get('src')
                if img_src:
                    images.append(self._get_absolute_url(img_src))
                    
            property_type = self._detect_property_type(title + " " + description + " " + card_full_text)
            
            return self.create_listing(
                title=title,
                description=description or card_full_text[:500],
                price=price,
                price_currency="ETB",
                location=location,
                property_type=property_type,
                area_sqm=area,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                images=images,
                posted_date=posted_date,
                listing_type=listing_type,
                source_url=link or self.base_url,
                raw_data={"card_html": str(card)}
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing listing card: {e}")
            return None
    
    def _detect_listing_type(self, text: str) -> str:
        """Detect if listing is for sale, rent, or auction."""
        t = text.lower()
        if any(kw in t for kw in ['auction', 'ሱሚ', 'የጨረታ', 'ጨረታ', 'ሐራጅ', 'foreclosure']):
            return "auction"
        if any(kw in t for kw in ['rent', 'ኪራይ', 'lease', 'for rent', 'ለኪራይ', 'ይከራያል']):
            return "rent"
        return "sale"
    
    def _detect_property_type(self, text: str) -> Optional[str]:
        """Detect property type from text — includes Amharic keywords."""
        t = text.lower()
        
        # Check Amharic first (more specific in Ethiopian context)
        if any(kw in t for kw in ['ኮንዶሚኒየም', '40/60', '20/80', 'condominium', 'condo']):
            return "apartment"
        if any(kw in t for kw in ['አፓርትማ', 'አፓርትማንት', 'apartment', 'flat']):
            return "apartment"
        if any(kw in t for kw in ['ቪላ', 'villa', 'townhouse']):
            return "house"
        if any(kw in t for kw in ['ቤት', 'house']):
            return "house"
        if any(kw in t for kw in ['ቢሮ', 'office', 'commercial space']):
            return "office"
        if any(kw in t for kw in ['ሱቅ', 'store', 'shop', 'retail']):
            return "store"
        if any(kw in t for kw in ['መጋዘን', 'warehouse', 'storage']):
            return "warehouse"
        if any(kw in t for kw in ['ቦታ', 'land', 'plot', 'parcel', 'ምድር']):
            return "land"
        if any(kw in t for kw in ['building', 'apartment building']):
            return "building"
                    
        return None
    
    def _extract_number(self, text: str) -> Optional[int]:
        """Extract integer from text."""
        m = re.search(r'(\d+)', text)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
        return None
    
    def _extract_area(self, text: str) -> Optional[float]:
        """
        Extract area in sqm from text.
        FIX: added ካሬ / ካሬ ሜትར (actual Amharic usage).
        Original only had ካዕራ which rarely appears in real listings.
        """
        if not text:
            return None

        patterns = [
            # Amharic: "200 ካሬ ሜትር" or "200 ካሬ"
            r'(\d{2,5})\s*ካሬ(?:\s*ሜትር)?',
            # "150 M²" or "150 m²"
            r'(\d{2,5})\s*[Mm][²2]',
            # "150 sqm" or "150 m2"
            r'(\d{2,5})\s*(?:sqm|sq\.?m|m2)',
            # "Area: 150" or "ስፋት: 200"
            r'(?:[Aa]rea|ስፋት)\s*[:\-=\s]+(\d{2,5})',
            # Legacy: ካዕራ / ካሪ
            r'(\d{2,5})\s*(?:ካዕራ|ካሪ)',
        ]
        
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    val = int(m.group(1))
                    # Sanity check: 20–5000 sqm is reasonable for residential/commercial
                    if 20 <= val <= 5000:
                        return float(val)
                except (ValueError, IndexError):
                    continue

        return None
