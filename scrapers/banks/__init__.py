"""Banks scrapers package."""
from scrapers.banks.addislist_scraper import AddisListScraper
from scrapers.banks.abyssinia_scraper import AbyssiniaBankScraper
from scrapers.banks.berhan_scraper import BerhanBankScraper
from scrapers.banks.abay_scraper import AbayBankScraper
from scrapers.banks.dbe_scraper import DBEScraper
from scrapers.banks.amhara_scraper import AmharaBankScraper
from scrapers.banks.auctionet_scraper import AuctionEthiopiaScraper
from scrapers.banks.delala_scraper import DelalaAppScraper

__all__ = [
    "AddisListScraper", 
    "AbyssiniaBankScraper",
    "BerhanBankScraper",
    "AbayBankScraper",
    "DBEScraper",
    "AmharaBankScraper",
    "AuctionEthiopiaScraper",
    "DelalaAppScraper"
]
