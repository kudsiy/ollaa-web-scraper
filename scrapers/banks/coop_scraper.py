
"""
Cooperative Bank of Oromia auction scraper.
"""
from scrapers.banks.keyword_bank_scraper import KeywordBankScraper

class CoopBankScraper(KeywordBankScraper):
    """
    Scraper for Coop Bank foreclosure auctions.
    """
    
    def __init__(self):
        super().__init__(
            source_name="Cooperative Bank of Oromia",
            base_url="https://coopbankoromia.com.et",
            auction_paths=["/tenders", "/notice"]
        )
