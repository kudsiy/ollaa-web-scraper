"""
Amharic text parser for extracting and normalizing Ethiopian property data.
Handles transliteration, character normalization, and script detection.
"""
import logging
import re
from typing import Optional, Dict, List, Any
from datetime import datetime
import unicodedata

from config import get_config


logger = logging.getLogger(__name__)


AMHARIC_CHARS_PATTERN = re.compile(
    r'[\u1200-\u137F\u1380-\u1399\u2D80-\u2DDF\uAB00-\uAB2F]+'
)

ETB_SYMBOLS = ["ETB", "Br", "Birr", "ብር", "በር", "ቢር"]
LOCATION_KEYWORDS = [
    " Addis Ababa", "አዲስ አበባ", "Addis", "Bole", "Kazanchis", "Piassa",
    "Mexico", "Sarbet", "Megenagna", "Gerji", "Akaki",
    "Lebu", "Kality", " CMC", "Summit", "Ayat", "Yeka", "Gullele", "Arada",
    "Kirkos", "Lideta", "Nifas Silk", "Lafto", "Kolfe Keranio", "Akaki Kality",
    "ሐረት", "ስልጣን", "ኮሚሽን", "ቦሌ", "ቂርቆስ", "የካ", "ጉለሌ", "አራዳ", "ልደታ", "ላፍቶ",
    "ፒያሳ", "ሜክሲኮ", "ሳርቤት", "ሜገና", "ገርጂ", "አቃቂ", "ቁጠባ", "ሳሚት", "አያት",
    "ኮሶሎ", "ሊቦን", "ጅራስ", "ጀሞ", "በርሸሳ", "አፍሪካ", "አምስር", "ስቲም", "ቄራ",
    "አለም", "ሮድስይ", "ለሜን", "ሎጀስቲክ", "ካራ", "አድሳር", "ሶሊሳ", "ማእከል", "ሀያ ሁለተ",
    "ካዛንቺስ", "ጃክሮስ", "ጎሮ", "ሰሚት", "ኮተቤ", "ሲኤምሲ", "ለቡ", "ቃሊቲ", "ቱሉ ዲምቱ",
    "ጎተራ", "ሳሪስ", "ቡልቡላ", "ሀያት", "ጃክሮስ", "ቦሌ አራብሳ", "መሪ", "ሎቄ", "ቤተል", "አየር ጤና", 
    "ጦር ኃይሎች", "አስኮ", "ዊንጌት", "ፈረንሳይ", "ጉርድ ሾላ", "ቦሌ ሚካኤል", "ቦሌ አትላስ", "ሀያት",
    "Lideta", "ልደታ", "Geja Sefer", "ገጃ ሰፈር", "Balcha", "ባልቻ", "Abnet", "አብነት",
    "Zenebework", "ዘነበወርቅ", "Ayertena", "አየር ጤና", "Total", "ቶታል", "Alem Bank", "ዓለም ባንክ",
    "Bethel", "ቤቴል", "Asko", "አስኮ", "Wingate", "ዊንጌት", "Shiromeda", "ሽሮ ሜዳ", 
    "Addisu Gebeya", "አዲሱ ገበያ", "Pasta Factory", "Entoto", "እንጦጦ", "Merkato", "መሪካቶ",
    "Autobus Tera", "አውቶብስ ተራ", "Sebategna", "ሰባተኛ", "Sheger", "ሸገር", "Sululta", "ሱሉልታ",
    "Burayu", "ቡራዩ", "Sebeta", "ሰበታ", "Legetafo", "ለገጣፎ", "Sendafa", "ሰንዳፋ", "Gelan", "ገላን",
    "Dukem", "ዱከም", "Bishoftu", "ቢሾፍቱ"
]

PROPERTY_KEYWORDS = [
    "ቤት", "ሽያጭ", "ሺያጭ", "ሽያች", "ሺያች", "ኪራይ", "ጨረታ", "ኮንዶሚኒየም", "ቪላ", "አፓርታማ", "መሬት",
    "ህንጻ", "ሱቅ", "መጋዘን", "ቢሮ", "ንግድ", "ቤት", "የንግድ", "የቤት", "ሳይት", "ማሳ", "ካሬ ሜትር",
    "House", "Sale", "Rent", "Auction", "Condominium", "Villa", "Apartment", "Land",
    "Building", "Shop", "Warehouse", "Office", "Commercial", "Residential", "Site", "Sq m", "Square meter"
]

