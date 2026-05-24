"""
Utility for exporting merged Telegram and Web scraper data to a 57-column Google Sheets schema.
"""
import logging
import csv
import io
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Standardized 57-column Google Sheets Schema
# Groups: Identity (1-15), Pricing (16-27), Location (28-42), Size & Features (43-57)
UNIFIED_SCHEMA = [
    # Identity Group (15)
    "id", "source_key", "source_name", "source_url", "external_id",
    "title", "description", "property_type", "property_subtype", "listing_type",
    "listing_class", "developer", "posted_date", "closing_date", "scraped_at",
    
    # Pricing Group (12)
    "price", "currency", "price_period", "price_per_sqm", "bank_loan_pct",
    "down_payment", "installment_years", "remaining_debt", "valuation_eligible", "price_negotiable",
    "price_type", "financial_notes",
    
    # Location Group (15)
    "region", "city", "subcity", "woreda", "neighborhood",
    "site_name", "building_name", "floor_level", "refined_location", "latitude",
    "longitude", "map_link", "address_raw", "distance_from_main_road", "location_notes",
    
    # Size & Features Group (15)
    "area_sqm", "area_type", "bedrooms", "bathrooms", "kitchens",
    "balcony_count", "parking_spaces", "finish_state", "construction_status", "year_built",
    "total_floors", "water_supply", "electricity", "security_features", "content_hash"
]

