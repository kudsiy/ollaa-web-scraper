
import pytest
from parsers.semantic_engine import SemanticProcessingEngine

def test_anchored_extraction():
    engine = SemanticProcessingEngine()
    
    # Test area extraction
    text1 = "The property size is 200 sqm and it is located in Bole. Price: 15 million."
    processed1 = engine.process({"title": "Test", "description": text1})
    assert processed1["area_sqm"] == 200.0
    assert processed1["refined_location"] == "Bole"
    assert processed1["valuation_eligible"] == True
    
    # Test price extraction with Amharic anchors
    text2 = "መነሻ ዋጋ: 5,000,000 ብር. ቦታ: የካ"
    processed2 = engine.process({"title": "Test", "description": text2})
    assert processed2["price"] == 5000000.0
    assert processed2["refined_location"] == "Yeka"
    
    # Test price with million multiplier
    text3 = "Price: 2.5 million. Location: CMC"
    processed3 = engine.process({"title": "Test", "description": text3})
    assert processed3["price"] == 2500000.0
    assert processed3["refined_location"] == "Yeka" # CMC is in Yeka
    
    # Test Land special case for eligibility
    text4 = "Land for sale in Gerji. Area: 500. Price: 10M"
    processed4 = engine.process({"title": "Land sale", "description": text4})
    assert processed4["property_type"] == "LAND"
    assert processed4["area_sqm"] == 500.0
    assert processed4["price"] == 10000000.0
    assert processed4["valuation_eligible"] == True

def test_advanced_location_patterns():
    engine = SemanticProcessingEngine()
    
    # Test sub-localities
    text1 = "House in Bole Arabsa"
    processed1 = engine.process({"title": "Test", "description": text1})
    assert processed1["refined_location"] == "Bole"
    
    text2 = "Condo near Tor Hailoch"
    processed2 = engine.process({"title": "Test", "description": text2})
    assert processed2["refined_location"] == "Kolfe Keranio"
    
    text3 = "Apartment in Salite Mihret"
    processed3 = engine.process({"title": "Test", "description": text3})
    assert processed3["refined_location"] == "Yeka"

def test_feature_extraction():
    engine = SemanticProcessingEngine()
    
    text = "4 bedrooms, 3 bathrooms, kitchen and parking."
    processed = engine.process({"title": "Test", "description": text})
    assert processed["bedrooms"] == 4
    assert processed["bathrooms"] == 3
    assert processed["kitchens"] == 1 # Extracted from standard pattern match
    assert processed["parking_spaces"] == 1
