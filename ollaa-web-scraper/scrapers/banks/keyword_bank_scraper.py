
"""
Unified scraper for banks using specific Amharic auction notice paths.
"""
import logging
import re
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper, ScrapedListing, ScrapeResult

logger = logging.getLogger(__name__)

class KeywordBankScraper(BaseScraper):
    """
    Generic scraper for banks that look for auction keywords in specific paths.
    """
    
    def __init__(self, source_name: str, base_url: str, auction_paths: List[str]):
        self.source_name = source_name
        self.base_url = base_url
        self.auction_paths = auction_paths
        super().__init__()
        
    def scrape(self) -> ScrapeResult:
        start_time = datetime.utcnow()
        result = ScrapeResult(success=False)
        
        try:
            self.logger.info(f"Starting {self.source_name} scrape")
            
            for path in self.auction_paths:
                url = self._get_absolute_url(path)
                self.logger.info(f"Fetching {url}")
                soup = self.scrape_page(url)
                if soup:
                    self._extract_listings_from_page(soup, result, url)
            
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            self.logger.error(f"Error during {self.source_name} scrape: {e}")
            result.errors.append(str(e))
            
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        return result
    
    def _extract_listings_from_page(self, soup: BeautifulSoup, result: ScrapeResult, current_url: str):
        """Extract listings from a page based on keywords and PDF links."""
        # Common containers for bank notices
        containers = soup.select('article, .post, .entry, tr, .tender-item, .auction-item, .card, .notice-item, li, div[class*="item"], div[class*="notice"]')
        
        # Keywords: የሐራጅ (auction) or ሽያጭ (sale) or ቤት (house/property) or ጨረታ (tender)
        keywords = ["የሐራጅ", "ሽያጭ", "ቤት", "ጨረታ", "ሐራጅ", "foreclosure", "auction", "tender"]
        
        found_count = 0
        for container in containers:
            text = container.get_text()
            if any(kw in text for kw in keywords):
                listing = self._parse_keyword_element(container, current_url)
                if listing:
                    result.listings.append(listing)
                    found_count += 1
        
        # Also look for PDF links that might contain auction notices
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        for link in pdf_links:
            link_text = link.get_text().lower()
            if any(kw in link_text for kw in ["auction", "ሐራጅ", "ጨረታ", "notice", "tender", "sale"]):
                pdf_url = self._get_absolute_url(link.get('href'))
                self.logger.info(f"Found potential auction PDF: {pdf_url}")
                result.listings.append(self.create_listing(
                    title=f"Auction Notice: {link.get_text(strip=True)}",
                    description=f"Auction notice found in PDF: {pdf_url}",
                    source_url=pdf_url,
                    listing_type="auction",
                    raw_data={"pdf_url": pdf_url}
                ))
                found_count += 1
        
        if found_count == 0:
            self.logger.info(f"No listings matching keywords found on {current_url}")
        else:
            self.logger.info(f"Found {found_count} potential listings on {current_url}")

    def _parse_keyword_element(self, element, current_url: str) -> Optional[ScrapedListing]:
        """Parse an element into a ScrapedListing."""
        try:
            title_elem = element.select_one('h1, h2, h3, h4, .title, a, b, strong')
            title = title_elem.get_text(strip=True) if title_elem else f"{self.source_name} Auction"
            
            # Clean up title if it's too long
            if len(title) > 200:
                title = title[:197] + "..."
                
            # Skip if title is too short or just a generic word
            if len(title) < 5:
                return None
                
            text = element.get_text(separator=" ", strip=True)
            price = self._extract_price(text)
            
            # Look for location and area (often near keywords)
            location = None
            area_sqm = None
            
            # Search in tables for specific fields (common in bank notices)
            for table in element.select('table'):
                for tr in table.select('tr'):
                    tds = tr.select('td, th')
                    if len(tds) >= 2:
                        key = tds[0].get_text(strip=True).lower()
                        val = tds[1].get_text(strip=True)
                        if any(k in key for k in ['area', 'ስፋት', 'ካሬ']):
                            m = re.search(r'(\d+(?:\.\d+)?)', val)
                            if m:
                                try: area_sqm = float(m.group(1).replace(',', ''))
                                except: pass
                        elif any(k in key for k in ['location', 'address', 'አድራሻ', 'ቦታ']):
                            location = val

            if not location:
                loc_match = re.search(r'(?:አድራሻ|ቦታ)[:\s]+([^,\n\.]+)', text)
                if loc_match:
                    location = loc_match.group(1).strip()
            
            if not area_sqm:
                area_match = re.search(r'(?:Area|ስፋት|ካሬ)[:\s]+([\d,]+)', text, re.I)
                if area_match:
                    try: area_sqm = float(area_match.group(1).replace(',', ''))
                    except: pass

            link_elem = element.select_one('a[href]')
            source_url = current_url
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                source_url = self._get_absolute_url(href)
            
            return self.create_listing(
                title=title,
                description=text[:1000],
                price=price,
                location=location,
                area_sqm=area_sqm,
                source_url=source_url,
                listing_type="auction",
                raw_data={"element_html": str(element)[:1000]}
            )
        except Exception as e:
            self.logger.debug(f"Error parsing element: {e}")
            return None

    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text."""
        if not text:
            return None
        # Look for numbers followed by ETB, Birr, or Amharic equivalents
        patterns = [
            r'([\d,]+(?:\.\d{2})?)\s*(?:ETB|Birr|ብር|Br)',
            r'(?:ዋጋ|ብር)[:\s]+([\d,]+(?:\.\d{2})?)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    pass
        return None
/home/engine/.bashrc: line 1: syntax error near unexpected token `('
/home/engine/.bashrc: line 1: `. /etc/profile.d/workload-containment.shn# ~/.bashrc: executed by bash(1) for non-login shells.'
/home/engine/.bashrc: line 1: syntax error near unexpected token `('
/home/engine/.bashrc: line 1: `. /etc/profile.d/workload-containment.shn# ~/.bashrc: executed by bash(1) for non-login shells.'
/home/engine/.bashrc: line 1: syntax error near unexpected token `('
/home/engine/.bashrc: line 1: `. /etc/profile.d/workload-containment.shn# ~/.bashrc: executed by bash(1) for non-login shells.'
