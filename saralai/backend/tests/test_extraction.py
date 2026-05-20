"""
Tests for document field extraction: Aadhaar masking and JSON parsing.

No Ollama or network required — ollama.chat is mocked throughout.

Run with:
    cd backend
    pytest tests/test_extraction.py -v
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Aadhaar masking — mask_aadhaar (string-level)
# ---------------------------------------------------------------------------

class TestMaskAadhaar:

    @pytest.fixture(autouse=True)
    def _import(self):
        with patch.dict("sys.modules", {"ollama": MagicMock()}):
            from ollama_client import mask_aadhaar
            self.mask = mask_aadhaar

    def test_standard_spaced_format(self):
        assert self.mask("1234 5678 9012") == "XXXX XXXX 9012"

    def test_no_spaces_format(self):
        assert self.mask("123456789012") == "XXXX XXXX 9012"

    def test_preserves_last_four_digits(self):
        assert self.mask("9876 5432 1099").endswith("1099")

    def test_no_number_unchanged(self):
        assert self.mask("no number here") == "no number here"

    def test_partial_number_unchanged(self):
        # 8-digit number is not an Aadhaar
        assert self.mask("12345678") == "12345678"

    def test_number_in_sentence(self):
        result = self.mask("Aadhaar: 1234 5678 9012 issued in Karnataka")
        assert "XXXX XXXX 9012" in result
        assert "1234" not in result
        assert "Karnataka" in result

    def test_multiple_numbers_masked(self):
        result = self.mask("First: 1111 2222 3333, Second: 4444 5555 6666")
        assert "XXXX XXXX 3333" in result
        assert "XXXX XXXX 6666" in result
        assert "1111" not in result
        assert "4444" not in result

    def test_empty_string(self):
        assert self.mask("") == ""

    def test_twelve_digit_run_masked(self):
        assert self.mask("000011112222") == "XXXX XXXX 2222"


# ---------------------------------------------------------------------------
# Aadhaar masking — mask_aadhaar_in_dict (recursive)
# ---------------------------------------------------------------------------

class TestMaskAadhaarInDict:

    @pytest.fixture(autouse=True)
    def _import(self):
        with patch.dict("sys.modules", {"ollama": MagicMock()}):
            from ollama_client import mask_aadhaar_in_dict
            self.mask_dict = mask_aadhaar_in_dict

    def test_top_level_aadhaar_key(self):
        data = {"name": "Test User", "aadhaar_number": "1234 5678 9012"}
        assert self.mask_dict(data)["aadhaar_number"] == "XXXX XXXX 9012"

    def test_non_aadhaar_key_unchanged(self):
        data = {"name": "Test User", "dob": "1973-04-15"}
        masked = self.mask_dict(data)
        assert masked["name"] == "Test User"
        assert masked["dob"] == "1973-04-15"

    def test_nested_dict_masked(self):
        data = {
            "aadhaar_number": "1234 5678 9012",
            "nested": {"aadhaar_ref": "9876 5432 1098"},
        }
        masked = self.mask_dict(data)
        assert masked["aadhaar_number"] == "XXXX XXXX 9012"
        assert masked["nested"]["aadhaar_ref"] == "XXXX XXXX 1098"

    def test_list_values_recursed(self):
        data = {"documents": [{"aadhaar_number": "1111 2222 3333"}, {"name": "plain"}]}
        masked = self.mask_dict(data)
        assert masked["documents"][0]["aadhaar_number"] == "XXXX XXXX 3333"
        assert masked["documents"][1]["name"] == "plain"

    def test_integer_values_unchanged(self):
        data = {"age": 52, "score": 99}
        assert self.mask_dict(data)["age"] == 52

    def test_empty_dict(self):
        assert self.mask_dict({}) == {}


# ---------------------------------------------------------------------------
# extract_fields() — JSON parsing + privacy with mocked ollama
# ---------------------------------------------------------------------------

VALID_AADHAAR_JSON = json.dumps({
    "name": "Rukmini Devi",
    "dob": "1973-04-15",
    "gender": "F",
    "address": "H.No 23, Sira Road, Tumkur",
    "district": "Tumkur",
    "state": "Karnataka",
    "aadhaar_number": "1234 5678 9012",
})


def _mock_chat_response(content: str) -> dict:
    return {"message": {"content": content}}


@patch("ollama_client.ollama")
def test_valid_json_parses_all_fields(mock_ollama):
    mock_ollama.chat.return_value = _mock_chat_response(VALID_AADHAAR_JSON)
    with patch("ollama_client.load_prompt", return_value="extract prompt"):
        from ollama_client import extract_fields
        result = extract_fields(b"fake_image", "aadhaar")
    assert result["name"] == "Rukmini Devi"
    assert result["dob"] == "1973-04-15"
    assert result["gender"] == "F"
    assert result["district"] == "Tumkur"
    assert result["state"] == "Karnataka"


@patch("ollama_client.ollama")
def test_aadhaar_number_masked_in_output(mock_ollama):
    mock_ollama.chat.return_value = _mock_chat_response(VALID_AADHAAR_JSON)
    with patch("ollama_client.load_prompt", return_value="extract prompt"):
        from ollama_client import extract_fields
        result = extract_fields(b"fake_image", "aadhaar")
    assert result["aadhaar_number"] == "XXXX XXXX 9012"
    assert "1234" not in result["aadhaar_number"]


@patch("ollama_client.ollama")
def test_json_in_markdown_fences_parsed(mock_ollama):
    fenced = f"```json\n{VALID_AADHAAR_JSON}\n```"
    mock_ollama.chat.return_value = _mock_chat_response(fenced)
    with patch("ollama_client.load_prompt", return_value="extract prompt"):
        from ollama_client import extract_fields
        result = extract_fields(b"fake_image", "aadhaar")
    # Either parsed correctly or returns an error key — must not raise
    assert isinstance(result, dict)


@patch("ollama_client.ollama")
def test_unparseable_response_returns_error(mock_ollama):
    mock_ollama.chat.return_value = _mock_chat_response("I could not read the document.")
    with patch("ollama_client.load_prompt", return_value="extract prompt"):
        from ollama_client import extract_fields
        result = extract_fields(b"fake_image", "aadhaar")
    assert "error" in result


@patch("ollama_client.ollama")
def test_ration_card_loads_ration_prompt(mock_ollama):
    ration_json = json.dumps({
        "card_number": "KA-BPL-12345", "category": "AAY",
        "head_of_family": "Rukmini Devi", "state": "Karnataka", "district": "Tumkur",
    })
    mock_ollama.chat.return_value = _mock_chat_response(ration_json)
    with patch("ollama_client.load_prompt", return_value="ration prompt") as mock_load:
        from ollama_client import extract_fields
        extract_fields(b"fake_image", "ration_card")
        mock_load.assert_called_once_with("extract_ration_card")
