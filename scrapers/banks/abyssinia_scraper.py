
"""
Bank of Abyssinia auction scraper.
"""
from scrapers.banks.keyword_bank_scraper import KeywordBankScraper

class AbyssiniaBankScraper(KeywordBankScraper):
    """
    Scraper for Bank of Abyssinia foreclosure auctions.
    """
    
    def __init__(self):
        super().__init__(
            source_name="Bank of Abyssinia",
            base_url="https://www.bankofabyssinia.com",
            auction_paths=["/የሐራጅ-ሽያጭ-ማስታወቂያ"]
        )
