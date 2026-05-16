"""
Arif Chereta scraper.
"""
import logging
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class ArifCheretaScraper(BaseTenderScraper):
    """
    Scraper for Arif Chereta notices.
    """
    
    base_url = "https://arifchereta.com"
    source_name = "Arif Chereta"
