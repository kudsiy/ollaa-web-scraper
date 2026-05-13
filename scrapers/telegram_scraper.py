"""
Telegram scraper for Ethiopian property channels using Telethon.
"""
import os
import logging
import asyncio
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

from scrapers.base_scraper import BaseScraper, ScrapedListing, ScrapeResult
from source_registry import SOURCE_REGISTRY
from parsers.amharic_parser import AmharicParser
from parsers.ocr_engine import OCREngine

logger = logging.getLogger(__name__)

class TelegramScraper(BaseScraper):
    """
    Scraper for Telegram channels using Telethon.
    """
    
    def __init__(self, source_key: str):
        if source_key not in SOURCE_REGISTRY:
            raise ValueError(f"Unknown source key: {source_key}")
            
        self.source_config = SOURCE_REGISTRY[source_key]
        self.source_key = source_key
        self.base_url = self.source_config["url"]
        self.source_name = self.source_config["name"]
        
        super().__init__()
        
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.phone = os.getenv("TELEGRAM_PHONE")
        self.channel_id = self.source_config.get("channel_id")
        self.amharic_parser = AmharicParser()
        self.ocr_engine = OCREngine()
        self.client = None

    async def _init_client(self):
        if not self.client:
            if not self.api_id or not self.api_hash:
                logger.error("Telegram API credentials not set in environment variables.")
                return False
            
            # Using a temporary session file path
            session_path = f"session_{self.source_key}"
            self.client = TelegramClient(session_path, self.api_id, self.api_hash)
            
            # Start client with phone if provided, otherwise assume already authorized
            if self.phone:
                await self.client.start(phone=self.phone)
            else:
                await self.client.start()
        return True

    async def scrape_async(self, limit: Optional[int] = None) -> ScrapeResult:
        """
        Scrape messages from the configured Telegram channel.
        """
        start_time = datetime.now(timezone.utc)
        result = ScrapeResult(success=False)
        
        if limit is None:
            limit = self.config.scraper.fetch_limit

        start_date_str = self.config.scraper.start_date
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        
        if not await self._init_client():
            result.errors.append("Could not initialize Telegram client")
            return result

        logger.info(f"Scraping Telegram channel: {self.channel_id} with limit {limit} and start_date {start_date_str}")
        
        try:
            async with self.client:
                async for message in self.client.iter_messages(self.channel_id, limit=limit):
                    if message.date < start_date:
                        logger.info(f"Reached start_date {start_date_str}, stopping scrape.")
                        break
                        
                    if not message.text and not message.media:
                        continue
                    
                    listing = await self._parse_message(message)
                    if listing:
                        result.listings.append(listing)
                        
            result.success = True
            result.scraped_count = len(result.listings)
        except Exception as e:
            logger.error(f"Error scraping Telegram channel {self.channel_id}: {e}")
            result.errors.append(str(e))
            
        result.duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        return result

    async def _parse_message(self, message) -> Optional[ScrapedListing]:
        """
        Parse a Telegram message into a ScrapedListing.
        """
        return await self.build_record_from_telegram(message)

    async def build_record_from_telegram(self, message) -> Optional[ScrapedListing]:
        """
        Extracts data from Telegram message and builds a ScrapedListing.
        Feeds the semantic processing pipeline.
        """
        text = message.text or ""
        image_text = ""
        
        # If has media, try OCR as fallback or supplementary info
        if message.media:
            try:
                # Download media to memory
                buffer = io.BytesIO()
                await message.download_media(file=buffer)
                buffer.seek(0)
                
                if isinstance(message.media, MessageMediaPhoto):
                    image_text = self.ocr_engine.extract_from_image(buffer.read())
                elif isinstance(message.media, MessageMediaDocument):
                    # Check if it's a PDF
                    if message.media.document.mime_type == 'application/pdf':
                        pdf_bytes = buffer.read()
                        if self.ocr_engine.is_scanned_pdf(pdf_bytes):
                            image_text = self.ocr_engine.extract_from_pdf(pdf_bytes)
            except Exception as e:
                logger.warning(f"Failed to perform OCR on Telegram media: {e}")

        combined_text = f"{text}\n{image_text}".strip()
        if not combined_text:
            return None

        # Basic extraction using AmharicParser
        normalized_text = self.amharic_parser.normalize_text(combined_text)
        
        # Check if it's a property-related message
        if not self.amharic_parser.is_property_listing(normalized_text):
            return None

        location = self.amharic_parser.extract_location(combined_text)
        
        # Extract price if possible
        from parsers.price_extractor import PriceExtractor
        price_extractor = PriceExtractor()
        price = price_extractor.extract(combined_text)

        return ScrapedListing(
            source_url=f"https://t.me/{self.channel_id}/{message.id}",
            source_name=self.source_name,
            title=text[:100].replace("\n", " ") if text else "Telegram Listing",
            description=combined_text,
            price=price,
            location=location,
            posted_date=message.date,
            listing_type="market" if "market" in self.source_config.get("valuation_signal", "") else "auction",
            raw_data={
                "message_id": message.id,
                "has_media": message.media is not None,
                "ocr_performed": bool(image_text),
                "source_key": self.source_key
            }
        )

    def scrape(self) -> ScrapeResult:
        """Synchronous implementation of abstract method."""
        try:
            # Check if there's an existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # This might be tricky in some environments
                # For simplicity, we assume we can run it
                return loop.run_until_complete(self.scrape_async())
            else:
                return asyncio.run(self.scrape_async())
        except Exception as e:
            logger.error(f"Sync scrape failed: {e}")
            return ScrapeResult(success=False, errors=[str(e)])
