
"""
Source registry for all data providers.
Maps source keys to their configuration and metadata.
"""

# Source status indicators
SOURCE_STATUS = {
    "verified_working": "Source has been verified to return real property data",
    "verified_no_data": "Source is accessible but has no property listings",
    "broken": "Source is inaccessible or URL is invalid",
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
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "engocha": {
        "name": "Engocha",
        "url": "https://engocha.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "realethio": {
        "name": "Real Ethio",
        "url": "https://realethio.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "betdelala": {
        "name": "BetDelala",
        "url": "https://betdelala.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "high",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "ethiopiarealty": {
        "name": "Ethiopia Realty",
        "url": "https://ethiopiarealty.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "ethiopiapropertycentre": {
        "name": "Ethiopia Property Centre",
        "url": "https://ethiopiapropertycentre.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "high",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "etrealtor": {
        "name": "ET Realtor",
        "url": "https://etrealtor.com.et",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "ethiorealestates": {
        "name": "Ethio Real Estates",
        "url": "https://www.ethiorealestates.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "ethiopianproperties": {
        "name": "Ethiopian Properties",
        "url": "https://ethiopianproperties.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "zegebeya": {
        "name": "Zegebeya",
        "url": "https://zegebeya.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "afrobet": {
        "name": "AfroBet",
        "url": "https://afrobet.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "livingethio": {
        "name": "Living Ethio",
        "url": "https://livingethio.com",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "medium",
        "status": "verified_working",
        "valuation_worthy": True,
    },
    "jiji": {
        "name": "Jiji Ethiopia",
        "url": "https://jiji.com.et/real-estate",
        "category": "market_listings",
        "valuation_signal": "market_price",
        "scrapability": "high",
        "status": "requires_js",
        "valuation_worthy": True,
    },

    # 2. Tender & Auction Aggregators
    "waliatender": {
        "name": "Walia Tender",
        "url": "https://www.waliatender.com",
        "category": "auction_aggregators",
        "valuation_signal": "liquidation_value",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "twomerkato": {
        "name": "2Merkato Tenders",
        "url": "https://www.2merkato.com/tenders",
        "category": "auction_aggregators",
        "valuation_signal": "liquidation_value",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "ethiopiantender": {
        "name": "Ethiopian Tender",
        "url": "https://www.ethiopiantender.com",
        "category": "auction_aggregators",
        "valuation_signal": "liquidation_value",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "afrotender": {
        "name": "Afro Tender",
        "url": "https://afrotender.com",
        "category": "auction_aggregators",
        "valuation_signal": "liquidation_value",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "reportertenders": {
        "name": "Reporter Tenders",
        "url": "https://www.ethiopianreportertenders.com",
        "category": "auction_aggregators",
        "valuation_signal": "liquidation_value",
        "scrapability": "low",
        "status": "broken",
    },
    "auctionethiopia": {
        "name": "Auction Ethiopia",
        "url": "https://auction.et",
        "category": "auction_aggregators",
        "valuation_signal": "liquidation_value",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "egp": {
        "name": "eGP Ethiopia",
        "url": "https://egp.ppa.gov.et/egp/bids/published",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "tendersontime": {
        "name": "TendersOnTime",
        "url": "https://www.tendersontime.com/ethiopia-tenders/",
        "category": "auction_aggregators",
        "valuation_signal": "liquidation_value",
        "scrapability": "low",
        "status": "verified_working",
    },
    "globaltenders": {
        "name": "Global Tenders",
        "url": "https://www.globaltenders.com/ethiopia-tenders.php",
        "category": "auction_aggregators",
        "valuation_signal": "liquidation_value",
        "scrapability": "low",
        "status": "verified_working",
    },

    # 3. Banking & Institutional Auction Sources
    "abyssinia": {
        "name": "Bank of Abyssinia",
        "url": "https://www.bankofabyssinia.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "amhara": {
        "name": "Amhara Bank",
        "url": "https://www.amharabank.com.et",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "cbe": {
        "name": "Commercial Bank of Ethiopia",
        "url": "https://www.combanketh.et",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "high",
        "status": "broken",
    },
    "awash": {
        "name": "Awash Bank",
        "url": "https://awashbank.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "berhan": {
        "name": "Berhan Bank",
        "url": "https://berhanbanksc.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "zemen": {
        "name": "Zemen Bank",
        "url": "https://www.zemenbank.com",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
        "status": "verified_working",
    },
    "coop": {
        "name": "Cooperative Bank of Oromia",
        "url": "https://coopbankoromia.com.et",
        "category": "institutional_auctions",
        "valuation_signal": "primary_auction",
        "scrapability": "medium",
        "status": "verified_working",
    },
}

MARKET_PRICE_SOURCE_KEYS = [k for k, v in SOURCE_REGISTRY.items() if v["valuation_signal"] == "market_price"]
VALUATION_WORTHY_SOURCE_KEYS = [k for k, v in SOURCE_REGISTRY.items() if v.get("valuation_worthy")]
AUCTION_VALUE_SOURCE_KEYS = [k for k, v in SOURCE_REGISTRY.items() if v["valuation_signal"] in ["liquidation_value", "primary_auction"]]

# Working scrapers (sources that have been verified to work)
WORKING_SOURCES = [k for k, v in SOURCE_REGISTRY.items() if v.get("status") == "verified_working" or v.get("status") == "requires_js"]

def iter_sources(category=None, status=None):
    """Iterate through sources, optionally filtered by category or status."""
    for key, config in SOURCE_REGISTRY.items():
        if category and config["category"] != category:
            continue
        if status and config.get("status") != status:
            continue
        yield key, config
