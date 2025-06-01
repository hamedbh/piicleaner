"""
PIICleaner - Personal Identifiable Information detection and cleaning for text
data.

This package provides functionality to detect and clean PII from text data,
with support for various types of sensitive information like National Insurance
numbers, email addresses, phone numbers, and more.
"""

# Import the Rust functions
from ._internal import (
    clean_pii,
    detect_pii,
    detect_pii_with_cleaners,
    get_available_cleaners,
)

# Import Polars integration
try:
    import polars as pl

    from . import _polars_plugin

    print("Polars plugin imported successfully")
except ImportError:
    print("Polars not available - skipping plugin registration")

__version__ = "0.1.0"
__all__ = [
    "detect_pii",
    "clean_pii",
    "detect_pii_with_cleaners",
    "get_available_cleaners",
]
