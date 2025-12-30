"""
Tests for sanitization functionality.
"""

import pytest

from fastpubsub.sanitizer import (
    sanitize_filter,
    sanitize_string,
    validate_filter_structure,
)


def test_sanitize_simple_string():
    """Test that simple strings pass through unchanged."""
    assert sanitize_string("hello") == "hello"
    assert sanitize_string("test123") == "test123"


def test_sanitize_xss_script_tag():
    """Test that script tags are HTML-encoded."""
    result = sanitize_string("<script>alert('xss')</script>")
    assert "&lt;script&gt;" in result
    assert "&lt;/script&gt;" in result
    assert "<script>" not in result


def test_sanitize_xss_img_onerror():
    """Test that img onerror XSS is encoded."""
    result = sanitize_string('<img src=x onerror="alert(1)">')
    assert "&lt;img" in result
    assert "&quot;" in result
    assert "onerror" in result
    assert "<img" not in result


def test_sanitize_sql_patterns():
    """Test that SQL-like patterns are handled (encoded for XSS)."""
    # While SQL injection isn't a direct risk with JSONB,
    # we still sanitize for XSS if these end up in a UI
    result = sanitize_string("'; DROP TABLE users; --")
    # These should pass through as text (they're not HTML)
    assert "DROP TABLE" in result
    assert "--" in result


def test_sanitize_quotes():
    """Test that quotes are properly escaped."""
    result = sanitize_string("\"quoted\" and 'single'")
    assert "&quot;" in result
    assert "&#x27;" in result


def test_sanitize_ampersand():
    """Test that ampersands are encoded."""
    result = sanitize_string("A & B")
    assert result == "A &amp; B"


def test_sanitize_control_characters():
    """Test that control characters are removed."""
    # Null byte
    result = sanitize_string("hello\x00world")
    assert result == "helloworld"

    # Other control characters
    result = sanitize_string("test\x01\x02\x03data")
    assert result == "testdata"

    # Newlines and tabs should be preserved
    result = sanitize_string("line1\nline2\ttab")
    assert "\n" in result
    assert "\t" in result


def test_sanitize_unicode():
    """Test that unicode characters are handled correctly."""
    result = sanitize_string("Hello 世界 🌍")
    assert "世界" in result
    assert "🌍" in result


def test_sanitize_empty_string():
    """Test that empty strings are handled."""
    assert sanitize_string("") == ""


def test_sanitize_non_string():
    """Test that non-string values are returned as-is."""
    assert sanitize_string(123) == 123
    assert sanitize_string(True) is True
    assert sanitize_string(None) is None


def test_validate_empty_filter():
    """Test that empty filters are valid."""
    assert validate_filter_structure({}) is True
    assert validate_filter_structure(None) is True


def test_validate_correct_structure():
    """Test that correctly structured filters are valid."""
    assert validate_filter_structure({"country": ["BR", "US"]}) is True
    assert validate_filter_structure({"status": ["active"]}) is True
    assert validate_filter_structure({"country": ["BR"], "status": ["active"]}) is True


def test_validate_with_numbers():
    """Test that filters with number values are valid."""
    assert validate_filter_structure({"age": [18, 25, 30]}) is True
    assert validate_filter_structure({"price": [9.99, 19.99]}) is True


def test_validate_with_booleans():
    """Test that filters with boolean values are valid."""
    assert validate_filter_structure({"premium": [True, False]}) is True
    assert validate_filter_structure({"active": [True]}) is True


def test_validate_mixed_types():
    """Test that filters with mixed primitive types are valid."""
    assert validate_filter_structure({"field": ["text", 123, True]}) is True


def test_validate_non_dict():
    """Test that non-dict filters are invalid."""
    assert validate_filter_structure("not a dict") is False
    assert validate_filter_structure(["list"]) is False
    assert validate_filter_structure(123) is False


def test_validate_non_string_keys():
    """Test that non-string keys are invalid."""
    assert validate_filter_structure({123: ["value"]}) is False
    assert validate_filter_structure({None: ["value"]}) is False


def test_validate_non_array_values():
    """Test that non-array values are invalid."""
    assert validate_filter_structure({"field": "string"}) is False
    assert validate_filter_structure({"field": 123}) is False
    assert validate_filter_structure({"field": {"nested": "dict"}}) is False


