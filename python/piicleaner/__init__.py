"""
PIICleaner - Personal Identifiable Information detection and cleaning for text
data.
This package provides functionality to detect and clean PII from text data,
with support for various types of sensitive information like National Insurance
numbers, email addresses, phone numbers, and more.
"""

# Import the Rust functions
# Import the Cleaner class
from ._cleaner import Cleaner
from ._internal import (
    clean_pii,
    clean_pii_batch,
    clean_pii_with_cleaners_batch,
    detect_pii,
    detect_pii_batch,
    detect_pii_with_cleaners,
    detect_pii_with_cleaners_batch,
    get_available_cleaners,
)

# Import Polars integration
try:
    import importlib.util

    if importlib.util.find_spec("polars") is not None:
        from . import _polars_plugin  # noqa: F401

        print("Polars plugin imported successfully")
except ImportError:
    print("Polars not available - skipping plugin registration")

__version__ = "0.1.0"

__all__ = [
    "detect_pii",
    "detect_pii_batch",
    "clean_pii",
    "clean_pii_batch",
    "clean_pii_with_cleaners_batch",
    "detect_pii_with_cleaners",
    "detect_pii_with_cleaners_batch",
    "get_available_cleaners",
    "Cleaner",
]
