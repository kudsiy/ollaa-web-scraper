#!/usr/bin/env python3
"""
Scheduler for running Ollaa web scrapers on a configured schedule.
Manages scraper execution, error handling, and database insertion.
"""
import logging
import asyncio
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import schedule
import time
import threading

from config import get_config, Config
from etl.normalizer import Normalizer
from etl.deduplicator import Deduplicator
from etl.db_writer import DBWriter
from scrapers.base_scraper import ScrapeResult
from source_registry import SOURCE_REGISTRY, iter_sources
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
    RealEthioScraper
)
from scrapers.telegram_scraper import TelegramScraper
from etl.sheets_exporter import SheetsExporter
from etl.sheets_uploader import SheetsUploader


logger = logging.getLogger(__name__)


class ScraperScheduler:
    """
    Scheduler for running web scrapers on configurable intervals.
    Handles scraper lifecycle, ETL pipeline, and graceful shutdown.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.normalizer = Normalizer()
        self.db_writer = DBWriter()
        self.sheets_exporter = SheetsExporter()
        self.sheets_uploader = SheetsUploader(self.config.sheets)
        
        # Initialize deduplicator with a live connection if possible
        try:
            import psycopg2
            params = self.db_writer._get_connection_params()
            conn = psycopg2.connect(**params)
            self.deduplicator = Deduplicator(db_connection=conn)
        except Exception as e:
            logger.warning(f"Failed to connect for deduplicator: {e}")
            self.deduplicator = Deduplicator(db_connection=None)
            
        self._running = False
        self._shutdown_event = threading.Event()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._executor = ThreadPoolExecutor(max_workers=5)
        
        self.scrapers = {
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
            "telegram_ethio_real_estate": TelegramScraper("telegram_ethio_real_estate"),
            "telegram_betoch": TelegramScraper("telegram_betoch"),
        }


        
        self._scrape_history: List[Dict[str, Any]] = []
        self._total_stats = {
            "scrape_count": 0,
            "total_listings": 0,
            "total_duplicates": 0,
            "total_inserted": 0,
            "total_errors": 0,
        }
    
    def setup_logging(self) -> None:
        """Configure logging for the scheduler."""
        log_config = self.config.log
        
        # Use UTF-8 for both console and file logging to prevent encoding crashes
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(log_config.format))
        
        handlers = [stream_handler]
        
        if log_config.file_path:
            file_handler = logging.FileHandler(log_config.file_path, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(log_config.format))
            handlers.append(file_handler)
            
        logging.basicConfig(
            level=getattr(logging, log_config.level),
            handlers=handlers
        )
        
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("bs4").setLevel(logging.WARNING)
    
    def initialize(self) -> bool:
        """
        Initialize scheduler components.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing Ollaa Web Scraper Scheduler")
            
            if not self.db_writer.init_database():
                logger.error("Failed to initialize database")
                return False
                
            self.deduplicator.load_existing_hashes(since_days=7)
            
            self._register_scheduled_jobs()
            
            logger.info("Scheduler initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False
    
    def _register_scheduled_jobs(self) -> None:
        """Register all scheduled scraping jobs."""
        scheduler_config = self.config.scheduler
        
        if not scheduler_config.enabled:
            logger.info("Scheduler is disabled in configuration")
            return
            
        schedule.clear()
        
        schedule.every(scheduler_config.banks_interval_minutes).minutes.do(
            self._run_scraper_group, "banks"
        )
        
        schedule.every(scheduler_config.tenders_interval_minutes).minutes.do(
            self._run_scraper_group, "tenders"
        )
        
        schedule.every(scheduler_config.listings_interval_minutes).minutes.do(
            self._run_scraper_group, "listings"
        )
        
        schedule.every(30).minutes.do(
            self._run_scraper_group, "telegram"
        )
        
        schedule.every(24).hours.do(self._cleanup_old_data)
        
        logger.info("Scheduled jobs registered")
    
    def _run_scraper_group(self, group: str) -> None:
        """
        Run all scrapers in a specific group.
        
        Args:
            group: Group name ("banks", "tenders", "listings", "telegram")
        """
        category_map = {
            "banks": ["institutional_auctions", "auction_aggregators"],
            "tenders": ["auction_aggregators"],
            "listings": ["market_listings", "specialized_platforms"],
            "telegram": ["telegram_channels"]
        }
        
        categories = category_map.get(group, [group])
        
        scraper_names = []
        for key, config in SOURCE_REGISTRY.items():
            if config.get("category") in categories:
                scraper_names.append(key)
        
        # If no scrapers found by category, try the hardcoded mapping for backward compatibility
        if not scraper_names:
            scraper_mapping = {
                "banks": ["addislist", "abyssinia", "berhan", "amhara", "cbe", "awash", "dashen", "zemen", "coop"],
                "tenders": ["waliatender"],
                "listings": ["engocha"],
            }
            scraper_names = scraper_mapping.get(group, [])
        
        for name in scraper_names:
            if name in self.scrapers:
                self._run_single_scraper(name)
    
    def _run_single_scraper(self, scraper_name: str) -> Optional[ScrapeResult]:
        """
        Run a single scraper and process results.
        
        Args:
            scraper_name: Name of the scraper to run
            
        Returns:
            ScrapeResult or None if scraper not found
        """
        if scraper_name not in self.scrapers:
            logger.warning(f"Unknown scraper: {scraper_name}")
            return None
            
        scraper = self.scrapers[scraper_name]
        
        try:
            logger.info(f"Starting scraper: {scraper_name}")
            result = scraper.scrape()
            
            if result.success:
                self._process_scrape_result(result, scraper_name)
            else:
                logger.error(f"Scraper {scraper_name} failed: {result.errors}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error running scraper {scraper_name}: {e}")
            return None
    
    def _process_scrape_result(self, result: ScrapeResult, scraper_name: str) -> None:
        """
        Process scraped results through ETL pipeline.
        
        Args:
            result: ScrapeResult from scraper
            scraper_name: Name of the scraper
        """
        try:
            logger.info(f"Processing {result.scraped_count} listings from {scraper_name}")
            
            normalized_listings = []
            for i, listing in enumerate(result.listings):
                try:
                    if not listing.source_key:
                        listing.source_key = scraper_name
                    normalized = self.normalizer.normalize_listing(listing)
                    is_valid, errors = self.normalizer.validate_normalized(normalized)
                    
                    if is_valid:
                        normalized_listings.append(normalized)
                    else:
                        logger.debug(f"Invalid listing {i} from {scraper_name}: {errors}")
                except AttributeError as e:
                    # Capture which field might have caused the error
                    logger.error(f"AttributeError in {scraper_name} record {i}: {e}. Skipping record.")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error in {scraper_name} record {i}: {e}. Skipping record.")
                    continue
                    
            logger.info(f"Successfully normalized {len(normalized_listings)}/{len(result.listings)} listings from {scraper_name}")
            
            unique_listings, duplicate_count = self.deduplicator.deduplicate(normalized_listings)
            logger.info(f"Deduplication: {len(normalized_listings)} -> {len(unique_listings)} (removed {duplicate_count})")
            
            insert_stats = self.db_writer.insert_batch(unique_listings)
            logger.info(f"Insert stats: {insert_stats}")
            
            # Export to unified Google Sheets format (CSV)
            if unique_listings:
                export_filename = f"exports/unified_listings_{datetime.utcnow().strftime('%Y%m%d')}.csv"
                self.sheets_exporter.export_to_csv(unique_listings, export_filename)
                
                # Upload to Google Sheets if enabled
                if self.config.sheets.enabled:
                    self.sheets_uploader.upload_listings(unique_listings)
            
            self._update_stats(
                scrape_count=1,
                listings=result.scraped_count,
                duplicates=duplicate_count,
                inserted=insert_stats["inserted"],
                skipped=insert_stats["skipped"],
                errors=insert_stats["errors"]
            )
            
            self._log_scrape_history(scraper_name, result, insert_stats)
            
        except Exception as e:
            logger.error(f"Error processing scrape result: {e}")
            self._total_stats["total_errors"] += 1
    
    def _update_stats(self, **kwargs) -> None:
        """Update statistics counters."""
        for key, value in kwargs.items():
            if key in self._total_stats:
                self._total_stats[key] += value
    
    def _log_scrape_history(self, scraper_name: str, result: ScrapeResult, insert_stats: Dict) -> None:
        """Log scrape history entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "scraper": scraper_name,
            "success": result.success,
            "scraped_count": result.scraped_count,
            "inserted": insert_stats.get("inserted", 0),
            "skipped": insert_stats.get("skipped", 0),
            "errors": insert_stats.get("errors", 0),
            "duration_seconds": result.duration_seconds,
            "scrape_errors": result.errors
        }
        
        self._scrape_history.append(entry)
        
        if len(self._scrape_history) > 1000:
            self._scrape_history = self._scrape_history[-500:]
    
    def _cleanup_old_data(self) -> None:
        """Clean up old data from database."""
        try:
            logger.info("Running scheduled cleanup")
            deleted = self.db_writer.delete_old_listings(days=90)
            logger.info(f"Cleanup completed: {deleted} old listings deleted")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self._running:
            logger.warning("Scheduler is already running")
            return
            
        self._running = True
        self._shutdown_event.clear()
        
        self._scheduler_thread = threading.Thread(target=self._run_scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        logger.info("Scheduler started")
        
        self._run_initial_scrape()
    
    def _run_initial_scrape(self) -> None:
        """Run an initial scrape of all sources."""
        logger.info("Running initial scrape of all sources")
        
        for scraper_name in self.scrapers:
            self._run_single_scraper(scraper_name)
    
    def _run_scheduler_loop(self) -> None:
        """Main scheduler loop running in background thread."""
        logger.info("Scheduler loop started")
        
        while self._running and not self._shutdown_event.is_set():
            schedule.run_pending()
            time.sleep(1)
            
        logger.info("Scheduler loop stopped")
    
    def stop(self) -> None:
        """Stop the scheduler gracefully."""
        logger.info("Stopping scheduler...")
        
        self._running = False
        self._shutdown_event.set()
        
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=30)
            
        if self.deduplicator and self.deduplicator.db:
            try:
                self.deduplicator.db.close()
            except Exception:
                pass
                
        self._executor.shutdown(wait=True)
        
        logger.info("Scheduler stopped")
    
    def run_now(self, scraper_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run scraper(s) immediately.
        
        Args:
            scraper_name: Optional specific scraper to run
            
        Returns:
            Dictionary with results
        """
        results = {}
        
        if scraper_name:
            result = self._run_single_scraper(scraper_name)
            results[scraper_name] = {
                "success": result.success if result else False,
                "scraped_count": result.scraped_count if result else 0,
                "errors": result.errors if result else []
            }
        else:
            for name in self.scrapers:
                result = self._run_single_scraper(name)
                results[name] = {
                    "success": result.success if result else False,
                    "scraped_count": result.scraped_count if result else 0,
                    "errors": result.errors if result else []
                }
                
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "running": self._running,
            "scheduled_jobs": len(schedule.get_jobs()),
            "total_stats": self._total_stats,
            "cache_stats": self.deduplicator.get_cache_stats(),
            "recent_scrape_count": len(self._scrape_history),
            "database_stats": self.db_writer.get_listing_stats()
        }
    
    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent scrape history."""
        return self._scrape_history[-limit:]


def main():
    """Main entry point for the scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollaa Web Scraper Scheduler")
    parser.add_argument("--init-db", action="store_true", help="Initialize database schema")
    parser.add_argument("--run-once", action="store_true", help="Run all scrapers once and exit")
    parser.add_argument("--scraper", type=str, help="Run specific scraper")
    parser.add_argument("--stats", action="store_true", help="Show statistics and exit")
    parser.add_argument("--diagnostic", action="store_true", help="Run in diagnostic mode (no database required)")
    
    args = parser.parse_args()
    
    scheduler = ScraperScheduler()
    scheduler.setup_logging()
    
    if args.init_db:
        if scheduler.db_writer.init_database():
            print("Database initialized successfully")
            return 0
        else:
            print("Failed to initialize database")
            return 1
    
    if args.stats:
        scheduler.db_writer.init_database()
        stats = scheduler.db_writer.get_listing_stats()
        print(f"Database Stats: {stats}")
        return 0

    if args.diagnostic:
        logger.info("Running in DIAGNOSTIC mode - Database operations will be mocked")
        # Mock database initialization and writing
        scheduler.db_writer.init_database = lambda: True
        scheduler.db_writer.insert_batch = lambda listings: {"inserted": len(listings), "skipped": 0, "errors": 0}
        scheduler.db_writer.get_listing_stats = lambda: {"total": 0, "status": "diagnostic"}
        
        # Override deduplicator to not need DB
        from etl.deduplicator import Deduplicator
        scheduler.deduplicator = Deduplicator(db_connection=None)

    if args.run_once:
        if not scheduler.initialize():
            return 1
            
        results = scheduler.run_now(args.scraper)
        # Use safe print for unicode characters in various terminals
        try:
            print(f"Results: {results}")
        except UnicodeEncodeError:
            print("Results contain characters that cannot be displayed in this terminal. Writing to results.txt instead.")
            with open("results.txt", "w", encoding="utf-8") as f:
                f.write(str(results))
        
        stats = scheduler.get_stats()
        print(f"Statistics: {stats}")
        
        return 0 if all(r.get("success", False) for r in results.values()) else 1
    
    if not scheduler.initialize():
        return 1
        
    scheduler.start()
    
    try:
        while True:
            time.sleep(10)
            
            if not scheduler._running:
                break
                
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        scheduler.stop()
        
    return 0


if __name__ == "__main__":
    sys.exit(main())