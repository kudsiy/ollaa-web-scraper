
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from parsers.amharic_parser import AmharicParser

logger = logging.getLogger(__name__)

class SemanticProcessingEngine:
    """
    12-step Semantic Processing Engine for Ethiopian property listings.
    Enhanced with anchored extraction and advanced location patterns.
    """

    def __init__(self):
        self.amharic_parser = AmharicParser()
        self.developers = [
            "Noah", "Gift", "Ayat", "Flintstone", "Enessa", "Yotek", "Sunshine",
            "Tracon", "Ovid", "Metropolitan", "Varnero", "Zemen", "Eagle Hills",
            "Pluto", "Great Abyssinia", "Noc", "Tsehay", "Goh", "Habesha",
            "Enat", "Roha", "Bale", "DMC", "Mulugeta", "Yosef", "Taza", "Gishen",
            "Ababa", "Lideta", "Federal", "Commercial", "Kurat", "Real Estate",
            "Access", "Yugo", "Grand", "Luxury", "Adera", "Sega", "Yemane",
            "Bete", "Tsedey", "Warka", "Abyssinia", "Midroc", "Varnero"
        ]
        
        self.locations = {
            "Bole": [
                "Bole", "ቦሌ", "Bole Atlas", "Bole Medhanialem", "Bole Japan", 
                "Bole Bulbula", "Bulbula", "Imperial", "22", "Haya Hulet",
                "Gerji", "ገርጂ", "Summit", "ሰሚት", "Jackros", "ጃክሮስ",
                "Goro", "ጎሮ", "Wello Sefer", "ወሎ ሰፈር", "Rwanda", "Friendship",
                "Bole Arabsa", "ቦሌ አራብሳ", "Mera", "መሪ", "Loke", "ሎቄ"
            ],
            "Yeka": [
                "Yeka", "የካ", "Megenagna", "ሜገናኛ", "CMC", "Summit", "Ayat", "አያት", 
                "Gurd Shola", "ጉርድ ሾላ", "Kotebe", "ኮተቤ", "Figa", "ፊጋ",
                "Kara", "ካራ", "Salite Mihret", "ሳሊተ ምህረት", "Cheshire", "Ferensay"
            ],
            "Kirkos": [
                "Kirkos", "ቂርቆስ", "Kazanchis", "ካዛንቺስ", "Mexico", "ሜክሲኮ", 
                "Olympia", "ኦሊምፒያ", "Meskel Square", "መስቀል አደባባይ", "Lancha", "ላንቻ", 
                "Gotera", "ጎተራ", "Riche", "ሪቼ", "Sarbet", "ሳርቤት", "Bambis", "ባምቢስ"
            ],
            "Arada": [
                "Arada", "አራዳ", "Piassa", "ፒያሳ", "4 Kilo", "አራት ኪሎ", "6 Kilo", "ስድስት ኪሎ", 
                "Somali Tera", "ሶማሌ ተራ", "Churchill", "ቸርቺል", "Kebena", "ቀበና"
            ],
            "Lideta": [
                "Lideta", "ልደታ", "Geja Sefer", "ገጃ ሰፈር", "Balcha", "ባልቻ", "Mexico", "Abnet", "አብነት"
            ],
            "Nifas Silk Lafto": [
                "Nifas Silk", "Lafto", "ላፍቶ", "Lebu", "ለቡ", "Sarbet", "ሳርቤት", 
                "Jamo", "ጀሞ", "Haile Garment", "ሃይሌ ጋርመንት", "Mekanisa", "መካኒሳ",
                "Kera", "ቄራ", "Gotera", "Vayer", "Vayerero", "Hana"
            ],
            "Kolfe Keranio": [
                "Kolfe", "Keranio", "ኮልፌ", "ቀራኒዮ", "Zenebework", "ዘነበወርቅ", 
                "Ayertena", "አየር ጤና", "Total", "ቶታል", "Alem Bank", "ዓለም ባንክ",
                "Bethel", "ቤቴል", "Asko", "አስኮ", "Wingate", "ዊንጌት", "Tor Hailoch", "ጦር ኃይሎች"
            ],
            "Akaki Kality": [
                "Akaki", "አቃቂ", "Kality", "ቃሊቲ", "Tulu Dimtu", "ቱሉ ዲምቱ", 
                "Koye Feche", "ቆዬ ፈጬ", "Gelala", "ገላላ", "Saris", "ሳሪስ"
            ],
            "Gullele": [
                "Gullele", "ጉለሌ", "Shiromeda", "ሽሮ ሜዳ", "Addisu Gebeya", "አዲሱ ገበያ", 
                "Wingate", "ዊንጌት", "Pasta Factory", "Entoto", "እንጦጦ"
            ],
            "Addis Ketema": [
                "Addis Ketema", "አዲስ ከተማ", "Merkato", "መሪካቶ", "Autobus Tera", "አውቶብስ ተራ",
                "Sebategna", "ሰባተኛ", "Abnet", "አብነት"
            ],
            "Sheger City": [
                "Sheger", "ሸገር", "Sululta", "ሱሉልታ", "Burayu", "ቡራዩ", 
                "Sebeta", "ሰበታ", "Legetafo", "ለገጣፎ", "Sendafa", "ሰንዳፋ",
                "Gelan", "ገላን", "Dukem", "ዱከም", "Bishoftu", "ቢሾፍቱ"
            ]
        }

    def process(self, raw_listing: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the enhanced 12-step pipeline on a listing."""
        text = (raw_listing.get("title", "") + " " + raw_listing.get("description", "")).strip()
        normalized_text = self.amharic_parser.normalize_text(text)
        
        processed = raw_listing.copy()
        
        # 1. Intent Classification
        processed["intent"] = self._classify_intent(normalized_text)
        
        # 2. Listing Class
        processed["listing_class"] = self._classify_listing(normalized_text)
        
        # 3. Property Type/Subtype
        processed["property_type"], processed["property_subtype"] = self._detect_property_type(normalized_text)
        
        # 4. Area Resolution (Enhanced with Anchors)
        processed["area_sqm"], processed["area_type"] = self._resolve_area(normalized_text)
        
        # 5 & 10. Financial Extraction & Currency Detection (Enhanced with Anchors)
        financials = self._extract_financials(normalized_text)
        processed.update(financials)
        
        # 6. Finish States
        processed["finish_state"] = self._detect_finish_state(normalized_text)
        
        # 7. Developer Recognition
        processed["developer"] = self._recognize_developer(normalized_text)
        
        # 8. Location Map (Region, City, Subcity)
        location_details = self._map_location_detailed(normalized_text)
        processed.update(location_details)
        
        # 9. Contact Info
        processed["contacts"] = self._extract_contacts(normalized_text)
        
        # 11. Floor Level and Total Floors
        processed["floor_level"] = self._extract_floor_level(normalized_text)
        processed["total_floors"] = self._extract_total_floors(normalized_text)
        
        # 12. Rooms and Features
        features = self._extract_features(normalized_text)
        processed.update(features)
        
        # 13. Eligibility Logic
        processed["valuation_eligible"] = self._check_eligibility(processed)
        
        return processed

    def _classify_intent(self, text: str) -> str:
        sale_score = len(re.findall(r'sale|ሽያጭ|ሺያጭ|ለሽያጭ|የሚሸጥ|auction|ጨረታ|ሐራጅ', text, re.I))
        rent_score = len(re.findall(r'rent|ኪራይ|ለኪራይ|የሚከራይ', text, re.I))
        
        if sale_score > rent_score:
            return "SALE"
        elif rent_score > sale_score:
            return "RENT"
        return "SALE"  # Default

    def _classify_listing(self, text: str) -> str:
        if re.search(r'promotional|discount|special offer|ቅናሽ|ፕሮሞሽን', text, re.I):
            return "PROMOTIONAL"
        if re.search(r'wanted|inquiry|እፈልጋለሁ|ፈላጊ', text, re.I):
            return "INQUIRY"
        if re.search(r'auction|ጨረታ|ሐраጅ|foreclosure', text, re.I):
            return "AUCTION"
        for dev in self.developers:
            if dev.lower() in text.lower():
                return "DEVELOPER"
        return "DIRECT_LISTING"

    def _detect_property_type(self, text: str) -> (str, Optional[str]):
        if re.search(r'40/60|20/80|ኮንዶሚኒየም|condominium|condo', text, re.I):
            subtype = "40/60" if "40/60" in text else ("20/80" if "20/80" in text else None)
            return "CONDO", subtype
        if re.search(r'apartment|አፓርታማ|flat', text, re.I):
            return "APARTMENT", None
        if re.search(r'villa|ቪላ|G\+\d', text, re.I):
            return "VILLA", None
        if re.search(r'land|መሬት|plot|ማሳ', text, re.I):
            return "LAND", None
        if re.search(r'warehouse|መጋዘን', text, re.I):
            return "WAREHOUSE", None
        if re.search(r'office|ቢሮ', text, re.I):
            return "OFFICE", None
        if re.search(r'shop|ሱቅ', text, re.I):
            return "SHOP", None

        # Fallback to title indicators
        if "ቤት" in text or "house" in text.lower():
            return "HOUSE", None

        return "HOUSE", None  # Default

    def _anchored_extract(self, text: str, anchors: List[str], pattern: str) -> Optional[str]:
        """Extract value near an anchor keyword."""
        for anchor in anchors:
            # Look for anchor followed by optional separator and then the pattern
            # Support both English and Amharic separators
            full_pattern = rf"{anchor}[:\s\-\x16\x17\x18]*({pattern})"
            match = re.search(full_pattern, text, re.I)
            if match:
                return match.group(1)
        return None

    def _resolve_area(self, text: str) -> (Optional[float], str):
        # 1. Anchored extraction
        area_anchors = ["area", "size", "ቦታ", "ስፋት", "ካሬ", "ያረፈበት"]
        area_pattern = r"\d+(?:\.\d+)?"
        anchored_val = self._anchored_extract(text, area_anchors, area_pattern)
        
        area = None
        if anchored_val:
            try:
                area = float(anchored_val)
            except:
                pass

        if area is None:
            # 2. Standard patterns like 200 sqm, 200 ካሬ
            area_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:sqm|sq\.m|ካሬ|m2|M2|square\s*meter|square\s*metres|ካሬ\s*ሜትር)', text, re.I)
            if area_match:
                try:
                    area = float(area_match.group(1))
                except:
                    pass

        if area is None:
            # 3. Try Amharic numerals with ካሬ
            match = re.search(r'([፩-፼]+)\s*(?:ካሬ|ካሬ\s*ሜትር)', text)
            if match:
                val_str = match.group(1)
                parsed_nums = self.amharic_parser.extract_numbers(val_str)
                if parsed_nums:
                    area = parsed_nums[0]

        area_type = "PLOTTED"
        if re.search(r'built-up|ካርታ|ያረፈበት|መኖሪያ', text, re.I):
            area_type = "BUILT_UP"

        return area, area_type

    def _extract_financials(self, text: str) -> Dict[str, Any]:
        results = {"price": None, "currency": "ETB", "bank_loan_pct": None, "down_payment": None}
        
        # Currency Detection
        if re.search(r'\$|USD|ዶላር', text, re.I):
            results["currency"] = "USD"
        
        # 1. Anchored Price extraction
        price_anchors = ["price", "value", "ዋጋ", "ብር", "መነሻ ዋጋ", "total price"]
        price_pattern = r"[\d,]+(?:\.\d+)?"
        anchored_price = self._anchored_extract(text, price_anchors, price_pattern)
        
        if anchored_price:
            try:
                val = anchored_price.replace(',', '')
                results["price"] = float(val)
                # Check for million/k multipliers near the price
                context = text[text.find(anchored_price):text.find(anchored_price)+20].lower()
                if any(m in context for m in ['million', 'ሚሊዮን', 'm']):
                    results["price"] *= 1_000_000
                elif any(k in context for k in ['k', 'ሺህ']):
                    results["price"] *= 1_000
            except:
                pass
        
        if results["price"] is None:
            # 2. Price extraction (basic standard pattern)
            price_match = re.search(r'(?:price|ዋጋ|ብር|ETB)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|ሚሊዮን|M|k|ሺህ)?', text, re.I)
            if price_match:
                try:
                    val = price_match.group(1).replace(',', '')
                    price = float(val)
                    if 'million' in price_match.group(0).lower() or 'ሚሊዮን' in price_match.group(0).lower() or 'M' in price_match.group(0):
                        price *= 1_000_000
                    elif 'k' in price_match.group(0).lower() or 'ሺህ' in price_match.group(0).lower():
                        price *= 1_000
                    results["price"] = price
                except:
                    pass
        
        # Loan %
        loan_match = re.search(r'(\d+)\s*%\s*(?:loan|ባንክ|እዳ)', text, re.I)
        if loan_match:
            results["bank_loan_pct"] = float(loan_match.group(1))
            
        # Down payment
        down_match = re.search(r'(?:down payment|ቅድመ ክፍያ)\s*([\d,]+(?:\.\d+)?)', text, re.I)
        if down_match:
            results["down_payment"] = float(down_match.group(1).replace(',', ''))
            
        return results

    def _detect_finish_state(self, text: str) -> str:
        if re.search(r'unfinished|ያልተጠናቀቀ|ጥሬ|shell', text, re.I):
            return "UNFINISHED"
        if re.search(r'furnished|ቤት እቃ ያለው|የተሟላ', text, re.I):
            return "FURNISHED"
        if re.search(r'semi-finished|ከፊል የተጠናቀቀ', text, re.I):
            return "SEMI_FINISHED"
        return "FINISHED"

    def _recognize_developer(self, text: str) -> Optional[str]:
        for dev in self.developers:
            if dev.lower() in text.lower():
                return dev
        return None

    def _map_location_detailed(self, text: str) -> Dict[str, Any]:
        result = {"refined_location": None, "region": "Addis Ababa", "city": "Addis Ababa", "subcity": None}
        
        # 1. Anchored Location Extraction
        loc_anchors = ["location", "address", "ቦታ", "አድራሻ", "ክፍለ ከተማ", "ሰፈር"]
        # Pattern for location is trickier, let's look for known keywords near anchors
        for anchor in loc_anchors:
            match = re.search(rf"{anchor}[:\s\-]*([^\n,]+)", text, re.I)
            if match:
                loc_text = match.group(1)
                for zone, keywords in self.locations.items():
                    for kw in keywords:
                        if kw.lower() in loc_text.lower():
                            result["refined_location"] = zone
                            result["subcity"] = zone
                            if zone == "Sheger City":
                                result["city"] = "Sheger"
                            return result

        # 2. Fallback to global keyword search
        for zone, keywords in self.locations.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    result["refined_location"] = zone
                    result["subcity"] = zone
                    if zone == "Sheger City":
                        result["city"] = "Sheger"
                    return result
        return result

    def _extract_contacts(self, text: str) -> List[str]:
        # Ethiopian phone numbers: +251..., 09..., 07...
        phones = re.findall(r'(?:\+251|0)[79]\d{8}', text)
        # Telegram handles
        tg_handles = re.findall(r'@[\w\d_]+', text)
        return list(set(phones + tg_handles))

    def _extract_floor_level(self, text: str) -> Optional[int]:
        floor_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*(?:floor|ፎቅ)', text, re.I)
        if floor_match:
            return int(floor_match.group(1))
        return None

    def _extract_total_floors(self, text: str) -> Optional[int]:
        match = re.search(r'(?:total|ጠቅላላ)\s*(\d+)\s*(?:floors|ፎቅ)', text, re.I)
        if match:
            return int(match.group(1))
        return None

    def _extract_features(self, text: str) -> Dict[str, Any]:
        results = {
            "bedrooms": None, "bathrooms": None, "kitchens": None,
            "parking_spaces": None, "water_supply": False, "electricity": False
        }
        
        # Anchored feature extraction
        bed_anchors = ["bedroom", "መኝታ", "bed"]
        bath_anchors = ["bathroom", "መታጠቢያ", "ባኞ", "bath"]
        
        bed_val = self._anchored_extract(text, bed_anchors, r"\d+")
        if bed_val: results["bedrooms"] = int(bed_val)
        
        bath_val = self._anchored_extract(text, bath_anchors, r"\d+")
        if bath_val: results["bathrooms"] = int(bath_val)
        
        # Standard patterns fallback
        if results["bedrooms"] is None:
            bed_match = re.search(r'(\d+)\s*(?:bedroom|መኝታ)', text, re.I)
            if bed_match: results["bedrooms"] = int(bed_match.group(1))
        
        if results["bathrooms"] is None:
            bath_match = re.search(r'(\d+)\s*(?:bathroom|መታጠቢያ|ባኞ)', text, re.I)
            if bath_match: results["bathrooms"] = int(bath_match.group(1))
        
        kit_match = re.search(r'(\d+)\s*(?:kitchen|ወጥ ቤት)', text, re.I)
        if kit_match: 
            results["kitchens"] = int(kit_match.group(1))
        elif re.search(r'kitchen|ወጥ ቤት', text, re.I):
            results["kitchens"] = 1
        
        park_match = re.search(r'(\d+)\s*(?:parking|መኪና ማቆሚያ)', text, re.I)
        if park_match: 
            results["parking_spaces"] = int(park_match.group(1))
        elif re.search(r'parking|መኪና ማቆሚያ', text, re.I):
            results["parking_spaces"] = 1
        
        if re.search(r'water|ውሃ', text, re.I): results["water_supply"] = True
        if re.search(r'electricity|መብራት', text, re.I): results["electricity"] = True
        
        return results

    def _check_eligibility(self, processed: Dict[str, Any]) -> bool:
        """
        Determine if listing is eligible for automated valuation.
        Requires: price, location, property_type, and area.
        """
        required = ["price", "refined_location", "property_type", "area_sqm"]
        missing = [f for f in required if processed.get(f) is None]
        
        # Special case: Land doesn't need bedrooms but needs area and location
        if processed.get("property_type") == "LAND":
            if all(processed.get(f) is not None for f in ["price", "refined_location", "area_sqm"]):
                return True
        
        if not missing:
            return True
            
        logger.debug(f"Listing not valuation eligible. Missing: {missing}. Title: {processed.get('title')}")
        return False
