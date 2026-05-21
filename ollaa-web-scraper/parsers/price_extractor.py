"""
Price extractor for parsing ETB amounts from text.
Handles various formats including Amharic and English notations.
"""
import logging
import re
from typing import Optional

from config import get_config


logger = logging.getLogger(__name__)


class PriceExtractor:
    """
    Extract monetary values from property listings.
    Normalizes Ethiopian Birr (ETB) amounts from various text formats.
    """
    
    def __init__(self):
        self.config = get_config()
        
    def extract(self, text: str) -> Optional[float]:
        """
        Extract price from text string.
        Enhanced with more patterns and multipliers.
        
        Args:
            text: Text containing price information
            
        Returns:
            Price as float or None if not found
        """
        if not text:
            return None
            
        text = text.strip()
        
        # Pre-process: remove some common confusing text
        clean_text = re.sub(r'09\d{8}', '', text) # Remove phone numbers
        
        patterns = [
            self._pattern_anchored,
            self._pattern_million,
            self._pattern_thousand,
            self._pattern_etb,
            self._pattern_br,
            self._pattern_numeric
        ]
        
        for pattern in patterns:
            price = pattern(clean_text)
            if price is not None:
                return price
                
        return None

    def _pattern_anchored(self, text: str) -> Optional[float]:
        """Match anchored patterns like 'Price: 5,000,000'"""
        anchors = ["price", "value", "ዋጋ", "ብር", "መነሻ ዋጋ", "total price", "ያለበት እዳ"]
        pattern = r"([\d,]+(?:\.\d+)?)"
        for anchor in anchors:
            match = re.search(rf"{anchor}[:\s\-\x16\x17\x18]*{pattern}", text, re.I)
            if match:
                try:
                    val = float(match.group(1).replace(',', ''))
                    # Check for multipliers near the match
                    context = text[match.start():match.end()+20].lower()
                    if any(m in context for m in ['million', 'ሚሊዮን', 'm']):
                        val *= 1_000_000
                    elif any(k in context for k in ['k', 'ሺህ']):
                        val *= 1_000
                    return val
                except:
                    continue
        return None
    
    def _pattern_million(self, text: str) -> Optional[float]:
        """
        Match patterns like '2.5 million ETB' or '2.5M'
        """
        patterns = [
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|mio|m)\s*(?:ETB|Birr|ብር)?',
            r'(?:ETB|Birr|ብር)\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|mio|m)',
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:ሚሊዮን|ሚሊየን|ሚሊዮን|ሚ)',
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:mil|mill|millions)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    return value * 1_000_000
                except (ValueError, IndexError):
                    continue
        return None
    
    def _pattern_thousand(self, text: str) -> Optional[float]:
        """
        Match patterns like '500 thousand' or '500K'
        """
        patterns = [
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:thousand|k)\s*(?:ETB|Birr)?',
            r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:ሺ|ሺህ|ሺር)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    return value * 1_000
                except (ValueError, IndexError):
                    continue
        return None
    
    def _pattern_etb(self, text: str) -> Optional[float]:
        """
        Match patterns like 'ETB 500,000' or '500,000 ETB'
        """
        patterns = [
            r'[Eé]T[B]?\s*([\d,]+(?:\.\d{2})?)',
            r'([\d,]+(?:\.\d{2})?)\s*[Eé]T[B]?',
            r'(?:ብር|በር)\s*([\d,]+(?:\.\d{2})?)',
            r'([\d,]+(?:\.\d{2})?)\s*(?:ብር|በር)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _pattern_br(self, text: str) -> Optional[float]:
        """
        Match patterns like 'Br 500,000' or '500,000 Br'
        """
        patterns = [
            r'Br\s*([\d,]+(?:\.\d{2})?)',
            r'([\d,]+(?:\.\d{2})?)\s*Br',
            r'Birr\s*([\d,]+(?:\.\d{2})?)',
            r'([\d,]+(?:\.\d{2})?)\s*Birr'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _pattern_numeric(self, text: str) -> Optional[float]:
        """
        Match plain numeric values (fallback pattern).
        Only matches if the number is reasonably large for a property price.
        """
        pattern = r'([\d,]+(?:\.\d{2})?)'
        match = re.search(pattern, text)
        if match:
            try:
                value = float(match.group(1).replace(',', ''))
                if value >= 1000:
                    return value
            except ValueError:
                pass
        return None
    
    def extract_all(self, text: str) -> list:
        """
        Extract all prices found in text.
        
        Args:
            text: Text containing price information
            
        Returns:
            List of prices found
        """
        prices = []
        
        patterns = [
            r'[Eé]T[B]?\s*([\d,]+(?:\.\d{2})?)',
            r'([\d,]+(?:\.\d{2})?)\s*(?:million|mio|m)',
            r'([\d,]+(?:\.\d{2})?)\s*Br',
            r'([\d,]+(?:\.\d{2})?)\s*Birr',
            r'([\d,]+(?:\.\d{2})?)\s*(?:ብር|በር)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1 if match.lastindex else 0).replace(',', '')
                    value = float(value_str)
                    
                    if 'million' in match.group(0).lower():
                        value *= 1_000_000
                    elif 'k' in match.group(0).lower():
                        value *= 1_000
                        
                    if value not in prices:
                        prices.append(value)
                except (ValueError, IndexError):
                    continue
                    
        return sorted(prices)
    
    def format_price(self, price: float, currency: str = "ETB") -> str:
        """
        Format price for display.
        
        Args:
            price: Price value
            currency: Currency code
            
        Returns:
            Formatted price string
        """
        if price >= 1_000_000:
            return f"{price / 1_000_000:.1f}M {currency}"
        elif price >= 1_000:
            return f"{price / 1_000:.0f}K {currency}"
        else:
            return f"{price:.2f} {currency}"
    
    def parse_price_range(self, text: str) -> tuple:
        """
        Parse price ranges like '500K - 1M' or 'ETB 500,000 - 1,000,000'.
        
        Args:
            text: Text containing price range
            
        Returns:
            Tuple of (min_price, max_price) or (None, None)
        """
        pattern = r'([\d,]+(?:\.\d+)?)\s*(?:M|million|K|k|)?\s*[-–to]+\s*([\d,]+(?:\.\d+)?)\s*(?:M|million|K|k|)?'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            try:
                min_val = float(match.group(1).replace(',', ''))
                max_val = float(match.group(2).replace(',', ''))
                
                if 'M' in match.group(0) or 'million' in match.group(0):
                    min_val *= 1_000_000
                    max_val *= 1_000_000
                elif 'K' in match.group(0):
                    min_val *= 1_000
                    max_val *= 1_000
                    
                return (min_val, max_val)
            except ValueError:
                pass
                
        return (None, None)