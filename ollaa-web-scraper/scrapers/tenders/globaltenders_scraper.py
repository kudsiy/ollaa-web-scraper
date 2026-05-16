"""
Global Tenders scraper.
"""
import logging
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class GlobalTendersScraper(BaseTenderScraper):
    """
    Scraper for Global Tenders Ethiopia.
    """
    
    base_url = "https://www.globaltenders.com/ethiopia-tenders.php"
    source_name = "Global Tenders"