def test_validate_non_primitive_array_elements():
    """Test that non-primitive array elements are invalid."""
    assert validate_filter_structure({"field": [["nested", "array"]]}) is False
    assert validate_filter_structure({"field": [{"nested": "object"}]}) is False
    assert validate_filter_structure({"field": [None]}) is False


def test_validate_empty_arrays():
    """Test that empty arrays are valid."""
    assert validate_filter_structure({"field": []}) is True


def test_sanitize_none_filter():
    """Test that None filters are handled."""
    assert sanitize_filter(None) is None


def test_sanitize_empty_filter():
    """Test that empty filters are handled."""
    assert sanitize_filter({}) == {}


def test_sanitize_simple_filter():
    """Test that simple filters are sanitized."""
    result = sanitize_filter({"country": ["BR", "US"]})
    assert result == {"country": ["BR", "US"]}


def test_sanitize_filter_with_xss():
    """Test that XSS in filter values is sanitized."""
    input_filter = {"field": ["<script>alert('xss')</script>", "normal"]}
    result = sanitize_filter(input_filter)

    assert "field" in result
    assert len(result["field"]) == 2
    assert "&lt;script&gt;" in result["field"][0]
    assert "<script>" not in result["field"][0]
    assert result["field"][1] == "normal"


def test_sanitize_filter_with_xss_in_key():
    """Test that XSS in filter keys is sanitized."""
    input_filter = {"<script>": ["value"]}
    result = sanitize_filter(input_filter)

    # Key should be sanitized
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_sanitize_filter_with_numbers():
    """Test that number values pass through unchanged."""
    input_filter = {"age": [18, 25, 30]}
    result = sanitize_filter(input_filter)
    assert result == {"age": [18, 25, 30]}


def test_sanitize_filter_with_booleans():
    """Test that boolean values pass through unchanged."""
    input_filter = {"premium": [True, False]}
    result = sanitize_filter(input_filter)
    assert result == {"premium": [True, False]}


def test_sanitize_filter_with_control_characters():
    """Test that control characters are removed."""
    input_filter = {"field": ["test\x00data", "normal"]}
    result = sanitize_filter(input_filter)
    assert result["field"][0] == "testdata"
    assert result["field"][1] == "normal"


def test_sanitize_invalid_structure_raises():
    """Test that invalid filter structure raises ValueError."""
    with pytest.raises(ValueError, match="Invalid filter structure"):
        sanitize_filter({"field": "not an array"})

    with pytest.raises(ValueError, match="Invalid filter structure"):
        sanitize_filter({"field": [{"nested": "object"}]})

    with pytest.raises(ValueError, match="Invalid filter structure"):
        sanitize_filter("not a dict")


def test_sanitize_sql_injection_patterns():
    """Test handling of SQL injection patterns in values."""
    # These should be sanitized for XSS but pass as text
    input_filter = {
        "field": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
        ]
    }
    result = sanitize_filter(input_filter)

    # Should be treated as text values, quotes encoded
    assert "field" in result
    assert len(result["field"]) == 3
    # Single quotes should be encoded
    assert "&#x27;" in result["field"][0]
    assert "&#x27;" in result["field"][1]
    assert "&#x27;" in result["field"][2]


def test_sanitize_multiple_fields():
    """Test sanitizing filters with multiple fields."""
    input_filter = {
        "country": ["BR", "<script>alert(1)</script>"],
        "status": ["active", "inactive"],
        "age": [25, 30],
    }
    result = sanitize_filter(input_filter)

    assert "country" in result
    assert "status" in result
    assert "age" in result
    assert result["status"] == ["active", "inactive"]
    assert result["age"] == [25, 30]
    assert "&lt;script&gt;" in result["country"][1]


def test_sanitize_unicode_values():
    """Test that unicode values are preserved."""
    input_filter = {"language": ["中文", "日本語", "한국어"]}
    result = sanitize_filter(input_filter)
    assert result == {"language": ["中文", "日本語", "한국어"]}


def test_sanitize_special_characters():
    """Test handling of various special characters."""
    input_filter = {"field": ["a&b", "c<d", "e>f", 'g"h', "i'j"]}
    result = sanitize_filter(input_filter)

    assert result["field"][0] == "a&amp;b"
    assert "&lt;" in result["field"][1]
    assert "&gt;" in result["field"][2]
    assert "&quot;" in result["field"][3]
    assert "&#x27;" in result["field"][4]
