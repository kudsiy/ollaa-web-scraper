
"""
Amhara Bank auction scraper.
"""
from scrapers.banks.keyword_bank_scraper import KeywordBankScraper

class AmharaBankScraper(KeywordBankScraper):
    """
    Scraper for Amhara Bank foreclosure auctions.
    """
    
    def __init__(self):
        super().__init__(
            source_name="Amhara Bank",
            base_url="https://www.amharabank.com.et",
            auction_paths=[
                "/notice",
                "/ማስታወቂያ",
                "/auction",
                "/tender",
                "/bids",
                "/bids-and-tenders",
                "/foreclosure-sale",
                "/ሐራጅ"
            ]
        )
