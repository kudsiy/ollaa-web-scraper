"""
Ollaa Web Scraper Package
Ethiopian Property Intelligence Platform

A modular scraper system for continuously monitoring Ethiopian bank auction,
tender, and real estate websites, normalizing all extracted property data into
the Ollaa PostgreSQL database.
"""

__version__ = "1.0.0"
__author__ = "Ollaa"
__description__ = "Web scraping module for Ethiopian property intelligence"

from scrapers.base_scraper import BaseScraper, ScrapedListing, ScrapeResult
from etl.normalizer import Normalizer
from etl.deduplicator import Deduplicator
from etl.db_writer import DBWriter

__all__ = [
    "BaseScraper",
    "ScrapedListing",
    "ScrapeResult",
    "Normalizer",
    "Deduplicator",
    "DBWriter",
]