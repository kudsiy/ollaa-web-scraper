
"""
Commercial Bank of Ethiopia auction scraper.
"""
from scrapers.banks.keyword_bank_scraper import KeywordBankScraper

class CBEScraper(KeywordBankScraper):
    """
    Scraper for CBE foreclosure auctions.
    """
    
    def __init__(self):
        super().__init__(
            source_name="Commercial Bank of Ethiopia",
            base_url="https://www.combanketh.et",
            auction_paths=["/notice", "/ማስታወቂያ"]
        )
