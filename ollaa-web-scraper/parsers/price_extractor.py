"""
Price extractor for parsing ETB amounts from text.
Enhanced with patterns from Ethiopian real estate listing analysis.
"""
import logging
import re
from typing import Optional

from config import get_config

logger = logging.getLogger(__name__)

# Sanity bounds — below 1k or above 500M is almost certainly not a valid price
MIN_PRICE = 1000
MAX_PRICE = 500_000_000


class PriceExtractor:
    """
    Extract monetary values from property listings.
    Normalizes Ethiopian Birr (ETB) amounts from various text formats.

    Priority order (highest specificity first):
      1. _pattern_anchored_equals  — "ዋጋ = 17 ሚሊዮን ብር"
      2. _pattern_anchored         — "Price: 5,000,000"
      3. _pattern_million          — "2.5 million ETB"
      4. _pattern_parenthesis_million — "(38 million)"
      5. _pattern_large_birr       — "6,930,000 ብር"
      6. _pattern_etb              — "ETB 500,000"
      7. _pattern_br               — "Birr 500,000"
      8. _pattern_seven_digits     — plain 7–9 digit number
      9. _pattern_thousand         — "500 thousand / ሺህ"
     10. _pattern_numeric          — plain numeric fallback
    """

    def __init__(self):
        self.config = get_config()

    # ── Public API ────────────────────────────────────────────────────────────

    def extract(self, text: str) -> Optional[float]:
        """Extract the primary price from text. Returns ETB float or None."""
        if not text:
            return None

        text = text.strip()
        # FIX: Strip phone numbers BEFORE any pattern runs, so 09XXXXXXXX
        # and +251XXXXXXXXX are never matched by the fallback.
        clean = re.sub(r'\b09\d{8}\b', '', text)
        clean = re.sub(r'\+251\d{9}', '', clean)
        clean = re.sub(r'\b251\d{9}\b', '', clean)

        for method in [
            self._pattern_anchored_equals,
            self._pattern_anchored,
            self._pattern_million,
            self._pattern_parenthesis_million,
            self._pattern_large_birr,
            self._pattern_etb,
            self._pattern_br,
            self._pattern_seven_digits,
            self._pattern_thousand,
            self._pattern_numeric,
        ]:
            price = method(clean)
            if price is not None and MIN_PRICE <= price <= MAX_PRICE:
                return price

        return None

    def extract_all(self, text: str) -> list:
        """Extract all candidate prices found in text, sorted ascending."""
        if not text:
            return []
        prices = []
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:ሚሊዮን|million)',
            r'(\d{1,3}(?:,\d{3})+)\s*(?:ብር|ETB|Birr)',
            r'ETB\s*([\d,]+)',
            r'\b(\d{7,9})\b',
        ]
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                try:
                    raw = m.group(1).replace(',', '')
                    val = float(raw)
                    if 'million' in m.group(0).lower() or 'ሚሊዮን' in m.group(0):
                        val *= 1_000_000
                    if MIN_PRICE <= val <= MAX_PRICE and val not in prices:
                        prices.append(val)
                except Exception:
                    continue
        return sorted(prices)

    def format_price(self, price: float, currency: str = "ETB") -> str:
        if price >= 1_000_000:
            return f"{price / 1_000_000:.1f}M {currency}"
        elif price >= 1_000:
            return f"{price / 1_000:.0f}K {currency}"
        return f"{price:.2f} {currency}"

    def parse_price_range(self, text: str) -> tuple:
        pat = r'([\d,]+(?:\.\d+)?)\s*(?:M|million|K|k)?\s*[-–to]+\s*([\d,]+(?:\.\d+)?)\s*(?:M|million|K|k)?'
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                lo = float(m.group(1).replace(',', ''))
                hi = float(m.group(2).replace(',', ''))
                g = m.group(0)
                if 'M' in g or 'million' in g.lower():
                    lo *= 1_000_000
                    hi *= 1_000_000
                elif 'K' in g or 'k' in g:
                    lo *= 1_000
                    hi *= 1_000
                return (lo, hi)
            except ValueError:
                pass
        return (None, None)

    # ── Private extraction methods (highest → lowest specificity) ─────────────

    def _pattern_anchored_equals(self, text: str) -> Optional[float]:
        """
        Amharic price with explicit = separator: "ዋጋ = 17 ሚሊዮን ብር"
        """
        patterns = [
            r'(?:ዋጋ|price|value|መነሻ\s*ዋጋ|total\s*price)[^\d]{0,8}=\s*([\d,]+(?:\.\d+)?)\s*(?:ሚሊዮን|ሚሊየን|million)',
            r'(?:ዋጋ|price|value)[^\d]{0,8}=\s*([\d,]{5,})',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    val = float(m.group(1).replace(',', ''))
                    if val < 1000:
                        val *= 1_000_000
                    return val
                except Exception:
                    continue
        return None

    def _pattern_anchored(self, text: str) -> Optional[float]:
        """
        Anchored patterns: "Price: 5,000,000" / "ብር: 3,500,000"
        """
        anchors = ["price", "value", "ብር", "መነሻ ዋጋ", "total price", "ያለበት እዳ"]
        num_pat = r"([\d,]+(?:\.\d+)?)"
        for anchor in anchors:
            m = re.search(rf"{anchor}[:\s\-=\x16\x17\x18]*{num_pat}", text, re.IGNORECASE)
            if m:
                try:
                    val = float(m.group(1).replace(',', ''))
                    ctx = text[m.start(): m.end() + 20].lower()
                    if any(w in ctx for w in ['million', 'ሚሊዮን', 'ሚሊየን']):
                        val *= 1_000_000
                    elif any(w in ctx for w in ['ሺህ', 'thousand']):
                        val *= 1_000
                    return val if val >= MIN_PRICE else None
                except Exception:
                    continue
        return None

    def _pattern_million(self, text: str) -> Optional[float]:
        """
        Match "X million" or "X ሚሊዮን [ብር]" or "X M"
        Handles decimal millions: "2.5 million", "17 ሚሊዮን", "2.5M"
        """
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(?:million|mio|m|M)\s*(?:ETB|Birr|ብር)?',
            r'(?:ETB|Birr|ብር)\s*(\d+(?:[.,]\d+)?)\s*(?:million|mio|m|M)',
            r'(\d+(?:[.,]\d+)?)\s*(?:ሚሊዮን|ሚሊየን|ሚ)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    return float(m.group(1).replace(',', '')) * 1_000_000
                except Exception:
                    continue
        return None

    def _pattern_parenthesis_million(self, text: str) -> Optional[float]:
        """Match "(38 million)" or "(38 ሚሊዮን)" format."""
        m = re.search(
            r'\((\d+(?:\.\d+)?)\s*(?:million|ሚሊዮን|ሚሊየን)\)',
            text, re.IGNORECASE
        )
        if m:
            try:
                return float(m.group(1)) * 1_000_000
            except Exception:
                pass
        return None

    def _pattern_large_birr(self, text: str) -> Optional[float]:
        """
        Match comma-formatted large amounts with ብር/ETB/Birr suffix.
        e.g. "6,930,000 ብር" or "7,936,500ETB"
        """
        m = re.search(r'(\d{1,3}(?:,\d{3})+)\s*(?:ብር|ETB|Birr)', text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(',', ''))
            except Exception:
                pass
        return None

    def _pattern_etb(self, text: str) -> Optional[float]:
        """Match "ETB 500,000" or "500,000 ETB"."""
        patterns = [
            r'ETB\s*([\d,]+(?:\.\d{2})?)',
            r'([\d,]+(?:\.\d{2})?)\s*ETB',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    val = float(m.group(1).replace(',', ''))
                    return val if val >= MIN_PRICE else None
                except Exception:
                    continue
        return None

    def _pattern_br(self, text: str) -> Optional[float]:
        """Match "Birr 500,000" or "500,000 Birr"."""
        patterns = [
            r'Birr\s*([\d,]+(?:\.\d{2})?)',
            r'([\d,]+(?:\.\d{2})?)\s*Birr',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    val = float(m.group(1).replace(',', ''))
                    return val if val >= MIN_PRICE else None
                except Exception:
                    continue
        return None

    def _pattern_seven_digits(self, text: str) -> Optional[float]:
        """
        Last-resort: plain 7–9 digit number is almost certainly a price in birr.
        e.g. "6930000" or "12500000"
        Excludes numbers adjacent to known non-price contexts (phone, year, sqm).
        """
        for m in re.finditer(r'(?<!\d)(\d{7,9})(?!\d)', text):
            try:
                val = float(m.group(1))
                if m.group(1).startswith('09') or m.group(1).startswith('251'):
                    continue
                if MIN_PRICE <= val <= MAX_PRICE:
                    return val
            except Exception:
                continue
        return None

    def _pattern_thousand(self, text: str) -> Optional[float]:
        """Match "500 thousand", "500K", "500 ሺህ"."""
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(?:thousand|k|K)\s*(?:ETB|Birr|ብር)?',
            r'(\d+(?:[.,]\d+)?)\s*(?:ሺ|ሺህ)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    return float(m.group(1).replace(',', '')) * 1_000
                except Exception:
                    continue
        return None

    def _pattern_numeric(self, text: str) -> Optional[float]:
        """
        Match plain numeric values (fallback pattern).
        Only matches if the number is reasonably large for a property price.
        """
        pattern = r'([\d,]+(?:\.\d+)?)(?!\d)'
        m = re.search(pattern, text)
        if m:
            try:
                val_str = m.group(1).replace(',', '')
                if val_str.startswith('09') or val_str.startswith('251'):
                    return None
                val = float(val_str)
                return val
            except ValueError:
                pass
        return None
