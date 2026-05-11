
"""
Source registry for all data providers.
Maps source keys to their configuration and metadata.
"""

# Source status indicators
SOURCE_STATUS = {
    "verified_working": "Source has been verified to return real property data",
    "verified_no_data": "Source is accessible but has no property listings",
    "blocked": "Source is blocked from current network environment",
    "requires_js": "Source requires JavaScript rendering (Playwright) for content",
    "unknown": "Status not yet verified"
}

SOURCE_REGISTRY = {
    # 1. Dedicated Real Estate Listing Platforms
    "addislist": {
        "name": "AddisList",
        "url": "https://addislist.com/property",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "high",
        "status": "requires_js",  # Requires Playwright for JS-rendered content
    },
    "engocha": {
        "name": "Engocha",
        "url": "https://engocha.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
        "status": "verified_working",  # Has property listings at /real-estate
    },

    # 2. Tender & Auction Aggregators
    "waliatender": {
        "name": "Walia Tender",
        "url": "https://www.waliatender.com",
        "category": "auction_aggregators",
        "valuation_signal": "liquidation_value",
        "scrapability": "blocked",
        "status": "blocked",  # Returns 403 Forbidden
    },

    # 3. Banking & Institutional Auction Sources
    "abyssinia": {
        "name": "Bank of Abyssinia",
        "url": "https://www.bankofabyssinia.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "timeout",
        "status": "blocked",  # Connection timeout
    },
    "amhara": {
        "name": "Amhara Bank",
        "url": "https://www.amharabank.com.et",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
        "status": "verified_working",  # Site accessible, scraper configured
    },
    "cbe": {
        "name": "Commercial Bank of Ethiopia",
        "url": "https://www.combanketh.et",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "blocked",
        "status": "blocked",  # Connection refused
    },
    "awash": {
        "name": "Awash Bank",
        "url": "https://awashbank.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "blocked",
        "status": "blocked",  # Connection refused
    },
    "berhan": {
        "name": "Berhan Bank",
        "url": "https://berhanbanksc.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "unknown",
        "status": "unknown",
    },
    "zemen": {
        "name": "Zemen Bank",
        "url": "https://www.zemenbank.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
        "status": "verified_working",  # Site accessible, scraper configured
    },
    "coop": {
        "name": "Cooperative Bank of Oromia",
        "url": "https://coopbankoromia.com.et",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "unknown",
        "status": "unknown",
    },
}

MARKET_PRICE_SOURCE_KEYS = [k for k, v in SOURCE_REGISTRY.items() if v["valuation_signal"] == "market_price"]
AUCTION_VALUE_SOURCE_KEYS = [k for k, v in SOURCE_REGISTRY.items() if v["valuation_signal"] in ["liquidation_value", "primary_auction"]]

# Working scrapers (sources that have been verified to work)
WORKING_SOURCES = [k for k, v in SOURCE_REGISTRY.items() if v.get("status") == "verified_working"]

def iter_sources(category=None, status=None):
    """Iterate through sources, optionally filtered by category or status."""
    for key, config in SOURCE_REGISTRY.items():
        if category and config["category"] != category:
            continue
        if status and config.get("status") != status:
            continue
        yield key, config