AMHARIC_NORMALIZATION_MAP = {
    'ሐ': 'ሀ', 'ሑ': 'ሁ', 'ሒ': 'ሂ', 'ሓ': 'ሃ', 'ሔ': 'ሄ', 'ሕ': 'ህ', 'ሖ': 'ሆ',
    'ኀ': 'ሀ', 'ኁ': 'ሁ', 'ኂ': 'ሂ', 'ኃ': 'ሃ', 'ኄ': 'ሄ', 'ኅ': 'ህ', 'ኆ': 'ሆ',
    'ሠ': 'ሰ', 'ሡ': 'ሱ', 'ሢ': 'ሲ', 'ሣ': 'ሳ', 'ሤ': 'ሰ', 'ሥ': 'ስ', 'ሦ': 'ሶ',
    'ዐ': 'አ', 'ዑ': 'ኡ', 'ዒ': 'ኢ', 'ዓ': 'ኣ', 'ዔ': 'ኤ', 'ዕ': 'እ', 'ዖ': 'ኦ',
    'ፀ': 'ጸ', 'ፁ': 'ጹ', 'ፂ': 'ጺ', 'ፃ': 'ጻ', 'ፄ': 'ጼ', 'ፅ': 'ጽ', 'ፆ': 'ጾ'
}


