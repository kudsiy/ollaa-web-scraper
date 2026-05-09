"""
Reporter Tenders scraper.
"""
import logging
from scrapers.tenders.merkato_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class ReporterTendersScraper(BaseTenderScraper):
    """
    Scraper for Reporter Tenders notices.
    """
    
    base_url = "https://reportertenders.com"
    source_name = "Reporter Tenders"
