"""
Ethiopian Tender scraper.
"""
import logging
from scrapers.tenders.merkato_scraper import BaseTenderScraper

logger = logging.getLogger(__name__)


class EthiopianTenderScraper(BaseTenderScraper):
    """
    Scraper for Ethiopian Tender notices.
    """
    
    base_url = "https://ethiopiantender.com"
    source_name = "Ethiopian Tender"
