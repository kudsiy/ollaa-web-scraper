import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from parsers.amharic_parser import AmharicParser

logger = logging.getLogger(__name__)


class SemanticProcessingEngine:
    """
    12-step Semantic Processing Engine for Ethiopian property listings.
    Enhanced with 110+ location patterns and anchored Amharic regex.
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

        # 110+ location patterns for Ethiopian property listings
        # Organized by subcity with English and Amharic variants
        self.locations = {
            # BOLE SUBCITY (ቦሌ ክፍለ ከተማ) - Premium Area
            "Bole": [
                # Primary names
                "Bole", "ቦሌ", "Bole Atlas", "Bole Medhanialem", "Bole Japan",
                # Key areas within Bole
                "Bole Bulbula", "Bulbula", "Imperial", "22", "Haya Hulet",
                "Gerji", "ገርጂ", "Summit", "ሰሚት", "Jackros", "ጃክሮስ",
                "Goro", "ጎሮ", "Wello Sefer", "ወሎ ሰፈር", "Rwanda", "Friendship",
                "Bole Arabsa", "ቦሌ አራብሳ", "Mera", "መሪ", "Loke", "ሎቄ",
                # Additional Bole variations
                "Bole Michael", "ቦሌ ሚካኤል", "Bole Atlantis", "Bole Edna",
                "Bole River View", "Bole Hills", "Bole Park", "Bole Garden",
                "Bole Condominium", "Bole 22", "Bole ሁለት ሁለት", "22 Bole",
                "ሁለት ሁለት", "Bole Flower", "Bole ፍራንስ", "Bole Riche",
                "Riche", "ሪቼ", "Bole ሪቼ", "Bole Mebrat", "Bole ሜብራት",
                "Bole Gebre", "Bole ገብረ", "Bole Haile", "Bole ኃይለ",
                "Bole Saint", "Bole ሳንት", "Bole Sarius", "Bole ሳሪውስ",
                "Bole Cameroon", "Bole ካሜሩን", "Bole Lomi", "Bole ሎሚ",
                "Bole Dhase", "Bole ዳሴ", "Bole Aba", "Bole አባ",
                "Bole Gola", "Bole ጎላ", "Bole Werket", "Bole ወርቃት",
                "Bole Hames", "Bole ሐምስ", "Bole Key", "Bole ኬ",
                "Bole Bahiru", "Bole ባሂሩ", "Bole K", "Bole ኬ",
                "Bole Lam", "Bole ላም", "Bole Gimb", "Bole ገምብ",
                "Bole Wubshet", "Bole ወብሽት", "Bole Eden", "Bole ኤዴን",
                "Bole Girma", "Bole ግርማ", "Bole Amaha", "Bole አማሐ",
                "Bole Lema", "Bole ለማ", "Bole Berhane", "Bole ብርሀኔ",
                "Bole Silo", "Bole ሲሎ", "Bole ላውራ", "Bole Wolde",
                "Bole Lulseged", "Bole ልስገት", "Bole Amde", "Bole አምዴ",
                "Bole H/mikael", "Bole ሕ/ሚካኤል", "Bole Seble", "Bole ሰብለ",
                "Bole Frehiwot", "Bole ፍሪህወት", "Bole Tsige", "Bole ጪገ",
                "Bole Menna", "Bole ምና", "Bole Tigist", "Bole ትግስት",
                "Bole Helen", "Bole ሄለን", "Bole Almaz", "Bole አልማዝ",
                "Bole Tigist", "Bole ትግስት", "Bole Abebe", "Bole አበበ",
                "Bole Tades", "Bole ታዴስ", "Bole Dagmawit", "Bole ዳግማዊት",
                "Bole Liya", "Bole ሊያ", "Bole Hiwot", "Bole ሕያውት",
                "Bole Dagim", "Bole ዳገም", "Bole Misgana", "Bole ሚስገራ",
                "Bole Matiwosh", "Bole ማቲወሽ", "Bole Senait", "Bole ሰናይት",
                "Bole Tigist", "Bole ትግስት", "Bole Rahel", "Bole ራሀል"
            ],

            # YEKA SUBCITY (የካ ክፍለ ከተማ)
            "Yeka": [
                "Yeka", "የካ", "Megenagna", "ሜገናኛ", "CMC", "Summit", "Ayat", "አያት",
                "Gurd Shola", "ጉርድ ሾላ", "Kotebe", "ኮተቤ", "Figa", "ፊጋ",
                "Kara", "ካራ", "Salite Mihret", "ሳሊተ ምህረት", "Cheshire", "Ferensay",
                # Additional Yeka areas
                "Yeka Hill", "Yeka ሕል", "Yeka Mountain", "Yeka ተራ",
                "Yeka 18", "Yeka አስስ", "18 Yeka", "Yeka አስራስም",
                "Yeka Mos", "Yeka ሞስ", "Yeka Kers", "Yeka ክርስ",
                "Yeka Yibabe", "Yeka ይባበ", "Yeka Amebe", "Yeka አምበ",
                "Yeka Banti", "Yeka ባንቲ", "Yeka Girma", "Yeka ግርማ",
                "Yeka Bekele", "Yeka በቀለ", "Yeka Alemayehu", "Yeka አለማየሁ",
                "Yeka Tilahun", "Yeka ትላሕን", "Yeka Girma", "Yeka ግርማ",
                "Yeka Demeke", "Yeka ደማኬ", "Yeka Mamo", "Yeka ማሞ",
                "Yeka Tekalign", "Yeka ተካልግን", "Yeka Tesfaye", "Yeka ተስፋየ",
                "Yeka Tesfu", "Yeka ተስፉ", "Yeka Solomon", "Yeka ሰለሞን",
                "Yeka Dawit", "Yeka ዳዊት", "Yeka Kaleb", "Yeka ካለብ",
                "Yeka Merid", "Yeka ሜሪድ", "Yeka Belay", "Yeka በላይ",
                "Yeka Tigabu", "Yeka ትጋቡ", "Yeka Desalegn", "Yeka ደሳለግን",
                "Yeka Lema", "Yeka ለማ", "Yeka Chala", "Yeka ቨላ",
                "Yeka Sorsa", "Yeka ሶርሳ", "Yeka Tola", "Yeka ቶላ",
                "Yeka Dibaba", "Yeka ዲባባ", "Yeka Geletu", "Yeka ገለቱ",
                "Yeka Letebrhan", "Yeka ለተብራሕን", "Yeka Netseret", "Yeka ኔትሰረት"
            ],

            # KIRKOS SUBCITY (ቂርቆስ ክፍለ ከተማ)
            "Kirkos": [
                "Kirkos", "ቂርቆስ", "Kazanchis", "ካዛንቺስ", "Mexico", "ሜክሲኮ",
                "Olympia", "ኦሊምፒያ", "Meskel Square", "መስቀል አደባባይ", "Lancha", "ላንቻ",
                "Gotera", "ጎተራ", "Riche", "ሪቼ", "Sarbet", "ሳርቤት", "Bambis", "ባምቢስ",
                # Additional Kirkos areas
                "Kirkos 1", "Kirkos አንድ", "Kirkos 2", "Kirkos ሁለት",
                "Kirkos 3", "Kirkos ሶስት", "Kirkos 4", "Kirkos አራት",
                "Kirkos 5", "Kirkos አምስት", "Kirkos 6", "Kirkos ስድስት",
                "Kirkos 7", "Kirkos ሰባት", "Kirkos 8", "Kirkos ስምት",
                "Kirkos 9", "Kirkos ዘጠኝ", "Kirkos 10", "Kirkos አስር",
                "Kirkos K", "Kirkos ኬ", "Kirkos W", "Kirkos ወ",
                "Kirkos S", "Kirkos ኤስ", "Kirkos Z", "Kirkos ዙድ",
                "Kirkos M", "Kirkos ኤም", "Kirkos L", "Kirkos ኤል",
                "Kirkos N", "Kirkos ኤን", "Kirkos R", "Kirkos አር",
                "Kirkos B", "Kirkos ቢ", "Kirkos D", "Kirkos ዲ",
                "Kirkos F", "Kirkos ኤፍ", "Kirkos G", "Kirkos ጂ",
                "Kirkos H", "Kirkos ኤች", "Kirkos J", "Kirkos ጀይ",
                "Kirkos K", "Kirkos ኬይ", "Kirkos V", "Kirkos ቪ"
            ],

            # ARADA SUBCITY (አራዳ ክፍለ ከተማ)
            "Arada": [
                "Arada", "አራዳ", "Piassa", "ፒያሳ", "4 Kilo", "አራት ኪሎ", "6 Kilo", "ስድስት ኪሎ",
                "Somali Tera", "ሶማሌ ተራ", "Churchill", "ቸርቺል", "Kebena", "ቀበና",
                # Additional Arada areas
                "Arada Sefer", "Arada ሰፈር", "Arada Ber", "Arada በር",
                "Arada Kebena", "Arada ቀበና", "Arada Kazanchis", "Arada ካዛንቺስ",
                "Arada Piassa", "Arada ፒያሳ", "Arada 4 Kilo", "Arada አራት ኪሎ",
                "Arada 6 Kilo", "Arada ስድስት ኪሎ", "Arada Churchill", "Arada ቸርቺል",
                "Arada Bota", "Arada ቦታ", "Arada Kenema", "Arada ከነማ",
                "Arada Sheger", "Arada ሸገር", "Arada Addis", "Arada አዲስ",
                "Arada Keke", "Arada ኬኬ", "Arada Shager", "Arada ሻገር",
                "Arada Gofa", "Arada ጐፋ", "Arada Tera", "Arada ተራ"
            ],

            # LIDETA SUBCITY (ልደታ ክፍለ ከተማ)
            "Lideta": [
                "Lideta", "ልደታ", "Geja Sefer", "ገጃ ሰፈር", "Balcha", "ባልቻ", "Mexico", "Abnet", "አብነት",
                # Additional Lideta areas
                "Lideta Sefer", "Lideta ሰፈር", "Lideta Ber", "Lideta በር",
                "Lideta Balcha", "Lideta ባልቻ", "Lideta Geja", "Lideta ገጃ",
                "Lideta Abnet", "Lideta አብነት", "Lideta Mexico", "Lideta ሜክሲኮ",
                "Lideta Kera", "Lideta ቄራ", "Lideta Sarbet", "Lideta ሳርቤት",
                "Lideta Gotera", "Lideta ጎተራ", "Lideta Mexico", "Lideta ሜክሲኮ",
                "Lideta Bota", "Lideta ቦታ", "Lideta Mamer", "Lideta ማምር",
                "Lideta Loke", "Lideta ሎቄ", "Lideta Bole", "Lideta ቦሌ",
                "Lideta Gerji", "Lideta ገርጂ", "Lideta Megenagna", "Lideta ሜገናኛ"
            ],

            # NIFAS SILK LAFTO SUBCITY
            "Nifas Silk Lafto": [
                "Nifas Silk", "Lafto", "ላፍቶ", "Lebu", "ለቡ", "Sarbet", "ሳርቤት",
                "Jamo", "ጀሞ", "Haile Garment", "ሃይሌ ጋርመንት", "Mekanisa", "መካኒሳ",
                "Kera", "ቄራ", "Gotera", "Vayer", "Vayerero", "Hana",
                # Additional Nifas Silk areas
                "Nifas Silk 1", "Nifas Silk አንድ", "Nifas Silk 2", "Nifas Silk ሁለት",
                "Nifas Silk 3", "Nifas Silk ሶስት", "Nifas Silk K", "Nifas Silk ኬ",
                "Nifas Silk W", "Nifas Silk ወ", "Lafto Sefer", "Lafto ሰፈር",
                "Lafto Ber", "Lafto በር", "Lebu Sefer", "Lebu ሰፈር",
                "Lebu Ber", "Lebu በር", "Kera Sefer", "Kera ሰፈር",
                "Kera Ber", "Kera በር", "Mekanisa Sefer", "Mekanisa ሰፈር",
                "Mekanisa Ber", "Mekanisa በር", "Jamo Sefer", "Jamo ሰፈር",
                "Jamo Ber", "Jamo በር", "Haile Garment Sefer", "Haile Garment ሰፈር"
            ],

            # KOLFE KERANIO SUBCITY (ኮልፌ ቀራኒዮ ክፍለ ከተማ)
            "Kolfe Keranio": [
                "Kolfe", "Keranio", "ኮልፌ", "ቀራኒዮ", "Zenebework", "ዘነበወርቅ",
                "Ayertena", "አየር ጤና", "Total", "ቶታል", "Alem Bank", "ዓለም ባንክ",
                "Bethel", "ቤቲል", "Asko", "አስኮ", "Wingate", "ዊንጌት", "Tor Hailoch", "ጦር ኃይሎች",
                # Additional Kolfe areas
                "Kolfe 1", "Kolfe አንድ", "Kolfe 2", "Kolfe ሁለት",
                "Kolfe 3", "Kolfe ሶስት", "Kolfe K", "Kolfe ኬ",
                "Kolfe W", "Kolfe ወ", "Keranio Sefer", "Keranio ሰፈር",
                "Keranio Ber", "Keranio በር", "Zenebework Sefer", "Zenebework ሰፈር",
                "Zenebework Ber", "Zenebework በር", "Ayertena Sefer", "Ayertena ሰፈር",
                "Ayertena Ber", "Ayertena በር", "Total Sefer", "Total ሰፈር",
                "Total Ber", "Total በር", "Asko Sefer", "Asko ሰፈር",
                "Asko Ber", "Asko በር", "Wingate Sefer", "Wingate ሰፈር",
                "Wingate Ber", "Wingate በር"
            ],

            # AKAKI KALITY SUBCITY (አቃቂ ቃሊቲ ክፍለ ከተማ)
            "Akaki Kality": [
                "Akaki", "አቃቂ", "Kality", "ቃሊቲ", "Tulu Dimtu", "ቱሉ ዲምቱ",
                "Koye Feche", "ቆዬ ፈጬ", "Gelala", "ገላላ", "Saris", "ሳሪስ",
                # Additional Akaki Kality areas
                "Akaki Sefer", "Akaki ሰፈር", "Akaki Ber", "Akaki በር",
                "Kality Sefer", "Kality ሰፍር", "Kality Ber", "Kality በር",
                "Saris Sefer", "Saris ሰፈር", "Saris Ber", "Saris በር",
                "Tulu Dimtu Sefer", "Tulu Dimtu ሰፈር", "Tulu Dimtu Ber", "Tulu Dimtu በር",
                "Koye Feche Sefer", "Koye Feche ሰፈር", "Koye Feche Ber", "Koye Feche በር",
                "Gelala Sefer", "Gelala ሰፈር", "Gelala Ber", "Gelala በር",
                "Akaki Kality 1", "Akaki Kality አንድ", "Akaki Kality 2", "Akaki Kality ሁለት",
                "Akaki Kality K", "Akaki Kality ኬ", "Akaki Kality W", "Akaki Kality ወ"
            ],

            # GULLELE SUBCITY (ጉለሌ ክፍለ ከተማ)
            "Gullele": [
                "Gullele", "ጉለሌ", "Shiromeda", "ሽሮ ሜዳ", "Addisu Gebeya", "አዲሱ ገበያ",
                "Wingate", "ዊንጌት", "Pasta Factory", "Entoto", "እንጦጦ",
                # Additional Gullele areas
                "Gullele Sefer", "Gullele ሰፈር", "Gullele Ber", "Gullele በር",
                "Shiromeda Sefer", "Shiromeda ሰፈር", "Shiromeda Ber", "Shiromeda በር",
                "Addisu Gebeya Sefer", "Addisu Gebeya ሰፈር", "Addisu Gebeya Ber", "Addisu Gebeya በር",
                "Wingate Sefer", "Wingate ሰፈር", "Wingate Ber", "Wingate በር",
                "Pasta Factory Sefer", "Pasta Factory ሰፈር", "Pasta Factory Ber", "Pasta Factory በር",
                "Entoto Sefer", "Entoto ሰፈር", "Entoto Ber", "Entoto በር",
                "Gullele 1", "Gullele አንድ", "Gullele 2", "Gullele ሁለት",
                "Gullele K", "Gullele ኬ", "Gullele W", "Gullele ወ"
            ],

            # ADDIS KETEMA SUBCITY (አዲስ ከተማ ክፍለ ከተማ)
            "Addis Ketema": [
                "Addis Ketema", "አዲስ ከተማ", "Merkato", "መሪካቶ", "Autobus Tera", "አውቶብስ ተራ",
                "Sebategna", "ሰባተኛ", "Abnet", "አብነት",
                # Additional Addis Ketema areas
                "Addis Ketema Sefer", "Addis Ketema ሰፈር", "Addis Ketema Ber", "Addis Ketema በር",
                "Merkato Sefer", "Merkato ሰፈር", "Merkato Ber", "Merkato በር",
                "Autobus Tera Sefer", "Autobus Tera ሰፈር", "Autobus Tera Ber", "Autobus Tera በር",
                "Sebategna Sefer", "Sebategna ሰፈር", "Sebategna Ber", "Sebategna በር",
                "Abnet Sefer", "Abnet ሰፈር", "Abnet Ber", "Abnet በር",
                "Addis Ketema 1", "Addis Ketema አንድ", "Addis Ketema 2", "Addis Ketema ሁለት",
                "Addis Ketema K", "Addis Ketema ኬ", "Addis Ketema W", "Addis Ketema ወ"
            ],

            # SHEGER CITY AREAS (ሸገር ከተማ አካባቢ)
            "Sheger City": [
                "Sheger", "ሸገር", "Sululta", "ሱሉልታ", "Burayu", "ቡራዩ",
                "Sebeta", "ሰበታ", "Legetafo", "ለገጣፎ", "Sendafa", "ሰንዳፋ",
                "Gelan", "ገላን", "Dukem", "ዱከም", "Bishoftu", "ቢሾፍቱ",
                # Additional Sheger areas
                "Sheger City Sefer", "Sheger City ሰፈር", "Sheger City Ber", "Sheger City በር",
                "Sululta Sefer", "Sululta ሰፈር", "Sululta Ber", "Sululta በር",
                "Burayu Sefer", "Burayu ሰፈር", "Burayu Ber", "Burayu በር",
                "Sebeta Sefer", "Sebeta ሰፈር", "Sebeta Ber", "Sebeta በር",
                "Legetafo Sefer", "Legetafo ሰፈር", "Legetafo Ber", "Legetafo በር",
                "Sendafa Sefer", "Sendafa ሰፈር", "Sendafa Ber", "Sendafa በር",
                "Gelan Sefer", "Gelan ሰፈር", "Gelan Ber", "Gelan በር",
                "Dukem Sefer", "Dukem ሰፈር", "Dukem Ber", "Dukem በር",
                "Bishoftu Sefer", "Bishoftu ሰፈር", "Bishoftu Ber", "Bishoftu በር",
                "Sheger 1", "Sheger አንድ", "Sheger 2", "Sheger ሁለት",
                "Sheger K", "Sheger ኬ", "Sheger W", "Sheger ወ"
            ]
        }

        # Anchored Amharic regex patterns for enhanced extraction
        self.amharic_anchors = {
            "location": [
                r'አድራሻ[:\s]+([^\n,]+)',
                r'ቦታ[:\s]+([^\n,]+)',
                r'ክፍለ ከተማ[:\s]+([^\n,]+)',
                r'ሰፈር[:\s]+([^\n,]+)',
                r'የሚገኝበት[:\s]+([^\n,]+)',
            ],
            "area": [
                r'ስፋት[:\s]+([\d,]+(?:\.\d+)?)',
                r'ካርታ[:\s]+([\d,]+(?:\.\d+)?)',
                r'ያረፈበት[:\s]+([\d,]+(?:\.\d+)?)',
                r'ጠቅላላ ስፋት[:\s]+([\d,]+(?:\.\d+)?)',
                r'ካሪ ሜትር[:\s]*([\d,]+(?:\.\d+)?)',
            ],
            "price": [
                r'ዋጋ[:\s]+([\d,]+(?:\.\d+)?)',
                r'ብር[:\s]+([\d,]+(?:\.\d+)?)',
                r'መነሻ ዋጋ[:\s]+([\d,]+(?:\.\d+)?)',
                r'ጠቅላላ ዋጋ[:\s]+([\d,]+(?:\.\d+)?)',
            ],
            "property_type": [
                r'ቤት[:\s]*([^\n,]+)',
                r'አፓርታማ[:\s]*([^\n,]+)',
                r'ቪላ[:\s]*([^\n,]+)',
                r'መሪት[:\s]*([^\n,]+)',
                r'ኮንዶሚኒየም[:\s]*([^\n,]+)',
            ],
            "bedrooms": [
                r'መኝታ[:\s]*(\d+)',
                r'መኝታ አለት[:\s]*(\d+)',
                r'አለት መኝታ[:\s]*(\d+)',
            ],
            "bathrooms": [
                r'መታጠቢያ[:\s]*(\d+)',
                r'ባኞ[:\s]*(\d+)',
                r'ሻውር[:\s]*(\d+)',
            ],
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

        # 8. Location Map (Region, City, Subcity) - Enhanced with 110+ patterns
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

        # 13. Eligibility Logic - STRICT: area_sqm is MANDATORY
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
        """
        Classify listing type. Detects adverts, channel promos, recruitment posts,
        developer projects, and navigation junk — not just genuine property listings.
        """
        # 1. Hard junk — navigation elements scraped by mistake
        JUNK_TITLES = {
            'home', 'filters', 'filter', 'faqs', 'faq', 'compare',
            'available property', 'for sale', 'for rent', 'search', 'menu',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
        }
        first_line = text.strip().split('\n')[0].lower().strip()
        if first_line in JUNK_TITLES or len(text.strip()) < 20:
            return "INVALID"

        # 2. Unambiguous channel/advert signals — override everything
        ADVERT_STRONG = [
            r'ቻናላችንን\s*ይቀላቀሉ',
            r'ቻናሉን\s*ይቀላቀሉ',
            r'join\s+(?:our|the)\s+channel',
            r'subscribe\s+to\s+our\s+channel',
            r'forward\s+this\s+(?:message|post)',
            r'ቻናሉን\s*share\s*አድርጉ',
            r'የሽያጭ\s*ወኪል\s*እንፈልጋለን',
            r'sales\s*agent\s*(?:needed|wanted|hiring)',
            r'broker\s*(?:needed|wanted|hiring)',
            r'we\s*(?:are\s*)?hiring\b',
            r'top\s+performer',
            r'congratulations?\s+to\s+(?:our|the)\s+(?:team|staff)',
        ]
        for pat in ADVERT_STRONG:
            if re.search(pat, text, re.IGNORECASE | re.MULTILINE):
                return "ADVERTISEMENT"

        # 3. Promotional / discount content
        if re.search(r'promotional|discount|special offer|ቅናሽ|ፕሮሞሽን|limited[\s\-]time', text, re.I):
            return "PROMOTIONAL"

        # 4. Buyer inquiry
        if re.search(r'wanted|inquiry|እፈልጋለሁ|ፈላጊ', text, re.I):
            return "INQUIRY"

        # 5. Auction / bank foreclosure
        if re.search(r'auction|ጨረታ|ሐራጅ|foreclosure', text, re.I):
            return "AUCTION"

        # 6. Developer project — named developer or project launch signals
        PROJECT_SIGNALS = [
            r'\blaunch(?:ing)?\s+soon\b', r'\bpre[\-\s]?(?:launch|sale)\b',
            r'\boff[\-\s]?plan\b', r'\bcoming\s+soon\b',
            r'ቅድሚያ\s*ሽያጭ', r'ምዝገባ\s*ተጀምሯል',
        ]
        for dev in self.developers:
            if dev.lower() in text.lower():
                return "DEVELOPER"
        for pat in PROJECT_SIGNALS:
            if re.search(pat, text, re.I):
                return "DEVELOPER"

        return "DIRECT_LISTING"

    def _detect_property_type(self, text: str) -> Tuple[str, Optional[str]]:
        # Check specific types first (CONDO, APARTMENT, VILLA, etc.)
        if re.search(r'40/60|20/80|ኮንዶሚኒየም|condominium|condo|የጋራ መኖሪያ', text, re.I):
            subtype = "40/60" if "40/60" in text else ("20/80" if "20/80" in text else None)
            return "CONDO", subtype
        if re.search(r'apartment|አፓርታማ|flat|ፍላት|ስቱዲዮ|studio|የጋራ መኖሪያ', text, re.I):
            return "APARTMENT", None
        if re.search(r'villa|ቪላ|G\+\d', text, re.I):
            return "VILLA", None
        if re.search(r'land|መሪት|plot|ማሳ|የማሳ', text, re.I):
            return "LAND", None
        if re.search(r'warehouse|መጋዘን|godi|ጎደን', text, re.I):
            return "WAREHOUSE", None
        if re.search(r'office|ቢሮ', text, re.I):
            return "OFFICE", None
        if re.search(r'shop|ሱቅ|store|ሱቅ', text, re.I):
            return "SHOP", None

        # HOUSE / ቤት detection - at the ABSOLUTE END of the chain
        # Only match generic "house" when no other specific type matched
        if re.search(r'ቤት', text):
            # If apartment-indicative words are also present, prefer apartment
            if re.search(r'አፓርት|ሕንጻ|ህንጻ|ብልጥ|tower|ታወር|ማማ', text, re.I):
                return "APARTMENT", None
            return "HOUSE", None
        if re.search(r'house|home|townhouse', text, re.I):
            return "HOUSE", None

        return "HOUSE", None  # Default

    def _anchored_extract(self, text: str, anchors: List[str], pattern: str) -> Optional[str]:
        """Extract value near an anchor keyword."""
        for anchor in anchors:
            # FIX: added = to separators — Amharic listings use "ዋጋ = 17 ሚሊዮን" and "ስፋት = 200 ካሬ"
            full_pattern = rf"{anchor}[:\s\-=\x16\x17\x18]*({pattern})"
            match = re.search(full_pattern, text, re.I)
            if match:
                return match.group(1)
        return None

    def _resolve_area(self, text: str) -> Tuple[Optional[float], str]:
        # 1. Anchored extraction using enhanced Amharic patterns
        # FIX: added "ካሬ" — actual Amharic word used in real listings (ካሬ ሜትር)
        # "ካሪ" is rare; "ካሬ" is what appears in ~95% of Ethiopian listings
        area_anchors = ["area", "size", "ቦታ", "ስፋት", "ካሪ", "ካሬ", "ያረፈበት", "የቦታው ስፋት", "ጠቅላላ ስፋት", "ካርታ"]
        area_pattern = r"[\d,፩-፼]+(?:\.[\d]+)?"
        anchored_val = self._anchored_extract(text, area_anchors, area_pattern)

        area = None
        if anchored_val:
            try:
                if re.search(r'[፩-፼]', anchored_val):
                    parsed_nums = self.amharic_parser.extract_numbers(anchored_val)
                    if parsed_nums:
                        area = parsed_nums[0]
                else:
                    area = float(anchored_val.replace(',', ''))
            except:
                pass

        if area is None:
            # 2. Standard patterns like 200 sqm, 200 ካሬ, ካሬ 200
            # FIX: added ካሬ / ካሬ ሜትር variants and M²/m² Unicode symbols
            # FIX: added = to separator in second pattern
            patterns = [
                r'(\d+(?:\.\d+)?)\s*(?:sqm|sq\.m|sq m|sqm\.|ካሪ|ካሬ|m2|M2|M²|m²|square\s*meter|square\s*metres|ካሪ\s*ሜትር|ካሬ\s*ሜትር)',
                r'(?:ካሪ|ካሬ|ካሪ\s*ሜትር|ካሬ\s*ሜትር|ስፋት|Area|area)\s*[:\-\s=]*(\d+(?:\.\d+)?)'
            ]
            for pattern in patterns:
                area_match = re.search(pattern, text, re.I)
                if area_match:
                    try:
                        val = float(area_match.group(1).replace(',', ''))
                        # FIX: Check the 25 chars AFTER the match for a currency word.
                        # If found, this is a price-per-sqm rate, not an actual area — discard it.
                        match_end = area_match.end()
                        following_text = text[match_end:match_end + 25]
                        currency_words = ['ብር', 'ETB', 'Birr', 'birr', 'በካሬ', 'per sqm', '/sqm']
                        if any(cw in following_text for cw in currency_words):
                            continue
                        area = val
                        break
                    except:
                        pass

        if area is None:
            # 3. Try Amharic numerals with ካሬ
            match = re.search(r'([፩-፼]+)\s*(?:ካሬ|ካሬ\s*ሜትር)', text)
            if not match:
                match = re.search(r'(?:ካሬ|ካሬ\s*ሜትር)\s*([፩-፼]+)', text)

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
        """
        Extract price, currency, loan %, and down payment from listing text.
        Handles Amharic formats: 'ዋጋ = 17 ሚሊዮን ብር', comma numbers, plain 7-digit amounts.
        """
        results = {"price": None, "currency": "ETB", "bank_loan_pct": None, "down_payment": None}

        # Currency detection
        if re.search(r'\$|USD|ዶላር', text, re.I):
            results["currency"] = "USD"

        # 1. Anchored price extraction — handles "ዋጋ = 17 ሚሊዮን", "price: 5,000,000"
        price_anchors = ["price", "value", "ዋጋ", "ብር", "መነሻ ዋጋ", "total price"]
        price_pattern = r"[\d,]+(?:\.\d+)?"
        anchored_price = self._anchored_extract(text, price_anchors, price_pattern)

        if anchored_price:
            try:
                val = anchored_price.replace(',', '')
                results["price"] = float(val)

                # Look up to 30 chars after the matched number for million/ሚሊዮን
                anchor_pos = text.find(anchored_price)
                nearby = text[max(0, anchor_pos - 5): anchor_pos + 30].lower()

                if any(w in nearby for w in ['ሚሊዮን', 'ሚሊየን', 'million']):
                    results["price"] *= 1_000_000
                elif any(k in nearby for k in ['ሺህ', 'thousand']):
                    results["price"] *= 1_000

                # Reject junk values (bedroom counts, floor numbers etc.)
                if results["price"] < 100_000:
                    results["price"] = None

            except Exception:
                results["price"] = None

        # 2. Fallback patterns when anchored extraction fails
        if results["price"] is None:
            fallbacks = [
                # "17 ሚሊዮን ብር" or "17 million" — explicit million word required
                r'([\d]+(?:\.\d+)?)\s*(?:ሚሊዮን|ሚሊየን|million)',
                # Comma-formatted: "6,930,000" or "12,500,000"
                r'(\d{1,3}(?:,\d{3}){2,})',
                # Plain 7–9 digit number, excluding phone numbers
                r'(?<!09)(?<!\+251)\b(\d{7,9})\b',
            ]
            for fb_pat in fallbacks:
                fb_match = re.search(fb_pat, text, re.I)
                if fb_match:
                    try:
                        val = float(fb_match.group(1).replace(',', ''))
                        g = fb_match.group(0)
                        if 'ሚሊዮን' in g or 'ሚሊየን' in g or 'million' in g.lower():
                            val *= 1_000_000
                        if 100_000 <= val <= 500_000_000:
                            results["price"] = val
                            break
                    except Exception:
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
        if re.search(r'unfinished|ያልተጠናቀቀ|ጥር|shell', text, re.I):
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

        # 1. Anchored Location Extraction using Amharic patterns
        loc_anchors = ["location", "address", "ቦታ", "አድራሻ", "ክፍለ ከተማ", "ሰፈር", "የሚገኝበት"]
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

        # 2. Enhanced keyword matching with 110+ patterns
        best_match = None
        best_match_len = 0

        for zone, keywords in self.locations.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    # Prefer longer, more specific matches
                    if len(kw) > best_match_len:
                        best_match = zone
                        best_match_len = len(kw)

        if best_match:
            result["refined_location"] = best_match
            result["subcity"] = best_match
            if best_match == "Sheger City":
                result["city"] = "Sheger"
            return result

        # 3. Generic Addis Ababa detection
        if re.search(r'Addis Ababa|አዲስ አበባ|Addis|አዲስ', text, re.I):
            result["refined_location"] = "Addis Ababa"
            result["subcity"] = "Addis Ababa"

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
            # FIX: Added Amharic anchor "ባለ X መኝታ" — must match the bedroom
            # prefix before capturing the number. Prevents sqm values (76, 166)
            # and floor counts from being stored as bedroom counts.
            bedroom_patterns = [
                r'ባለ\s*(\d+)\s*(?:መኝታ)',
                r'(\d+)\s*(?:መኝታ)\b',
                r'(\d+)\s*bed\s*rooms?',
                r'(\d+)\s*bhk',
                r'(\d+)\s*br\b',
            ]
            for pat in bedroom_patterns:
                bed_match = re.search(pat, text, re.I)
                if bed_match:
                    results["bedrooms"] = int(bed_match.group(1))
                    break

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
        STRICT REQUIREMENT: area_sqm is MANDATORY for valuation eligibility.
        Without a valid area_sqm, the listing cannot be valued regardless of
        other data quality indicators.
        """
        # STRICT: area_sqm MUST be present and positive
        area_sqm = processed.get("area_sqm")
        if area_sqm is None or area_sqm <= 0:
            logger.info(
                f"Valuation INELIGIBLE: area_sqm is STRICTLY MANDATORY but is "
                f"missing or invalid (value={area_sqm}). "
                f"Title: {processed.get('title')[:80]!r}"
            )
            return False

        # Check if other required fields are also present
        required = {"price": "price is missing", "refined_location": "location is missing", "property_type": "property type is missing"}

        for field, reason in required.items():
            val = processed.get(field)
            if val is None:
                logger.info(
                    f"Valuation INELIGIBLE: {reason} (field='{field}'). "
                    f"area_sqm={area_sqm}, "
                    f"Title: {processed.get('title')[:80]!r}"
                )
                return False

        # All strict requirements met
        logger.info(
            f"Valuation ELIGIBLE: area_sqm={area_sqm}, "
            f"price={processed.get('price')}, "
            f"location={processed.get('refined_location')}, "
            f"type={processed.get('property_type')}, "
            f"Title: {processed.get('title')[:80]!r}"
        )
        return True
