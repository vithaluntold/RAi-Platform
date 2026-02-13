"""Financial data normalization utilities for matching financial statement names."""

import re
from typing import Optional
from app.constants.financial_mappings import FINANCIAL_STATEMENT_MAPPINGS


def normalize_financial_statement_name(name: str) -> str:
    """
    Normalize a financial statement name by removing special characters,
    converting to lowercase, and trimming whitespace.
    
    Args:
        name: Raw financial statement name
        
    Returns:
        Normalized name in lowercase
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Remove extra whitespace
    name = name.strip()
    
    # Remove special characters but keep spaces for multi-word names
    name = re.sub(r'[^\w\s]', '', name)
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()


def map_financial_statement_name(name: str) -> Optional[str]:
    """
    Map a financial statement name to its standardized form using the mappings dictionary.
    Includes fuzzy matching for slight variations.
    
    Args:
        name: Financial statement name to map
        
    Returns:
        Standardized financial statement name, or None if no match found
    """
    if not name or not isinstance(name, str):
        return None
    
    normalized = normalize_financial_statement_name(name)
    
    # Direct lookup in mappings
    if normalized in FINANCIAL_STATEMENT_MAPPINGS:
        return FINANCIAL_STATEMENT_MAPPINGS[normalized]
    
    # Fuzzy substring matching - check if any mapping key is a substring
    for key, value in FINANCIAL_STATEMENT_MAPPINGS.items():
        if key in normalized or normalized in key:
            return value
    
    return None


def is_financial_statement_present(
    statement_name: str,
    expected_names: list[str]
) -> bool:
    """
    Check if a financial statement name is present in an expected list,
    accounting for various naming conventions.
    
    Args:
        statement_name: Name to search for
        expected_names: List of names to search in
        
    Returns:
        True if the statement name is found (with normalization), False otherwise
    """
    if not statement_name or not expected_names:
        return False
    
    normalized_statement = normalize_financial_statement_name(statement_name)
    normalized_expected = [
        normalize_financial_statement_name(name) for name in expected_names
    ]
    
    return normalized_statement in normalized_expected


__all__ = [
    "normalize_financial_statement_name",
    "map_financial_statement_name",
    "is_financial_statement_present",
]
