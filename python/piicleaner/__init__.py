"""PII Cleaner - A fast library for detecting and cleaning personally
identifiable information
"""

# Import the Rust functions (keep these available)
# Import the main Cleaner class
from piicleaner._cleaner import Cleaner
from piicleaner._internal import (
    clean_pii,
    detect_pii,
    detect_pii_with_cleaners,
    get_available_cleaners,
)

# Make everything available at the top level
__all__ = [
    "detect_pii",
    "clean_pii",
    "detect_pii_with_cleaners",
    "get_available_cleaners",
    "Cleaner",
]
