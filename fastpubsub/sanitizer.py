"""
Sanitization utilities for preventing SQL and XSS injection attacks.
"""

import html
import re
from typing import Any


def sanitize_string(value: str) -> str:
    """
    Sanitize a string value to prevent XSS attacks.
    
    - HTML entity encoding to prevent script injection
    - Remove null bytes and control characters
    
    Args:
        value: String to sanitize
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return value
    
    # Remove null bytes and other control characters (except newlines, tabs)
    # Control characters can be used in injection attacks
    value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    # HTML entity encode to prevent XSS
    value = html.escape(value, quote=True)
    
    return value


def validate_filter_structure(filter_dict: dict | None) -> bool:
    """
    Validate that a filter has the correct structure.
    
    Expected structure: {"field_name": ["value1", "value2", ...]}
    - Keys must be strings
    - Values must be arrays
    - Array elements must be strings, numbers, or booleans (primitives)
    
    Args:
        filter_dict: Filter dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    if filter_dict is None or filter_dict == {}:
        return True
    
    if not isinstance(filter_dict, dict):
        return False
    
    for key, value in filter_dict.items():
        # Keys must be strings
        if not isinstance(key, str):
            return False
        
        # Values must be lists/arrays
        if not isinstance(value, list):
            return False
        
        # Array elements must be primitives (string, int, float, bool)
        for item in value:
            if not isinstance(item, (str, int, float, bool)):
                return False
            # Disallow None/null in arrays
            if item is None:
                return False
    
    return True


def sanitize_filter(filter_dict: dict | None) -> dict | None:
    """
    Sanitize a filter dictionary to prevent SQL and XSS injection attacks.
    
    This function:
    1. Validates the filter structure
    2. Sanitizes all string keys and values
    3. Ensures no malicious content can be injected
    
    Args:
        filter_dict: Filter dictionary to sanitize
        
    Returns:
        Sanitized filter dictionary
        
    Raises:
        ValueError: If filter structure is invalid
    """
    if filter_dict is None or filter_dict == {}:
        return filter_dict
    
    # Validate structure first
    if not validate_filter_structure(filter_dict):
        raise ValueError(
            "Invalid filter structure. Expected format: "
            '{"field_name": ["value1", "value2"]} where values are strings, numbers, or booleans'
        )
    
    # Sanitize all keys and values
    sanitized = {}
    for key, values in filter_dict.items():
        # Sanitize key (field name)
        sanitized_key = sanitize_string(key)
        
        # Sanitize each value in the array
        sanitized_values = []
        for value in values:
            if isinstance(value, str):
                sanitized_values.append(sanitize_string(value))
            else:
                # Numbers and booleans don't need sanitization
                sanitized_values.append(value)
        
        sanitized[sanitized_key] = sanitized_values
    
    return sanitized
