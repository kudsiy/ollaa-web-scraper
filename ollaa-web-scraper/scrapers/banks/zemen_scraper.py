
"""
Zemen Bank auction scraper.
"""
from scrapers.banks.keyword_bank_scraper import KeywordBankScraper

class ZemenBankScraper(KeywordBankScraper):
    """
    Scraper for Zemen Bank foreclosure auctions.
    """
    
    def __init__(self):
        super().__init__(
            source_name="Zemen Bank",
            base_url="https://www.zemenbank.com",
            auction_paths=["/notice", "/ማስታወቂያ"]
        )
