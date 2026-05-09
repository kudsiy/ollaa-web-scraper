"""
Walia Tender scraper.
"""
import logging
from scrapers.tenders.merkato_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class WaliaTenderScraper(BaseTenderScraper):
    """
    Scraper for Walia Tender notices.
    """
    
    base_url = "https://www.waliatender.com"
    source_name = "Walia Tender"
