
"""
Unified JSON exporter for Ollaa Web Scraper.
Runs all verified scrapers and exports processed data to property_data.json.
"""
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any

from source_registry import SOURCE_REGISTRY
from parsers.semantic_engine import SemanticProcessingEngine

# Import all scrapers
from scrapers.banks import (
    AddisListScraper, AbyssiniaBankScraper, BerhanBankScraper, 
    AmharaBankScraper, CBEScraper, AwashBankScraper, 
    ZemenBankScraper, CoopBankScraper
)
from scrapers.tenders.waliatender_scraper import WaliaTenderScraper
from scrapers.tenders.merkato_scraper import MerkatoScraper
from scrapers.tenders.ethiopiantender_scraper import EthiopianTenderScraper
from scrapers.tenders.afrotender_scraper import AfroTenderScraper
from scrapers.tenders.auctionethiopia_scraper import AuctionEthiopiaScraper
from scrapers.tenders.egp_scraper import EGPScraper
from scrapers.tenders.tendersontime_scraper import TendersOnTimeScraper
from scrapers.tenders.globaltenders_scraper import GlobalTendersScraper

from scrapers.listings import (
    EngochaScraper, BetDelalaScraper, EthiopiaPropertyCentreScraper,
    EthiopiaRealtyScraper, EthioRealEstatesScraper, LivingEthioScraper,
    RealEthioScraper, JijiScraper
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("json_exporter")

async def run_exporter_async():
    """Run all verified scrapers and export results to JSON."""
    semantic_engine = SemanticProcessingEngine()
    
    # Map source keys to scraper instances
    scraper_instances = {
        "addislist": AddisListScraper(),
        "abyssinia": AbyssiniaBankScraper(),
        "berhan": BerhanBankScraper(),
        "amhara": AmharaBankScraper(),
        "cbe": CBEScraper(),
        "awash": AwashBankScraper(),
        "zemen": ZemenBankScraper(),
        "coop": CoopBankScraper(),
        "waliatender": WaliaTenderScraper(),
        "twomerkato": MerkatoScraper(),
        "ethiopiantender": EthiopianTenderScraper(),
        "afrotender": AfroTenderScraper(),
        "auctionethiopia": AuctionEthiopiaScraper(),
        "egp": EGPScraper(),
        "tendersontime": TendersOnTimeScraper(),
        "globaltenders": GlobalTendersScraper(),
        "engocha": EngochaScraper(),
        "betdelala": BetDelalaScraper(),
        "ethiopiapropertycentre": EthiopiaPropertyCentreScraper(),
        "ethiopiarealty": EthiopiaRealtyScraper(),
        "ethiorealestates": EthioRealEstatesScraper(),
        "livingethio": LivingEthioScraper(),
        "realethio": RealEthioScraper(),
        "jiji": JijiScraper(),
    }
    
    all_processed_listings = []
    
    # Filter to only working sources as defined in source_registry
    verified_sources = [k for k, v in SOURCE_REGISTRY.items() if v.get("status") in ["verified_working", "requires_js"]]
    
    logger.info(f"Starting unified export for {len(verified_sources)} verified sources")
    
    for source_key in verified_sources:
        if source_key not in scraper_instances:
            logger.warning(f"No scraper implementation found for verified source: {source_key}")
            continue
            
        logger.info(f"Running scraper: {source_key}")
        scraper = scraper_instances[source_key]
        
        try:
            # Check if it's an async scraper
            if hasattr(scraper, 'scrape_async'):
                result = await scraper.scrape_async()
            else:
                # Run sync scraper in executor to not block event loop
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, scraper.scrape)
                
            if result.success:
                logger.info(f"Successfully scraped {len(result.listings)} listings from {source_key}")
                for listing in result.listings:
                    # Convert listing to flat dict for processing
                    listing_dict = {
                        "source_url": listing.source_url,
                        "source_name": listing.source_name,
                        "title": listing.title,
                        "description": listing.description,
                        "price": listing.price,
                        "location": listing.location,
                        "listing_type": listing.listing_type,
                        "scraped_at": listing.scraped_at.isoformat() if listing.scraped_at else datetime.utcnow().isoformat()
                    }
                    
                    # Apply Semantic Processing Engine
                    processed = semantic_engine.process(listing_dict)
                    
                    # Add original source key for reference
                    processed["source_key"] = source_key
                    
                    all_processed_listings.append(processed)
            else:
                logger.error(f"Scraper {source_key} failed: {result.errors}")
                
        except Exception as e:
            logger.exception(f"Unexpected error running scraper {source_key}: {e}")

    # Final Export
    output_file = "property_data.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_processed_listings, f, ensure_ascii=False, indent=2)
        logger.info(f"Successfully exported {len(all_processed_listings)} listings to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")

if __name__ == "__main__":
    asyncio.run(run_exporter_async())
