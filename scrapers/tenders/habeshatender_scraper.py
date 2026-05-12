"""
Habesha Tender scraper.
"""
import logging
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class HabeshaTenderScraper(BaseTenderScraper):
    """
    Scraper for Habesha Tender notices.
    """
    
    base_url = "https://www.habeshatender.com"
    source_name = "Habesha Tender"
