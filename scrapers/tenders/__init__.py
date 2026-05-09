"""Tenders scrapers package."""
from scrapers.tenders.merkato_scraper import BaseTenderScraper
from scrapers.tenders.ethiopiantender_scraper import EthiopianTenderScraper
from scrapers.tenders.arifchereta_scraper import ArifCheretaScraper
from scrapers.tenders.reportertenders_scraper import ReporterTendersScraper
from scrapers.tenders.habeshatender_scraper import HabeshaTenderScraper
from scrapers.tenders.waliatender_scraper import WaliaTenderScraper

__all__ = [
    "BaseTenderScraper",
    "EthiopianTenderScraper",
    "ArifCheretaScraper",
    "ReporterTendersScraper",
    "HabeshaTenderScraper",
    "WaliaTenderScraper"
]