class SheetsExporter:
    """
    Exports property listings in the 57-column standardized format.
    Handles merging of Web and Telegram scraper data.
    """
    def __init__(self, schema: Optional[List[str]] = None):
        self.schema = schema or UNIFIED_SCHEMA
        if len(self.schema) != 57:
            logger.warning(f"Schema has {len(self.schema)} columns instead of 57.")

    def format_listing(self, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map normalized data to the 57-column schema.
        Extracts nested information from raw_data if necessary.
        Ensures all 57 columns are present, filling missing values with None.
        """
        raw_data = normalized_data.get("raw_data", {})
        if isinstance(raw_data, str):
            try:
                import json
                raw_data = json.loads(raw_data)
            except:
                raw_data = {}
        
        # Identity Mapping
        formatted = {
            "id": normalized_data.get("id") or normalized_data.get("content_hash"),
            "source_key": normalized_data.get("source_key") or raw_data.get("source_key") or normalized_data.get("source_name", "").lower().replace(" ", ""),
            "source_name": normalized_data.get("source_name"),
            "source_url": normalized_data.get("source_url"),
            "external_id": raw_data.get("message_id") or raw_data.get("id") or raw_data.get("external_id") or normalized_data.get("external_id"),
            "title": normalized_data.get("title"),
            "description": normalized_data.get("description"),
            "property_type": normalized_data.get("property_type"),
            "property_subtype": normalized_data.get("property_subtype"),
            "listing_type": normalized_data.get("listing_type"),
            "listing_class": normalized_data.get("listing_class"),
            "developer": normalized_data.get("developer"),
            "posted_date": self._format_date(normalized_data.get("posted_date")),
            "closing_date": self._format_date(normalized_data.get("closing_date")),
            "scraped_at": self._format_date(normalized_data.get("scraped_at")),
        }
        
        # Pricing Mapping
        price = normalized_data.get("price")
        area = normalized_data.get("area_sqm")
        formatted.update({
            "price": price,
            "currency": normalized_data.get("price_currency", "ETB"),
            "price_period": raw_data.get("price_period") or ("monthly" if normalized_data.get("listing_type") == "rent" else "total"),
            "price_per_sqm": self._calculate_price_per_sqm(price, area),
            "bank_loan_pct": normalized_data.get("bank_loan_pct") or raw_data.get("bank_loan_pct"),
            "down_payment": normalized_data.get("down_payment") or raw_data.get("down_payment"),
            "installment_years": raw_data.get("installment_years"),
            "remaining_debt": raw_data.get("remaining_debt"),
            "valuation_eligible": "Yes" if normalized_data.get("valuation_eligible") else "No",
            "price_negotiable": raw_data.get("price_negotiable"),
            "price_type": raw_data.get("price_type") or ("starting" if normalized_data.get("listing_type") == "auction" else "fixed"),
            "financial_notes": raw_data.get("financial_notes"),
        })
        
        # Location Mapping
        location_raw = normalized_data.get("location", "")
        formatted.update({
            "region": normalized_data.get("region") or raw_data.get("region") or ("Addis Ababa" if any(x in location_raw for x in ["Addis", "አዲስ"]) else None),
            "city": normalized_data.get("city") or raw_data.get("city") or ("Addis Ababa" if any(x in location_raw for x in ["Addis", "አዲስ"]) else None),
            "subcity": normalized_data.get("subcity") or raw_data.get("subcity") or normalized_data.get("refined_location"),
            "woreda": raw_data.get("woreda"),
            "neighborhood": raw_data.get("neighborhood"),
            "site_name": raw_data.get("site_name"),
            "building_name": raw_data.get("building_name"),
            "floor_level": normalized_data.get("floor_level"),
            "refined_location": normalized_data.get("refined_location"),
            "latitude": raw_data.get("latitude"),
            "longitude": raw_data.get("longitude"),
            "map_link": raw_data.get("map_link"),
            "address_raw": location_raw,
            "distance_from_main_road": raw_data.get("distance_from_main_road"),
            "location_notes": raw_data.get("location_notes"),
        })
        
        # Size & Features Mapping
        formatted.update({
            "area_sqm": area,
            "area_type": normalized_data.get("area_type"),
            "bedrooms": normalized_data.get("bedrooms"),
            "bathrooms": normalized_data.get("bathrooms"),
            "kitchens": normalized_data.get("kitchens") or raw_data.get("kitchens"),
            "balcony_count": raw_data.get("balcony_count"),
            "parking_spaces": normalized_data.get("parking_spaces") or raw_data.get("parking_spaces"),
            "finish_state": normalized_data.get("finish_state"),
            "construction_status": raw_data.get("construction_status"),
            "year_built": raw_data.get("year_built"),
            "total_floors": normalized_data.get("total_floors") or raw_data.get("total_floors"),
            "water_supply": "Yes" if normalized_data.get("water_supply") else ("No" if normalized_data.get("water_supply") is False else None),
            "electricity": "Yes" if normalized_data.get("electricity") else ("No" if normalized_data.get("electricity") is False else None),
            "security_features": raw_data.get("security_features"),
            "content_hash": normalized_data.get("content_hash"),
        })
        
        # Ensure all 57 columns are present in the correct order (strict mapping)
        result = {}
        for col in self.schema:
            val = formatted.get(col)
            # Convert complex types to string representation to avoid CSV/sheets issues
            if isinstance(val, (list, dict)) and col == "raw_data":
                val = None  # raw_data is never a column in the schema
            result[col] = val
            
        return result

    def _format_date(self, dt: Any) -> Optional[str]:
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return str(dt) if dt else None

    def _calculate_price_per_sqm(self, price: Optional[float], area: Optional[float]) -> Optional[float]:
        if price and area and area > 0:
            try:
                return round(float(price) / float(area), 2)
            except (ValueError, TypeError):
                return None
        return None

    def export_to_csv(self, listings: List[Dict[str, Any]], filepath: str) -> bool:
        """
        Export list of normalized listings to a CSV file.
        """
        try:
            formatted_listings = [self.format_listing(l) for l in listings]
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=self.schema)
                writer.writeheader()
                writer.writerows(formatted_listings)
            logger.info(f"Successfully exported {len(formatted_listings)} listings to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return False

    def export_to_stream(self, listings: List[Dict[str, Any]]) -> io.StringIO:
        """
        Export list of normalized listings to a string stream.
        """
        output = io.StringIO()
        formatted_listings = [self.format_listing(l) for l in listings]
        writer = csv.DictWriter(output, fieldnames=self.schema)
        writer.writeheader()
        writer.writerows(formatted_listings)
        output.seek(0)
        return output
