"""
TendersOnTime scraper.
"""
import logging
from scrapers.tenders.base_tender_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class TendersOnTimeScraper(BaseTenderScraper):
    """
    Scraper for TendersOnTime Ethiopia.
    """
    
    base_url = "https://www.tendersontime.com/ethiopia-tenders/"
    source_name = "TendersOnTime"
