import pytest
from parsers.price_extractor import PriceExtractor

def test_price_extractor_million():
    extractor = PriceExtractor()
    assert extractor.extract("2.5 million ETB") == 2500000.0
    assert extractor.extract("2.5M") == 2500000.0
    assert extractor.extract("ETB 2.5 million") == 2500000.0
    assert extractor.extract("2.5 ሚሊዮን") == 2500000.0

def test_price_extractor_thousand():
    extractor = PriceExtractor()
    assert extractor.extract("500 thousand ETB") == 500000.0
    assert extractor.extract("500K") == 500000.0
    assert extractor.extract("500 ሺ") == 500000.0

def test_price_extractor_etb():
    extractor = PriceExtractor()
    assert extractor.extract("ETB 500,000.00") == 500000.0
    assert extractor.extract("500,000 ETB") == 500000.0
    assert extractor.extract("ብር 500,000") == 500000.0

def test_price_extractor_numeric():
    extractor = PriceExtractor()
    assert extractor.extract("500,000") == 500000.0
    assert extractor.extract("999") is None  # Below threshold
    assert extractor.extract("1000") == 1000.0
