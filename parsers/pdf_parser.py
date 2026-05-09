"""
PDF parser for extracting property information from auction notices.
Uses pdfplumber for text extraction and layout preservation.
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

import pdfplumber
from pdfplumber.utils import get_bbox_overlap, extract_words

from config import get_config
from parsers.ocr_engine import OCREngine


logger = logging.getLogger(__name__)


class PDFParser:
    """
    Parser for extracting structured data from PDF auction notices.
    Handles both English and Amharic text with layout analysis.
    """
    
    def __init__(self):
        self.config = get_config()
        self.ocr_engine = OCREngine()
        
    def parse_file(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse a PDF file and extract property information.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted data
        """
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        return self.parse_bytes(pdf_bytes)
    
    def parse_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Parse PDF from bytes (for downloaded content).
        
        Args:
            pdf_bytes: PDF content as bytes
            
        Returns:
            Dictionary containing extracted data
        """
        data = {
            "pages": [],
            "full_text": "",
            "tables": [],
            "property_info": {},
            "extracted_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Check if OCR is needed
            if self.ocr_engine.is_scanned_pdf(pdf_bytes):
                logger.info("PDF appears to be scanned, using OCR fallback")
                data["full_text"] = self.ocr_engine.extract_from_pdf(pdf_bytes)
                data["is_ocr"] = True
            else:
                import io
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    data["page_count"] = len(pdf.pages)
                    
                    for page_num, page in enumerate(pdf.pages):
                        page_data = self._parse_page(page, page_num)
                        data["pages"].append(page_data)
                        data["full_text"] += page_data["text"] + "\n\n"
                        
                        if page_data["tables"]:
                            data["tables"].extend(page_data["tables"])
            
            data["property_info"] = self._extract_property_info(data["full_text"])
                
        except Exception as e:
            logger.error(f"Error parsing PDF from bytes: {e}")
            data["error"] = str(e)
            
        return data
    
    def _parse_page(self, page, page_num: int) -> Dict[str, Any]:
        """Parse a single PDF page."""
        page_data = {
            "page_num": page_num + 1,
            "text": page.extract_text() or "",
            "tables": [],
            "dimensions": {"width": page.width, "height": page.height}
        }
        
        tables = page.extract_tables()
        for table in tables:
            if table:
                page_data["tables"].append(table)
                
        return page_data
    
    def _extract_property_info(self, text: str) -> Dict[str, Any]:
        """
        Extract structured property information from PDF text.
        
        Args:
            text: Full text extracted from PDF
            
        Returns:
            Dictionary with extracted property fields
        """
        from parsers.price_extractor import PriceExtractor
        price_extractor = PriceExtractor()
        
        info = {}
        
        patterns = {
            "price": [
                r"(?:starting\s+price|starting\s+bid|initial\s+bid|reserve\s+price)[:\s]*[Eé]T[B]?\s*([\d,]+(?:\.\d{2})?)",
                r"[Eé]T[B]?\s*([\d,]+(?:\.\d{2})?)\s*(?:million|mio|m)",
                r"([\d,]+(?:\.\d{2})?)\s*(?:million\s*)?[Eé]T[B]?"
            ],
            "area": [
                r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:sq\.?\s*m\.?|square\s*meters?|m²|sq\s*metres?)",
                r"area[:\s]*(\d+(?:,\d{3})*(?:\.\d+)?)"
            ],
            "bedrooms": [
                r"(\d+)\s*(?:bed(?:room)?s?|br)",
                r"bedrooms?[:\s]*(\d+)"
            ],
            "bathrooms": [
                r"(\d+)\s*(?:bath(?:room)?s?|ba)",
                r"bathrooms?[:\s]*(\d+)"
            ],
            "location": [
                r"(?:location|address|situate[sd]?)[:\s]*([^\n]+)",
                r"(?:in\s+the\s+(?:city|area|zone|sub\s*city))[:\s]*([^\n]+)"
            ]
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.lastindex else match.group(0)
                    if field == "price":
                        info[field] = price_extractor.extract(value)
                    elif field in ("bedrooms", "bathrooms", "area"):
                        try:
                            clean_value = value.replace(",", "")
                            info[field] = int(clean_value) if "." not in value else float(clean_value)
                        except ValueError:
                            info[field] = value
                    else:
                        info[field] = value.strip()
                    break
        
        property_types = ["apartment", "house", "villa", "office", "store", "warehouse", "land", "plot", "building"]
        for prop_type in property_types:
            if re.search(prop_type, text, re.IGNORECASE):
                info["property_type"] = prop_type
                break
        
        dates = [
            (r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})", "%d/%m/%Y"),
            (r"(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})", "%Y/%m/%d"),
            (r"(\d{1,2})\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})", "%d %b %Y")
        ]
        for date_pattern, date_format in dates:
            match = re.search(date_pattern, text, re.IGNORECASE)
            if match:
                try:
                    info["auction_date"] = datetime.strptime(
                        match.group(0), date_format
                    ).isoformat()
                    break
                except ValueError:
                    continue
        
        return info
    
    def extract_links(self, pdf_path: str, base_url: str) -> List[Dict[str, str]]:
        """
        Extract hyperlinks from PDF auction notice.
        
        Args:
            pdf_path: Path to PDF file
            base_url: Base URL for resolving relative links
            
        Returns:
            List of dicts with link text and URL
        """
        links = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    annots = page.annots or []
                    for annot in annots:
                        if annot.get("annotation_type") == "link":
                            uri = annot.get("uri", "")
                            if uri:
                                links.append({
                                    "url": uri,
                                    "page": page.page_number
                                })
        except Exception as e:
            logger.error(f"Error extracting links from PDF: {e}")
            
        return links
    
    def is_valid_pdf(self, pdf_path: str) -> bool:
        """Check if a file is a valid PDF."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages) > 0
        except Exception:
            return False