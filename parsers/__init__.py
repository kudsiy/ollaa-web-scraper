"""Parsers package for Ollaa Web Scraper."""
from parsers.pdf_parser import PDFParser
from parsers.amharic_parser import AmharicParser
from parsers.price_extractor import PriceExtractor

__all__ = ["PDFParser", "AmharicParser", "PriceExtractor"]