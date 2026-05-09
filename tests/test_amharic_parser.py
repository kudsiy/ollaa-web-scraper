import pytest
from parsers.amharic_parser import AmharicParser

def test_detect_script():
    parser = AmharicParser()
    assert parser.detect_script("አዲስ አበባ") == "amharic"
    assert parser.detect_script("Addis Ababa") == "english"
    assert parser.detect_script("Addis Ababa አዲስ አበባ") == "mixed"

def test_transliterate_to_english():
    parser = AmharicParser()
    # ሀ -> ha, ለ -> la (wait, check map)
    # Map says 'ሀ': 'ha'
    # Wait, my test is guessing 'ለ'
    # Let's check the map in amharic_parser.py
    # 'ሰ': 'sa'
    assert parser.transliterate_to_english("ሀሰ") == "hasa"

def test_extract_location():
    parser = AmharicParser()
    assert parser.extract_location("The house is in Bole") == "Bole"
    assert parser.extract_location("አፓርትመንት ቦሌ") == "ቦሌ"

def test_extract_numbers():
    parser = AmharicParser()
    assert 5.0 in parser.extract_numbers("5 rooms")
    # ፭ is 5
    assert 5.0 in parser.extract_numbers("፭")
