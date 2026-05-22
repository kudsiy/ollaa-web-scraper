
"""
Berhan Bank auction scraper.
"""
from scrapers.banks.keyword_bank_scraper import KeywordBankScraper

class BerhanBankScraper(KeywordBankScraper):
    """
    Scraper for Berhan Bank foreclosure auctions.
    """
    
    def __init__(self):
        super().__init__(
            source_name="Berhan Bank",
            base_url="https://berhanbanksc.com",
            auction_paths=[
                "/news",
                "/bids-and-tenders",
                "/bids",
                "/auction",
                "/notice",
                "/ማስታወቂያ",
                "/tender",
                "/foreclosure",
                "/property-notices"
            ]
        )
