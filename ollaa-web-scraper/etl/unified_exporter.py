"""
Unified exporter for Ollaa Web Scraper.
Runs all verified scrapers and exports processed data to property_data.json 
and property_data_unified.csv (57-column Google Sheets schema).
"""
import json
import logging
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any

from source_registry import SOURCE_REGISTRY
from etl.normalizer import Normalizer
from etl.sheets_exporter import SheetsExporter
from etl.sheets_uploader import SheetsUploader
from etl.deduplicator import Deduplicator
from config import config

# Import all scrapers
from scrapers.banks import (
    AddisListScraper, AbyssiniaBankScraper, BerhanBankScraper, 
    AmharaBankScraper, CBEScraper, AwashBankScraper, 
    DashenBankScraper, ZemenBankScraper, CoopBankScraper
)
from scrapers.tenders.waliatender_scraper import WaliaTenderScraper
from scrapers.tenders.merkato_scraper import MerkatoScraper
from scrapers.tenders.ethiopiantender_scraper import EthiopianTenderScraper
from scrapers.tenders.afrotender_scraper import AfroTenderScraper
from scrapers.tenders.reportertenders_scraper import ReporterTendersScraper
from scrapers.tenders.auctionethiopia_scraper import AuctionEthiopiaScraper
from scrapers.tenders.egp_scraper import EGPScraper
from scrapers.tenders.tendersontime_scraper import TendersOnTimeScraper
from scrapers.tenders.globaltenders_scraper import GlobalTendersScraper

from scrapers.listings import (
    EngochaScraper, BetDelalaScraper, EthiopiaPropertyCentreScraper,
    EthiopiaRealtyScraper, EthioRealEstatesScraper, LivingEthioScraper,
    RealEthioScraper, JijiScraper
)
from scrapers.telegram_scraper import TelegramScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("unified_exporter")

async def run_exporter_async():
    """Run all verified scrapers and export results to JSON and CSV."""
    normalizer = Normalizer()
    sheets_exporter = SheetsExporter()
    sheets_uploader = SheetsUploader(config.sheets)
    deduplicator = Deduplicator()
    
    # Map source keys to scraper instances
    scraper_instances = {
        "addislist": AddisListScraper(),
        "abyssinia": AbyssiniaBankScraper(),
        "berhan": BerhanBankScraper(),
        "amhara": AmharaBankScraper(),
        "cbe": CBEScraper(),
        "awash": AwashBankScraper(),
        "dashen": DashenBankScraper(),
        "zemen": ZemenBankScraper(),
        "coop": CoopBankScraper(),
        "waliatender": WaliaTenderScraper(),
        "twomerkato": MerkatoScraper(),
        "ethiopiantender": EthiopianTenderScraper(),
        "afrotender": AfroTenderScraper(),
        "reportertenders": ReporterTendersScraper(),
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
        "telegram_ethio_real_estate": TelegramScraper("telegram_ethio_real_estate"),
        "telegram_betoch": TelegramScraper("telegram_betoch"),
    }
    
    all_normalized_listings = []
    fetch_limit = config.scraper.fetch_limit
    start_date_str = config.scraper.start_date
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    
    # Filter to only working sources as defined in source_registry
    verified_sources = [k for k, v in SOURCE_REGISTRY.items() if v.get("status") in ["verified_working", "requires_js"]]
    
    logger.info(f"Starting unified export for {len(verified_sources)} verified sources. Limit: {fetch_limit}, Start Date: {start_date_str}")

    semaphore = asyncio.Semaphore(3)  # Run 3 scrapers concurrently to avoid resource exhaustion

    async def scrape_source(source_key):
        # No early-exit here — all sources run; dedup handles cross-site overlap.
        # Volume is controlled by fetch_limit on each individual scraper instance.

        if source_key not in scraper_instances:
            logger.warning(f"No scraper implementation found for verified source: {source_key}")
            return []

        async with semaphore:
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

                source_listings = []
                if result.success:
                    logger.info(f"Successfully scraped {len(result.listings)} listings from {source_key}")
                    for listing in result.listings:
                        # Inject source_key into listing for normalizer to pick up
                        listing.source_key = source_key

                        # Normalize listing
                        normalized = normalizer.normalize_listing(listing)

                        # Date filtering
                        posted_date = normalized.get("posted_date")
                        if posted_date and posted_date < start_date:
                            continue

                        normalized["source_key"] = source_key
                        source_listings.append(normalized)
                    return source_listings
                else:
                    logger.error(f"Scraper {source_key} failed: {result.errors}")
                    return []
            except Exception as e:
                logger.exception(f"Unexpected error running scraper {source_key}: {e}")
                return []

    # Run all scrapers concurrently with semaphore
    tasks = [scrape_source(sk) for sk in verified_sources]
    results = await asyncio.gather(*tasks)

    # Flatten all results — deduplication handles cross-source overlaps
    # FIX: removed premature break that discarded data from later sources
    for source_listings in results:
        all_normalized_listings.extend(source_listings)
    # Apply ceiling only after all sources are collected
    if len(all_normalized_listings) > fetch_limit:
        all_normalized_listings = all_normalized_listings[:fetch_limit]

    # Deduplication
    logger.info(f"Performing deduplication on {len(all_normalized_listings)} listings")
    unique_listings, duplicate_count = deduplicator.deduplicate(all_normalized_listings)
    logger.info(f"Deduplication complete. Removed {duplicate_count} duplicates. {len(unique_listings)} remaining.")

    # Final Export to JSON
    json_output_file = "property_data.json"
    try:
        with open(json_output_file, "w", encoding="utf-8") as f:
            json.dump(unique_listings, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"Successfully exported {len(unique_listings)} listings to {json_output_file}")
    except Exception as e:
        logger.error(f"Failed to write JSON output file: {e}")

    # Final Export to CSV (Google Sheets schema)
    csv_output_file = "property_data_unified.csv"
    try:
        sheets_exporter.export_to_csv(unique_listings, csv_output_file)
        logger.info(f"Successfully exported {len(unique_listings)} listings to {csv_output_file}")
        
        # Upload to Google Sheets if enabled
        if config.sheets.enabled:
            sheets_uploader.upload_listings(unique_listings)
    except Exception as e:
        logger.error(f"Failed to write CSV output file: {e}")

if __name__ == "__main__":
    asyncio.run(run_exporter_async())
