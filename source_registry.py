
"""
Source registry for all data providers.
Maps source keys to their configuration and metadata.
"""

SOURCE_REGISTRY = {
    # 1. Dedicated Real Estate Listing Platforms
    "addislist": {
        "name": "AddisList",
        "url": "https://addislist.com/property",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "high",
    },
    "engocha": {
        "name": "Engocha",
        "url": "https://engocha.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
    },

    # 2. Tender & Auction Aggregators
    "waliatender": {
        "name": "Walia Tender",
        "url": "https://www.waliatender.com",
        "category": "auction_aggregators",
        "valuation_signal": "liquidation_value",
        "scrapability": "medium",
    },

    # 3. Banking & Institutional Auction Sources
    "abyssinia": {
        "name": "Bank of Abyssinia",
        "url": "https://www.bankofabyssinia.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
    },
    "amhara": {
        "name": "Amhara Bank",
        "url": "https://www.amharabank.com.et",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
    },
    "cbe": {
        "name": "Commercial Bank of Ethiopia",
        "url": "https://www.combanketh.et",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
    },
    "awash": {
        "name": "Awash Bank",
        "url": "https://awashbank.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
    },
    "dashen": {
        "name": "Dashen Bank",
        "url": "https://dashenbanksc.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
    },
    "berhan": {
        "name": "Berhan Bank",
        "url": "https://berhanbanksc.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
    },
    "zemen": {
        "name": "Zemen Bank",
        "url": "https://www.zemenbank.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
    },
    "coop": {
        "name": "Cooperative Bank of Oromia",
        "url": "https://coopbankoromia.com.et",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
    },
}

MARKET_PRICE_SOURCE_KEYS = [k for k, v in SOURCE_REGISTRY.items() if v["valuation_signal"] == "market_price"]
AUCTION_VALUE_SOURCE_KEYS = [k for k, v in SOURCE_REGISTRY.items() if v["valuation_signal"] in ["liquidation_value", "primary_auction"]]

def iter_sources(category=None):
    """Iterate through sources, optionally filtered by category."""
    for key, config in SOURCE_REGISTRY.items():
        if category and config["category"] != category:
            continue
        yield key, config
