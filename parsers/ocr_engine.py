"""
OCR engine for extracting text from images and scanned PDF documents.
Supports Ethiopian context by integrating with Tesseract OCR.
"""
import logging
import io
from typing import Optional, List
import PIL.Image

logger = logging.getLogger(__name__)

class OCREngine:
    """
    OCR Engine to handle scanned notices and image-based property listings.
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        try:
            import pytesseract
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        except ImportError:
            logger.warning("pytesseract not installed. OCR will not be available.")
            
    def extract_from_image(self, image_bytes: bytes, lang: str = "eng+amh") -> str:
        """
        Extract text from image bytes.
        
        Args:
            image_bytes: Raw bytes of the image
            lang: Tesseract language codes (default: English + Amharic)
            
        Returns:
            Extracted text
        """
        try:
            import pytesseract
            image = PIL.Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image, lang=lang)
            return text
        except ImportError:
            logger.error("pytesseract not installed.")
            return ""
        except Exception as e:
            logger.error(f"OCR Error: {e}")
            return ""
            
    def extract_from_pdf(self, pdf_bytes: bytes, lang: str = "eng+amh") -> str:
        """
        Convert scanned PDF pages to images and perform OCR.
        
        Args:
            pdf_bytes: Raw bytes of the PDF
            lang: Tesseract language codes
            
        Returns:
            Extracted text from all pages
        """
        try:
            from pdf2image import convert_from_bytes
            import pytesseract
            images = convert_from_bytes(pdf_bytes)
            full_text = []
            for i, image in enumerate(images):
                logger.info(f"Processing PDF page {i+1}/{len(images)}")
                text = pytesseract.image_to_string(image, lang=lang)
                full_text.append(text)
            return "\n\n".join(full_text)
        except ImportError as e:
            logger.error(f"Missing dependency for PDF OCR: {e}")
            return ""
        except Exception as e:
            logger.error(f"PDF OCR Error: {e}")
            return ""

    def is_scanned_pdf(self, pdf_bytes: bytes) -> bool:
        """
        Check if a PDF is likely scanned (contains little to no text).
        """
        import pdfplumber
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                total_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        total_text += text
                
                # If less than 100 characters in the whole doc, it's likely scanned
                return len(total_text.strip()) < 100
        except Exception:
            return True