class AmharicParser:
    """
    Parser for Amharic text extraction and normalization.
    Handles Ethiopian property listings in Amharic script.
    """
    
    def __init__(self):
        self.config = get_config()
        
    def detect_script(self, text: str) -> str:
        """
        Detect the primary script used in text.
        
        Args:
            text: Input text
            
        Returns:
            "amharic", "english", "mixed", or "unknown"
        """
        if not text:
            return "unknown"
            
        amharic_count = 0
        latin_count = 0
        
        for c in text:
            if self._is_amharic_char(c):
                amharic_count += 1
            elif c.isalpha():
                latin_count += 1
        
        total_alpha = amharic_count + latin_count
        if total_alpha == 0:
            return "unknown"
            
        amharic_ratio = amharic_count / total_alpha
        
        if amharic_ratio > 0.8:
            return "amharic"
        elif amharic_ratio < 0.2:
            return "english"
        else:
            return "mixed"
    
    def _is_amharic_char(self, char: str) -> bool:
        """Check if a character is Amharic script."""
        try:
            return "ETHIOPIC" in unicodedata.name(char, "").upper()
        except ValueError:
            return False
    
    def extract_text_blocks(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract text blocks from HTML, separating Amharic and English.
        
        Args:
            html_content: HTML content string
            
        Returns:
            List of text blocks with script type
        """
        from bs4 import BeautifulSoup
        
        blocks = []
        soup = BeautifulSoup(html_content, "html.parser")
        
        for element in soup.find_all(string=True):
            text = str(element).strip()
            if len(text) < 3:
                continue
                
            script_type = self.detect_script(text)
            if script_type != "unknown":
                blocks.append({
                    "text": text,
                    "script": script_type,
                    "parent_tag": element.parent.name if element.parent else None
                })
                
        return blocks
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison and storage.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        text = unicodedata.normalize("NFKC", text)
        for char, normalized in AMHARIC_NORMALIZATION_MAP.items():
            text = text.replace(char, normalized)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def transliterate_to_english(self, amharic_text: str) -> str:
        """
        Basic transliteration of Amharic to Latin script.
        Note: This is approximate; proper transliteration requires specialized library.
        
        Args:
            amharic_text: Text in Amharic script
            
        Returns:
            Approximate Latin transliteration
        """
        transliteration_map = {
            'ሀ': 'ha', 'ሁ': 'hu', 'ሂ': 'hi', 'ሃ': 'ha', 'ሄ': 'he', 'ህ': 'he', 'ሆ': 'ho',
            'ሐ': 'wa', 'ሑ': 'wu', 'ሒ': 'wi', 'ሓ': 'wa', 'ሔ': 'we', 'ሕ': 'we', 'ሖ': 'wo',
            'ሗ': 'wo',
            'ሠ': 'sa', 'ሡ': 'su', 'ሢ': 'si', 'ሣ': 'sa', 'ሤ': 'se', 'ሥ': 'se', 'ሦ': 'so',
            'ሧ': 'so',
            'ረ': 'ra', 'ሩ': 'ru', 'ሪ': 'ri', 'ራ': 'ra', 'ሬ': 're', 'ር': 're', 'ሮ': 'ro',
            'ሯ': 'ro',
            'ሰ': 'sa', 'ሱ': 'su', 'ሲ': 'si', 'ሳ': 'sa', 'ሴ': 'se', 'ስ': 'se', 'ሶ': 'so',
            'ሷ': 'so',
            'ሸ': 'sha', 'ሹ': 'shu', 'ሺ': 'shi', 'ሻ': 'sha', 'ሼ': 'she', 'ሽ': 'she', 'ሾ': 'sho',
            'ሿ': 'sho',
            'ቀ': "k'a", 'ቁ': "k'u", 'ቂ': "k'i", 'ቃ': "k'a", 'ቄ': "k'e", 'ቅ': "k'e",
            'ቆ': "k'o",
            'ቈ': "k'wa", 'ቊ': "k'wi", 'ቋ': "k'wa", 'ቌ': "k'we", 'ቍ': "k'wo",
            'በ': 'ba', 'ቡ': 'bu', 'ቢ': 'bi', 'ባ': 'ba', 'ቤ': 'be', 'ብ': 'be', 'ቦ': 'bo',
            'ቧ': 'bo',
            'ቨ': 'va', 'ቩ': 'vu', 'ቪ': 'vi', 'ቫ': 'va', 'ቬ': 've', 'ቭ': 've', 'ቮ': 'vo',
            'ቯ': 'vo',
            'ተ': 'ta', 'ቱ': 'tu', 'ቲ': 'ti', 'ታ': 'ta', 'ት': 'te', 'ቶ': 'to', 'ቷ': 'to',
            'ቸ': "cha", 'ቹ': 'chu', 'ቺ': 'chi', 'ቻ': 'cha', 'ቼ': 'che', 'ች': 'che',
            'ቾ': 'cho', 'ቿ': 'cho',
            'ኀ': "j'a", 'ኁ': "j'u", 'ኂ': "j'i", 'ኃ': "j'a", 'ኄ': "j'e", 'ኅ': "j'e",
            'ኆ': "j'o",
            'ኈ': "j'wa", 'ኊ': "j'wi", 'ኋ': "j'wa", 'ኌ': "j'we", 'ኍ': "j'wo",
            'ነ': "na", 'ኑ': 'nu', 'ኒ': 'ni', 'ና': 'na', 'ኔ': 'ne', 'ን': 'ne', 'ኖ': 'no',
            'ኗ': 'no',
            'ኘ': "nya", 'ኙ': 'nyu', 'ኚ': 'nyi', 'ኛ': 'nya', 'ኜ': 'nye', 'ኝ': 'nye',
            'ኞ': 'nyo', 'ኟ': 'nyo',
            'አ': "a'", 'ኡ': "u'", 'ኢ': "i'", 'ኣ': "a'", 'ኤ': "e'", 'እ': "e'", 'ኦ': "o'",
            'ኧ': "e'",
            'ከ': "k'a", 'ኩ': "k'u", 'ኪ': "k'i", 'ካ': "k'a", 'ኬ': "k'e", 'ክ': "k'e",
            'ኮ': "k'o",
            'ኰ': "k'wa", 'ኲ': "k'wi", 'ኳ': "k'wa", 'ኴ': "k'we", 'ኵ': "k'wo",
            'ኸ': "x'a", 'ኹ': 'xu', 'ኺ': 'xi', 'ኻ': 'xa', 'ኼ': 'xe', 'ኽ': 'xe', 'ኾ': 'xo',
            'ዀ': "x'wa", 'ዂ': "x'wi", 'ዃ': "x'wa", 'ዄ': "x'we", 'ዅ': "x'wo",
            'ወ': 'wa', 'ዉ': 'wu', 'ዊ': 'wi', 'ዋ': 'wa', 'ዌ': 'we', 'ው': 'we', 'ዎ': 'wo',
            'ዏ': 'wo',
            'ዐ': "a'", 'ዑ': "u'", 'ዒ': "i'", 'ዓ': "a'", 'ዔ': "e'", 'ዕ': "e'", 'ዖ': "o'",
            'ዘ': 'za', 'ዙ': 'zu', 'ዚ': 'zi', 'ዛ': 'za', 'ዜ': 'ze', 'ዝ': 'ze', 'ዞ': 'zo',
            'ዟ': 'zo',
            'ዠ': 'zha', 'ዡ': 'zhu', 'ዢ': 'zhi', 'ዣ': 'zha', 'ዤ': 'zhe', 'ዥ': 'zhe',
            'ዦ': 'zho', 'ዧ': 'zho',
            'የ': 'ya', 'ዩ': 'yu', 'ዪ': 'yi', 'ያ': 'ya', 'ዬ': 'ye', 'ይ': 'ye', 'ዮ': 'yo',
            'ዯ': 'yo',
            'ደ': 'da', 'ዱ': 'du', 'ዲ': 'di', 'ዳ': 'da', 'ዴ': 'de', 'ድ': 'de', 'ዶ': 'do',
            'ዷ': 'do',
            'ዸ': 'dda', 'ዹ': 'ddu', 'ዺ': 'ddi', 'ዻ': 'dda', 'ዼ': 'dde', 'ዽ': 'dde',
            'ዾ': 'ddo', 'ዿ': 'ddo',
            'ጀ': 'ja', 'ጁ': 'ju', 'ጂ': 'ji', 'ጃ': 'ja', 'ጄ': 'je', 'ጅ': 'je', 'ጆ': 'jo',
            'ጇ': 'jo',
            'ገ': 'ga', 'ጉ': 'gu', 'ጊ': 'gi', 'ጋ': 'ga', 'ጌ': 'ge', 'ግ': 'ge', 'ጎ': 'go',
            'ጏ': 'go',
            'ጐ': 'gwa', 'ጒ': 'gwi', 'ጓ': 'gwa', 'ጔ': 'gwe', 'ጕ': 'gwo',
            'ጘ': 'gna', 'ጙ': 'gnu', 'ጚ': 'gni', 'ጛ': 'gna', 'ጜ': 'gne', 'ጝ': 'gne',
            'ጞ': 'gno', 'ጟ': 'gno',
            'ጠ': "t'a", 'ጡ': "t'u", 'ጢ': "t'i", 'ጣ': "t'a", 'ጤ': "t'e", 'ጥ': "t'e",
            'ጦ': "t'o", 'ጧ': "t'o",
            'ጨ': "ts'a", 'ጩ': "ts'u", 'ጪ': "ts'i", 'ጫ': "ts'a", 'ጬ': "ts'e", 'ጭ': "ts'e",
            'ጮ': "ts'o", 'ጯ': "ts'o",
            'ጰ': "p'a", 'ጱ': "p'u", 'ጲ': "p'i", 'ጳ': "p'a", 'ጴ': "p'e", 'ጵ': "p'e",
            'ጶ': "p'o", 'ጷ': "p'o",
            'ጸ': "tsa", 'ጹ': 'tsu', 'ጺ': 'tsi', 'ጻ': 'tsa', 'ጼ': 'tse', 'ጽ': 'tse',
            'ጾ': 'tso', 'ጿ': 'tso',
            'ፀ': 'tsa', 'ፁ': 'tsu', 'ፂ': 'tsi', 'ፃ': 'tsa', 'ፄ': 'tse', 'ፅ': 'tse',
            'ፆ': 'tso',
            'ፈ': 'fa', 'ፉ': 'fu', 'ፊ': 'fi', 'ፋ': 'fa', 'ፌ': 'fe', 'ፍ': 'fe', 'ፎ': 'fo',
            'ፏ': 'fo',
            'ፐ': 'pa', 'ፑ': 'pu', 'ፒ': 'pi', 'ፓ': 'pa', 'ፔ': 'pe', 'ፕ': 'pe', 'ፖ': 'po',
            'ፗ': 'po',
            '፠': ':', '፡': ' ', '።': '.', '፣': ',', '፤': ';', '፥': ':', '፦': '?',
            '፧': '?',
            '፨': ':', '፩': '1', '፪': '2', '፫': '3', '፬': '4', '፭': '5', '፮': '6',
            '፯': '7', '፰': '8', '፱': '9', '፲': '10', '፳': '20', '፴': '30', '፵': '40',
            '፶': '50', '፷': '60', '፸': '70', '፹': '80', '፺': '90', '፻': '100',
            '፼': '10000',
        }
        
        result = []
        for char in amharic_text:
            if char in transliteration_map:
                result.append(transliteration_map[char])
            elif self._is_amharic_char(char):
                result.append(f"[{hex(ord(char))}]")
            else:
                result.append(char)
                
        return ''.join(result)
    
    def extract_location(self, text: str) -> Optional[str]:
        """
        Extract location from Amharic or English text.
        Enhanced with more specific patterns and anchor keywords.
        
        Args:
            text: Input text containing location information
            
        Returns:
            Location string or None
        """
        if not text:
            return None

        # 1. Anchored patterns (High confidence)
        anchors = [
            r'located?\s+(?:in|at)', r'address', r'sub\s*city', r'zone', r'area',
            r'አድራሻ', r'ቦታ', r'ክፍለ ከተማ', r'ሰፈር', r'የሚገኝበት'
        ]
        for anchor in anchors:
            match = re.search(rf'{anchor}[:\s\-\x16\x17\x18]*([^\n,]+)', text, re.IGNORECASE)
            if match:
                loc_candidate = match.group(1).strip()
                if len(loc_candidate) > 2:
                    return loc_candidate

        # 2. Keyword-based matching
        matches = []
        for location in LOCATION_KEYWORDS:
            loc_clean = location.strip()
            if loc_clean.lower() in text.lower():
                matches.append(loc_clean)
        
        if matches:
            # Prefer more specific locations over general ones like "Addis Ababa"
            general_terms = ["addis ababa", "addis", "አዲስ አበባ", "አዲስ", "ethiopia", "ኢትዮጵያ"]
            specific_matches = [m for m in matches if m.lower() not in general_terms]
            
            if specific_matches:
                return sorted(specific_matches, key=len, reverse=True)[0]
            return sorted(matches, key=len, reverse=True)[0]
                
        # 3. Structural patterns (Fallbacks)
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*(?:Addis\s+Ababa|Kaliti|Kality|Bole|Piassa|Yeka|Kirkos|Arada))',
            r'([^\n,]+)(?:ሚካኤል|አትላስ|አደባባይ|ሕንፃ)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
                
        return None
    
    def extract_numbers(self, text: str) -> List[float]:
        """
        Extract numeric values from text, including Amharic numerals.
        
        Args:
            text: Input text
            
        Returns:
            List of numeric values
        """
        numbers = []
        
        amharic_numerals = {
            '፩': 1, '፪': 2, '፫': 3, '፬': 4, '፭': 5, '፮': 6, '፯': 7, '፰': 8, '፱': 9,
            '፲': 10, '፳': 20, '፴': 30, '፵': 40, '፶': 50, '፷': 60, '፸': 70, '፹': 80,
            '፺': 90, '፻': 100, '፼': 10000
        }
        
        english_nums = re.findall(r'[\d,]+\.?\d*', text)
        for num in english_nums:
            try:
                numbers.append(float(num.replace(',', '')))
            except ValueError:
                continue
                
        amharic_nums = re.findall(r'[' + ''.join(amharic_numerals.keys()) + ']+', text)
        for num in amharic_nums:
            total = 0
            for char in num:
                if char in amharic_numerals:
                    total += amharic_numerals[char]
            if total > 0:
                numbers.append(float(total))
                
        return numbers

    def is_property_listing(self, text: str) -> bool:
        """
        Check if the text likely contains a property listing based on keywords.
        """
        if not text:
            return False
        
        normalized_text = self.normalize_text(text).lower()
        for keyword in PROPERTY_KEYWORDS:
            if self.normalize_text(keyword).lower() in normalized_text:
                return True
        return False
