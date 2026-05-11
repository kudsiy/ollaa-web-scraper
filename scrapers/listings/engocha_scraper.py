"""
Engocha real estate listing scraper.
Scrapes property listings from Ethiopian real estate websites.
"""
import logging
import re
from datetime import datetime
from typing import List, Optional

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, ScrapedListing, ScrapeResult
from parsers.price_extractor import PriceExtractor
from config import get_config


logger = logging.getLogger(__name__)


class EngochaScraper(BaseScraper):
    """
    Scraper for Ethiopian real estate listings (Engocha-style sites).
    Target: Real estate listing aggregator sites.
    """
    
    base_url = "https://www.engocha.com"
    source_name = "Engocha"
    
    def __init__(self):
        super().__init__()
        self.price_extractor = PriceExtractor()
        
    def scrape(self) -> ScrapeResult:
        """
        Main scraping method for Engocha listings.
        
        Returns:
            ScrapeResult with all scraped listings
        """
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        try:
            self.logger.info("Starting Engocha listing scrape")
            
            listing_urls = self._find_listing_pages()
            self.logger.info(f"Found {len(listing_urls)} listing pages")
            
            for url in listing_urls:
                listings = self._scrape_listing_page(url)
                result.listings.extend(listings)
                
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during Engocha scrape: {e}")
            result.errors.append(str(e))
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result
    
    def _find_listing_pages(self) -> List[str]:
        """Find listing pages from Engocha website."""
        pages = []
        
        # Known working property listing URLs on Engocha
        possible_urls = [
            f"{self.base_url}/real-estate",
            f"{self.base_url}/apartments-houses-for-sale",
            f"{self.base_url}/apartments-houses-for-rent",
        ]
        
        for url in possible_urls:
            soup = self.scrape_page(url)
            if soup:
                cards = soup.select('.listing-card, .property-card, .listing-item, [class*="listing"], article')
                if cards:
                    pages.append(url)
                    break
                
        return pages if pages else possible_urls[:1]
    
    def _scrape_listing_page(self, url: str) -> List[ScrapedListing]:
        """Scrape individual listing page."""
        listings = []
        soup = self.scrape_page(url)
        
        if not soup:
            return listings
            
        listing_cards = soup.select(
            '.listing, .listing-card, .property-card, .listing-item, .property-item, '
            '[class*="listing"], [class*="property"], article, .item'
        )
        
        for card in listing_cards:
            listing = self._parse_listing_card(card)
            if listing:
                listings.append(listing)
                
        pagination = self._get_pagination_pages(soup, url)
        for page_url in pagination[:5]:
            page_soup = self.scrape_page(page_url)
            if page_soup:
                cards = page_soup.select('.listing-card, .property-card, .listing-item, [class*="listing"]')
                for card in cards:
                    listing = self._parse_listing_card(card)
                    if listing:
                        listings.append(listing)
                        
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
            
            title = title_elem.get_text(strip=True) if title_elem else "Property Listing"
            if title_elem and title_elem.name == 'a':
                title = title_elem.get_text(strip=True)
                
            price_text = price_elem.get_text(strip=True) if price_elem else ""
            price = self.price_extractor.extract(price_text)
            
            listing_type = self._detect_listing_type(title + " " + price_text)
            
            location = location_elem.get_text(strip=True) if location_elem else None
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            bedrooms = None
            if bedrooms_elem:
                bedrooms_text = bedrooms_elem.get_text(strip=True)
                bedrooms = self._extract_number(bedrooms_text)
                
            bathrooms = None
            if bathrooms_elem:
                bathrooms_text = bathrooms_elem.get_text(strip=True)
                bathrooms = self._extract_number(bathrooms_text)
                
            area = None
            if area_elem:
                area_text = area_elem.get_text(strip=True)
                area = self._extract_area(area_text)
                
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
                    
            property_type = self._detect_property_type(title + " " + description)
            
            return self.create_listing(
                title=title,
                description=description,
                price=price,
                price_currency="ETB",
                location=location,
                property_type=property_type,
                area_sqm=area,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                images=images,
                posted_date=None,
                listing_type=listing_type,
                source_url=link or self.base_url,
                raw_data={"card_html": str(card)}
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing listing card: {e}")
            return None
    
    def _detect_listing_type(self, text: str) -> str:
        """Detect if listing is for sale, rent, or auction."""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['auction', 'ሱሚ', 'የጨረታ']):
            return "auction"
        elif any(kw in text_lower for kw in ['rent', 'ኪራይ', 'lease', 'for rent']):
            return "rent"
        elif any(kw in text_lower for kw in ['sale', 'ሽያይ', 'for sale', 'ለሽጡ']):
            return "sale"
        else:
            return "sale"
    
    def _detect_property_type(self, text: str) -> Optional[str]:
        """Detect property type from text."""
        text_lower = text.lower()
        
        property_types = {
            "apartment": ["apartment", "condo", "flat", "አፓርትማንት"],
            "house": ["house", "villa", "townhouse", "ቤት"],
            "office": ["office", "commercial space"],
            "store": ["store", "shop", "retail", "ሱቅ"],
            "warehouse": ["warehouse", "storage"],
            "land": ["land", "plot", "parcel", "ምድር", "ፕሎት"],
            "building": ["building", "apartment building"]
        }
        
        for prop_type, keywords in property_types.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return prop_type
                    
        return None
    
    def _extract_number(self, text: str) -> Optional[int]:
        """Extract integer from text."""
        match = re.search(r'(\d+)', text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None
    
    def _extract_area(self, text: str) -> Optional[float]:
        """Extract area in sqm from text."""
        patterns = [
            r'([\d,]+(?:\.\d+)?)\s*(?:sq\.?\s*m\.?|m²|sq\s*metres?|ካዕራ)',
            r'([\d,]+(?:\.\d+)?)\s*(?:sqft|ካረ)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    if 'sqft' in pattern.lower() or 'ካረ' in text:
                        value *= 0.0929
                    return value
                except ValueError:
                    pass
        return None