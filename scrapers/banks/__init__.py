
"""Banks scrapers package."""
from scrapers.banks.addislist_scraper import AddisListScraper
from scrapers.banks.abyssinia_scraper import AbyssiniaBankScraper
from scrapers.banks.berhan_scraper import BerhanBankScraper
from scrapers.banks.amhara_scraper import AmharaBankScraper
from scrapers.banks.cbe_scraper import CBEScraper
from scrapers.banks.awash_scraper import AwashBankScraper
from scrapers.banks.zemen_scraper import ZemenBankScraper
from scrapers.banks.coop_scraper import CoopBankScraper

__all__ = [
    "AddisListScraper", 
    "AbyssiniaBankScraper",
    "BerhanBankScraper",
    "AmharaBankScraper",
    "CBEScraper",
    "AwashBankScraper",
    "ZemenBankScraper",
    "CoopBankScraper"
]
