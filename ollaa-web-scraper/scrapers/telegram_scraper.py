"""
Telegram scraper for Ethiopian property channels using web preview.
Uses requests + BeautifulSoup to scrape https://t.me/s/channelname
to avoid needing API credentials.
"""
import os
import logging
import re
import time
import random
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper, ScrapedListing, ScrapeResult
from source_registry import SOURCE_REGISTRY
from parsers.amharic_parser import AmharicParser
from parsers.ocr_engine import OCREngine

logger = logging.getLogger(__name__)

class TelegramScraper(BaseScraper):
    """
    Scraper for Telegram channels using the public web preview.
    Scrapes https://t.me/s/channelname to avoid needing API credentials.
    """
    
    def __init__(self, source_key: str):
        if source_key not in SOURCE_REGISTRY:
            raise ValueError(f"Unknown source key: {source_key}")
            
        self.source_config = SOURCE_REGISTRY[source_key]
        self.source_key = source_key
        self.base_url = self.source_config["url"]
        self.source_name = self.source_config["name"]
        
        # Override base_url to use the web preview URL
        self.channel_id = self.source_config.get("channel_id")
        self.web_preview_url = f"https://t.me/s/{self.channel_id}" if self.channel_id else self.base_url
        
        super().__init__()
        
        self.amharic_parser = AmharicParser()
        self.ocr_engine = OCREngine()
    
    def scrape(self) -> ScrapeResult:
        """
        Scrape Telegram channel messages from the public web preview.
        """
        start_time = datetime.now(timezone.utc)
        result = ScrapeResult(success=False)
        
        limit = self.config.scraper.fetch_limit
        start_date_str = self.config.scraper.start_date
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        
        logger.info(f"Scraping Telegram channel via web preview: {self.web_preview_url} with limit {limit}")
        
        try:
            # Use the existing session from BaseScraper
            messages = self._fetch_messages(limit, start_date)
            
            for msg_data in messages:
                listing = self._parse_message_data(msg_data)
                if listing:
                    result.listings.append(listing)
            
            result.success = True
            result.scraped_count = len(result.listings)
            
        except Exception as e:
            logger.error(f"Error scraping Telegram channel {self.channel_id}: {e}")
            result.errors.append(str(e))
        
        result.duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        return result
    
    def _fetch_messages(self, limit: int, start_date: datetime) -> List[Dict[str, Any]]:
        """
        Fetch messages from Telegram web preview.
        Uses pagination via the 'before' parameter to load older messages.
        """
        messages = []
        before = None
        
        for page_num in range(10):  # Max 10 pages to avoid excessive requests
            if len(messages) >= limit:
                break
            
            url = self.web_preview_url
            if before:
                url = f"{self.web_preview_url}?before={before}"
            
            self._rate_limit()
            
            try:
                response = self.session.get(
                    url,
                    timeout=self.config.scraper.request_timeout,
                    headers={
                        "User-Agent": self.config.scraper.user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Referer": "https://t.me/",
                    }
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, "lxml")
                
                # Find message containers in Telegram web preview
                # Messages are in div.tgme_widget_message_wrap or div.tgme_widget_message
                message_wraps = soup.select(
                    ".tgme_widget_message_wrap, "
                    ".tgme_widget_message, "
                    ".tgme_widget_message_bubble, "
                    "div[class*='message']"
                )
                
                if not message_wraps:
                    # Try parsing from the main content div
                    message_wraps = soup.select(".tgme_channel_history > div, .tgme_main > div")
                
                page_messages = []
                for msg_div in message_wraps:
                    msg_data = self._extract_message_data(msg_div)
                    if msg_data:
                        msg_date = msg_data.get("date")
                        if msg_date and msg_date < start_date:
                            continue
                        page_messages.append(msg_data)
                        if len(page_messages) >= limit:
                            break
                
                # Sort by date descending (newest first)
                page_messages.sort(key=lambda x: x.get("date", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
                messages.extend(page_messages)
                
                # Find the 'before' parameter for pagination
                # Telegram web preview uses a link with data-before or data-after attribute
                prev_link = soup.select_one("a.tgme_widget_message_prev, a[data-before], a[href*='before=']")
                if prev_link:
                    href = prev_link.get("href") or ""
                    before_match = re.search(r'before=(\d+)', href)
                    if before_match:
                        before = before_match.group(1)
                    else:
                        # Check data attributes
                        before = prev_link.get("data-before") or prev_link.get("data-after")
                else:
                    # Try to find the last message ID for pagination
                    if page_messages:
                        last_msg = page_messages[-1]
                        before = str(last_msg.get("message_id", ""))
                    
                    if not before:
                        logger.info("No more pages available")
                        break
                
                logger.debug(f"Fetched page {page_num + 1}, total messages: {len(messages)}")
                
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch Telegram page {page_num + 1}: {e}")
                break
        
        return messages[:limit]
    
    def _extract_message_data(self, msg_div) -> Optional[Dict[str, Any]]:
        """
        Extract data from a Telegram message div.
        """
        try:
            # Extract message ID from data attributes
            message_id = (
                msg_div.get("data-post") or 
                msg_div.get("data-message-id") or 
                msg_div.get("id", "")
            )
            
            # Extract text content
            text_div = msg_div.select_one(
                ".tgme_widget_message_text, "
                ".tgme_widget_message_bubble, "
                "div[class*='message_text'], "
                ".message-text"
            )
            text = text_div.get_text(separator="\n", strip=True) if text_div else ""
            
            if not text:
                # Try getting all text from the message div
                text = msg_div.get_text(separator="\n", strip=True)
            
            # Extract date
            date_elem = msg_div.select_one(
                ".tgme_widget_message_date, "
                "time, "
                ".message-date, "
                "a[href*='t.me/']:not([href*='/s/'])"
            )
            
            date = None
            if date_elem:
                date_str = date_elem.get("datetime") or date_elem.get_text(strip=True)
                if date_str:
                    try:
                        # Try ISO format first (from datetime attribute)
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        try:
                            # Try Telegram's common datetime format
                            date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                        except (ValueError, TypeError):
                            pass
            
            if not date:
                date = datetime.now(timezone.utc)
            
            # Extract media (images)
            media_imgs = msg_div.select("img.tgme_widget_message_photo, a.tgme_widget_message_photo_wrap img")
            images = []
            for img in media_imgs:
                src = img.get("src")
                if src:
                    images.append(src)
            
            # Extract link/post URL
            post_link = msg_div.select_one("a.tgme_widget_message_date, .tgme_widget_message_date a")
            source_url = self.web_preview_url
            if post_link:
                href = post_link.get("href")
                if href:
                    source_url = href
            
            # Extract message ID from post link or data
            if not message_id:
                msg_id_match = re.search(r'/(\d+)$', source_url)
                if msg_id_match:
                    message_id = msg_id_match.group(1)
            
            return {
                "message_id": str(message_id) if message_id else "",
                "text": text,
                "date": date,
                "images": images,
                "source_url": source_url,
            }
            
        except Exception as e:
            logger.debug(f"Error extracting message data: {e}")
            return None
    
    def _parse_message_data(self, msg_data: Dict[str, Any]) -> Optional[ScrapedListing]:
        """
        Parse extracted message data into a ScrapedListing.
        """
        try:
            text = msg_data.get("text", "")
            image_text = ""
            
            # Basic extraction using AmharicParser
            normalized_text = self.amharic_parser.normalize_text(text)
            
            # Check if it's a property-related message
            if not self.amharic_parser.is_property_listing(normalized_text):
                return None
            
            location = self.amharic_parser.extract_location(text)
            
            # Extract price if possible
            from parsers.price_extractor import PriceExtractor
            price_extractor = PriceExtractor()
            price = price_extractor.extract(text)
            
            # Create title from first line or first 100 chars
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            title = lines[0][:100] if lines else "Telegram Listing"
            
            return ScrapedListing(
                source_url=msg_data.get("source_url", self.web_preview_url),
                source_name=self.source_name,
                title=title,
                description=text[:2000],
                price=price,
                location=location,
                posted_date=msg_data.get("date"),
                images=msg_data.get("images", []),
                listing_type="market" if "market" in self.source_config.get("valuation_signal", "") else "auction",
                raw_data={
                    "message_id": msg_data.get("message_id", ""),
                    "has_media": len(msg_data.get("images", [])) > 0,
                    "source_key": self.source_key
                }
            )
        except Exception as e:
            logger.debug(f"Error parsing Telegram message: {e}")
            return None
