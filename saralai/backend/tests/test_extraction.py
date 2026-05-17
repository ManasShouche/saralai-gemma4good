"""Tests for document field extraction accuracy."""

import json
import pytest


# Test fixtures: expected outputs for known Aadhaar images
RUKMINI_EXPECTED = {
    "name": "Rukmini Devi",
    "dob": "1973-04-15",
    "gender": "F",
    "district": "Tumkur",
    "state": "Karnataka",
}

SURESH_EXPECTED = {
    "name": "Suresh Kumar",
    "dob": "1980-11-22",
    "gender": "M",
    "district": "Bengaluru Rural",
    "state": "Karnataka",
}


def test_aadhaar_field_accuracy():
    """Extracted fields should match expected output for known test images.

    Acceptance criteria: >=80% field accuracy (4 out of 5 core fields).
    """
    # This test requires Ollama + Gemma 4 running with test images
    # Placeholder: will be filled during integration testing
    pass


def test_aadhaar_masking():
    """Aadhaar numbers should always be masked to last 4 digits."""
    from ollama_client import mask_aadhaar

    assert mask_aadhaar("1234 5678 9012") == "XXXX XXXX 9012"
    assert mask_aadhaar("123456789012") == "XXXX XXXX 9012"
    assert mask_aadhaar("no number here") == "no number here"


def test_aadhaar_dict_masking():
    """Aadhaar masking should work recursively in dictionaries."""
    from ollama_client import mask_aadhaar_in_dict

    data = {
        "name": "Test User",
        "aadhaar_number": "1234 5678 9012",
        "nested": {
            "aadhaar_ref": "9876 5432 1098",
        },
    }
    masked = mask_aadhaar_in_dict(data)
    assert masked["aadhaar_number"] == "XXXX XXXX 9012"
    assert masked["nested"]["aadhaar_ref"] == "XXXX XXXX 1098"
    assert masked["name"] == "Test User"


def test_ration_card_categories():
    """Ration card extraction should produce valid category values."""
    valid_categories = {"APL", "BPL", "AAY", "PHH"}
    # Placeholder for integration test with real images
    pass
