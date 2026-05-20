"""
Deduplicator for preventing duplicate listings in Ollaa database.
Uses content hashing and fuzzy matching for detection.
"""
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set, Optional

from config import get_config


logger = logging.getLogger(__name__)


class Deduplicator:
    """
    Deduplicates scraped listings using hash-based and fuzzy matching.
    """
    
    def __init__(self, db_connection=None):
        self.config = get_config()
        self.db = db_connection
        self._hash_cache: Set[str] = set()
        self._seen_urls: Set[str] = set()
        
    def load_existing_hashes(self, since_days: int = 30) -> None:
        """
        Load existing content hashes from database.
        
        Args:
            since_days: Load hashes from listings in the last N days
        """
        if not self.db:
            logger.warning("No database connection, skipping hash load")
            return
            
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=since_days)
            
            query = """
                SELECT content_hash, source_url 
                FROM web_scraped_listings 
                WHERE scraped_at >= %s
            """
            
            with self.db.cursor() as cursor:
                cursor.execute(query, (cutoff_date,))
                for row in cursor.fetchall():
                    if row[0]:
                        self._hash_cache.add(row[0])
                    if row[1]:
                        self._seen_urls.add(row[1])
                        
            logger.info(f"Loaded {len(self._hash_cache)} existing hashes")
            
        except Exception as e:
            logger.error(f"Error loading existing hashes: {e}")
    
    def deduplicate(self, listings: List[Dict[str, Any]]) -> tuple:
        """
        Deduplicate a list of normalized listings.
        Uses content hash (including many fields) and URL matching.
        Similar listings from different sources are allowed to persist.
        
        Args:
            listings: List of normalized listing dictionaries
            
        Returns:
            Tuple of (unique_listings, duplicate_count)
        """
        unique = []
        # Optimization: Group unique listings by source to speed up fuzzy matching
        unique_by_source: Dict[str, List[Dict[str, Any]]] = {}
        duplicates = 0
        
        for listing in listings:
            content_hash = listing.get("content_hash")
            # Generate hash if not present (using centralized method)
            if not content_hash:
                content_hash = self.generate_hash(listing)
                listing["content_hash"] = content_hash
            
            source_url = listing.get("source_url")
            source_name = listing.get("source_name", "Unknown")
            
            if source_name not in unique_by_source:
                unique_by_source[source_name] = []
            
            is_duplicate = False
            
            # 1. Exact hash match
            if content_hash and content_hash in self._hash_cache:
                is_duplicate = True
                logger.debug(f"Duplicate hash: {content_hash[:16]}...")
                
            # 2. URL match
            elif source_url and source_url in self._seen_urls:
                is_duplicate = True
                logger.debug(f"Duplicate URL: {source_url}")
                
            # 3. Fuzzy match WITHIN THE SAME SOURCE ONLY
            elif self._fuzzy_match_within_source(listing, unique_by_source[source_name]):
                is_duplicate = True
                logger.debug(f"Fuzzy match detected within source: {source_name}")
                
            if is_duplicate:
                duplicates += 1
            else:
                unique.append(listing)
                unique_by_source[source_name].append(listing)
                if content_hash:
                    self._hash_cache.add(content_hash)
                if source_url:
                    self._seen_urls.add(source_url)
                
        return (unique, duplicates)
    
    def _fuzzy_match_within_source(self, listing: Dict[str, Any], existing: List[Dict[str, Any]]) -> bool:
        """
        Perform fuzzy matching to detect near-duplicates ONLY within the same source.
        Different sources can have similar listings about the same property.
        
        Args:
            listing: Listing to check
            existing: List of existing listings to compare against
            
        Returns:
            True if duplicate detected
        """
        threshold = 0.95  # Much higher threshold - practically identical
        
        title = (listing.get("title", "") or "").lower().strip()
        source_name = listing.get("source_name")
        
        if not title or not source_name:
            return False
        
        for exist_listing in existing:
            # Only compare listings from the exact same source
            if exist_listing.get("source_name") != source_name:
                continue
                
            exist_title = (exist_listing.get("title", "") or "").lower().strip()
            
            # Only flag as duplicate if titles are virtually identical
            if self._string_similarity(title, exist_title) > threshold:
                return True
                
        return False
    
    def _fuzzy_match(self, listing: Dict[str, Any], existing: List[Dict[str, Any]]) -> bool:
        """
        Legacy fuzzy matching - kept for backward compatibility but no longer used by default.
        """
        return self._fuzzy_match_within_source(listing, existing)
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate string similarity using simple comparison.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not s1 or not s2:
            return 0.0
            
        if s1 == s2:
            return 1.0
            
        s1 = (s1 or "").lower()
        s2 = (s2 or "").lower()
        
        if s1 in s2 or s2 in s1:
            return 0.9
            
        return self._levenshtein_similarity(s1, s2)
    
    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate Levenshtein distance-based similarity.
        
        Args:
            s1: First string
            s2: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        if len(s1) > 100 or len(s2) > 100:
            s1 = s1[:100]
            s2 = s2[:100]
            
        len1, len2 = len(s1), len(s2)
        
        if len1 == 0 and len2 == 0:
            return 1.0
        if len1 == 0 or len2 == 0:
            return 0.0
            
        prev_row = list(range(len2 + 1))
        curr_row = [0] * (len2 + 1)
        
        for i in range(1, len1 + 1):
            curr_row[0] = i
            for j in range(1, len2 + 1):
                cost = 0 if s1[i-1] == s2[j-1] else 1
                curr_row[j] = min(
                    prev_row[j] + 1,
                    curr_row[j-1] + 1,
                    prev_row[j-1] + cost
                )
            prev_row, curr_row = curr_row, prev_row
            
        distance = prev_row[len2]
        max_len = max(len1, len2)
        
        return 1 - (distance / max_len)
    
    @staticmethod
    def _normalize_hash_value(value: Any) -> str:
        """Normalize values before hash composition for consistent hashing."""
        if value is None:
            return ""

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, (int, float)):
            return str(value)

        return (str(value) or "").strip().lower()

    @staticmethod
    def generate_hash(listing: Dict[str, Any]) -> str:
        """
        Generate a precise content hash for a listing.
        Includes identity, pricing, location, classification, and size fields
        to reduce aggressive deduplication across similar-but-distinct records.
        """
        hash_fields = [
            # Identity fields
            "id", "source_name", "source_key", "source_url", "external_id",
            "title", "description",
            
            # Pricing fields (include both price_currency and currency for schema compatibility)
            "price", "price_currency", "currency", "price_period", "price_type", "price_per_sqm",
            "listing_type", "listing_class",
            "property_type", "property_subtype",
            
            # Location fields
            "location", "refined_location", "region", "city", "subcity", "woreda", "neighborhood",
            "address_raw", "site_name", "building_name",
            
            # Size fields
            "area_sqm", "area_type", "bedrooms", "bathrooms", "kitchens", "parking_spaces",
            "balcony_count",
            
            # Property attributes
            "floor_level", "total_floors", "finish_state", "construction_status", "year_built",
            "water_supply", "electricity", "security_features",
            
            # Financial fields
            "developer", "posted_date", "closing_date",
            "bank_loan_pct", "down_payment", "installment_years", "remaining_debt", "valuation_eligible",
            "price_negotiable",
        ]

        parts = []
        for field in hash_fields:
            value = Deduplicator._normalize_hash_value(listing.get(field))
            parts.append(f"{field}:{value}")

        content = "|".join(parts)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def add_to_cache(self, listing: Dict[str, Any]) -> None:
        """
        Add a listing to the internal cache.
        
        Args:
            listing: Listing dictionary
        """
        content_hash = listing.get("content_hash")
        source_url = listing.get("source_url")
        
        if content_hash:
            self._hash_cache.add(content_hash)
        if source_url:
            self._seen_urls.add(source_url)
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get deduplicator cache statistics."""
        return {
            "hash_count": len(self._hash_cache),
            "url_count": len(self._seen_urls)
        }