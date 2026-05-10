
"""
Dashen Bank auction scraper.
"""
from scrapers.banks.keyword_bank_scraper import KeywordBankScraper

class DashenBankScraper(KeywordBankScraper):
    """
    Scraper for Dashen Bank foreclosure auctions.
    """
    
    def __init__(self):
        super().__init__(
            source_name="Dashen Bank",
            base_url="https://dashenbanksc.com",
            auction_paths=["/notice", "/ማስታወቂያ"]
        )
