"""
Walia Tender scraper.
"""
import logging
from typing import Optional
from scrapers.base_scraper import ScrapedListing, ScrapeResult
from scrapers.tenders.merkato_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)



class WaliaTenderScraper(BaseTenderScraper):
    """
    Scraper for Walia Tender notices.
    """
    
    base_url = "https://www.waliatender.com"
    source_name = "Walia Tender"

    async def scrape_async(self) -> ScrapeResult:
        # Override to add debugging
        result = await super().scrape_async()
        return result

    def _parse_tender_item(self, item) -> Optional[ScrapedListing]:
        # Print raw HTML of the first item to understand the actual structure
        if not hasattr(self, '_first_item_printed'):
            print("\n--- WALIA TENDER DEBUG: FIRST ITEM HTML ---")
            print(item.prettify())
            print("--- END DEBUG ---\n")
            self._first_item_printed = True

        try:
            # Based on common tender site structures in Ethiopia
            title_elem = item.select_one(".tender-title, .title, h3, h4, a.tender-link, td:nth-child(2)")
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
