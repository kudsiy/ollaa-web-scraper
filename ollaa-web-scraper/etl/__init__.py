"""ETL package for Ollaa Web Scraper."""
from etl.normalizer import Normalizer
from etl.deduplicator import Deduplicator
from etl.db_writer import DBWriter

__all__ = ["Normalizer", "Deduplicator", "DBWriter"]