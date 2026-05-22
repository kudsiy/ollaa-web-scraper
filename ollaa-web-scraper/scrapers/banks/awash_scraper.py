
"""
Awash Bank auction scraper.
"""
from scrapers.banks.keyword_bank_scraper import KeywordBankScraper

class AwashBankScraper(KeywordBankScraper):
    """
    Scraper for Awash Bank foreclosure auctions.
    """
    
    def __init__(self):
        super().__init__(
            source_name="Awash Bank",
            base_url="https://awashbank.com",
            auction_paths=[
                "/news",
                "/bids",
                "/auction",
                "/notice",
                "/ማስታወቂያ",
                "/tender",
                "/foreclosure",
                "/property-auctions"
            ]
        )
