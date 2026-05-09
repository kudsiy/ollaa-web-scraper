"""
Normalizer for mapping scraped data to Ollaa schema.
Transforms raw scraped listings into database-ready format.
"""
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any

from config import get_config
from parsers.semantic_engine import SemanticProcessingEngine


logger = logging.getLogger(__name__)


class Normalizer:
    """
    Normalizes scraped property data to match the Ollaa schema.
    Handles field mapping, validation, and transformation.
    """
    
    def __init__(self):
        self.config = get_config()
        self.semantic_engine = SemanticProcessingEngine()
        
    def normalize_listing(self, listing) -> Dict[str, Any]:
        """
        Normalize a ScrapedListing to Ollaa schema format.
        
        Args:
            listing: ScrapedListing object
            
        Returns:
            Dictionary with normalized fields for database insert
        """
        # First perform basic normalization
        raw_data = listing.raw_data or {}
        
        # Apply semantic processing
        semantic_input = {
            "title": listing.title,
            "description": listing.description,
            "price": listing.price,
            "location": listing.location,
            "property_type": listing.property_type,
            "area_sqm": listing.area_sqm
        }
        semantic_results = self.semantic_engine.process(semantic_input)

        normalized = {
            "source_url": self._normalize_url(listing.source_url),
            "source_name": self._normalize_text(listing.source_name),
            "title": self._normalize_text(listing.title),
            "description": self._normalize_text(listing.description),
            "price": semantic_results.get("price") or self._normalize_price(listing.price),
            "price_currency": semantic_results.get("currency") or self._normalize_currency(listing.price_currency),
            "property_type": semantic_results.get("property_type") or self._normalize_property_type(listing.property_type),
            "property_subtype": semantic_results.get("property_subtype"),
            "location": semantic_results.get("refined_location") or self._normalize_location(listing.location),
            "area_sqm": semantic_results.get("area_sqm") or self._normalize_area(listing.area_sqm),
            "area_type": semantic_results.get("area_type"),
            "bedrooms": self._normalize_integer(listing.bedrooms),
            "bathrooms": self._normalize_integer(listing.bathrooms),
            "images": self._normalize_images(listing.images),
            "posted_date": self._normalize_date(listing.posted_date),
            "closing_date": self._normalize_date(listing.closing_date),
            "listing_type": (semantic_results.get("intent", "") or "").lower() or self._normalize_listing_type(listing.listing_type),
            "listing_class": semantic_results.get("listing_class"),
            "developer": semantic_results.get("developer"),
            "finish_state": semantic_results.get("finish_state"),
            "contacts": semantic_results.get("contacts"),
            "floor_level": semantic_results.get("floor_level"),
            "valuation_eligible": semantic_results.get("valuation_eligible", False),
            "content_hash": self._generate_hash(listing),
            "scraped_at": datetime.utcnow(),
            "raw_data": self._normalize_raw_data(listing.raw_data),
        }
        
        return normalized
    
    def _normalize_url(self, url: Optional[str]) -> Optional[str]:
        """Normalize and validate URL."""
        if not url:
            return None
            
        url = (url or "").strip()
        url = re.sub(r'\s+', '', url)
        
        if not url.startswith(('http://', 'https://')):
            return None
            
        return url
    
    def _normalize_text(self, text: Optional[str]) -> Optional[str]:
        """Normalize text fields."""
        if not text:
            return None
            
        text = (text or "").strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        if len(text) > 5000:
            text = text[:5000]
            
        return text if text else None
    
    def _normalize_price(self, price: Optional[float]) -> Optional[float]:
        """Normalize and validate price."""
        if price is None:
            return None
            
        try:
            price = float(price)
            if price < 0:
                return None
            if price > 1_000_000_000:
                return None
            return round(price, 2)
        except (ValueError, TypeError):
            return None
    
    def _normalize_currency(self, currency: Optional[str]) -> str:
        """Normalize currency code."""
        if not currency:
            return "ETB"
            
        currency_str = (str(currency) or "").upper().strip()
        
        if currency_str in ["ETB", "BIRR", "BR", "ብር"]:
            return "ETB"
            
        return currency_str
    
    def _normalize_property_type(self, prop_type: Optional[str]) -> Optional[str]:
        """Normalize property type to standard values."""
        if not prop_type:
            return None
            
        prop_type_str = (str(prop_type) or "").lower().strip()
        
        type_mapping = {
            "apartment": ["apartment", "condo", "condominium", "flat", "አፓርትማንት"],
            "house": ["house", "villa", "townhouse", "detached", "semi-detached", "ቤት"],
            "office": ["office", "office space", "commercial", "commercial space"],
            "store": ["store", "shop", "retail", "retail space"],
            "warehouse": ["warehouse", "storage", "storage space", "industrial"],
            "land": ["land", "plot", "parcel", "lot", "ምድር", "ፕሎት"],
            "building": ["building", "apartment building", "commercial building"],
        }
        
        for standard_type, variations in type_mapping.items():
            if prop_type_str in variations:
                return standard_type
            for var in variations:
                if var in prop_type_str:
                    return standard_type
                    
        return prop_type_str if prop_type_str else None
    
    def _normalize_location(self, location: Optional[str]) -> Optional[str]:
        """Normalize location string."""
        if not location:
            return None
            
        location = (location or "").strip()
        location = re.sub(r'\s+', ' ', location)
        location = (location or "").title()
        
        ethiopian_locations = [
            "Addis Ababa", "Bole", "Kazanchis", "Piassa", "Mexico",
            "Sarbet", "Megenagna", "Gerji", "Akaki", "Shaggar",
            "Lebu", "Kality", "CMC", "Summit", "Haya Hulet",
            "Korniche", "Qosqe", "Liberia", "Lemen", "Logistics",
            "Kara", "Adis Zemen", "Solisa", "Mekdes", "Gorgi",
            "Hamba", "Hole", "Mekdes", "Niger", "Adis", "Lebs"
        ]
        
        for known_loc in ethiopian_locations:
            if (known_loc or "").lower() in (location or "").lower():
                return known_loc
                
        return location if len(location) < 200 else location[:200]
    
    def _normalize_area(self, area: Optional[float]) -> Optional[float]:
        """Normalize area in square meters."""
        if area is None:
            return None
            
        try:
            area = float(area)
            if area < 0 or area > 100000:
                return None
            return round(area, 2)
        except (ValueError, TypeError):
            return None
    
    def _normalize_integer(self, value: Optional[int]) -> Optional[int]:
        """Normalize integer fields."""
        if value is None:
            return None
            
        try:
            value = int(value)
            if value < 0:
                return None
            if value > 100:
                return None
            return value
        except (ValueError, TypeError):
            return None
    
    def _normalize_images(self, images: list) -> list:
        """Normalize image URLs."""
        if not images:
            return []
            
        normalized = []
        for img_url in images:
            url = self._normalize_url(img_url)
            if url:
                normalized.append(url)
                
        return normalized[:20]
    
    def _normalize_date(self, date: Optional[datetime]) -> Optional[datetime]:
        """Normalize date fields."""
        if date is None:
            return None
            
        try:
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            if isinstance(date, datetime):
                if date.year < 1900 or date.year > 2100:
                    return None
                return date.replace(tzinfo=None)
        except (ValueError, TypeError):
            return None
            
        return None
    
    def _normalize_listing_type(self, listing_type: Optional[str]) -> str:
        """Normalize listing type to standard values."""
        if not listing_type:
            return "sale"
            
        listing_type_str = (str(listing_type) or "").lower().strip()
        
        type_mapping = {
            "auction": ["auction", "ሱሚ", "የጨረታ", "ጨረታ", "foreclosure", "bank auction"],
            "rent": ["rent", "ኪራይ", "lease", "rental", "to rent", "ለኪራይ"],
            "sale": ["sale", "ሽያይ", "for sale", "ለሽጡ", "ሽጡ", "sell", "sold"],
        }
        
        for standard_type, variations in type_mapping.items():
            if listing_type_str in variations:
                return standard_type
            for var in variations:
                if var in listing_type_str:
                    return standard_type
                    
        return "sale"
    
    def _generate_hash(self, listing) -> str:
        """Generate content hash for deduplication."""
        import hashlib
        
        content = (
            f"{listing.source_name or ''}|"
            f"{listing.title or ''}|"
            f"{listing.price or ''}|"
            f"{listing.location or ''}|"
            f"{listing.property_type or ''}"
        )
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _normalize_raw_data(self, raw_data: Dict) -> Dict:
        """Normalize raw data for storage."""
        if not raw_data:
            return {}
            
        normalized = {}
        for key, value in raw_data.items():
            if value is not None:
                if isinstance(value, (str, int, float, bool, list, dict)):
                    normalized[str(key)] = value
                    
        return normalized
    
    def validate_normalized(self, data: Dict[str, Any]) -> tuple:
        """
        Validate normalized data before insert.
        
        Args:
            data: Normalized data dictionary
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        if not data.get("source_url"):
            errors.append("Missing source_url")
            
        if not data.get("source_name"):
            errors.append("Missing source_name")
            
        if not data.get("title"):
            errors.append("Missing title")
            
        if data.get("price") and data["price"] < 0:
            errors.append("Invalid price (negative)")
            
        if data.get("images") and not isinstance(data["images"], list):
            errors.append("Invalid images format")
            
        return (len(errors) == 0, errors)