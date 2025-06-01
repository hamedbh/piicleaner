"""PII Cleaner - A fast library for detecting and cleaning personally identifiable information"""

# Import the Rust functions (keep these available)
# Import the main Cleaner class
from piicleaner._cleaner import Cleaner
from piicleaner._internal import (
    clean_pii,
    detect_pii,
    detect_pii_with_cleaners,
    get_available_cleaners,
)

# Import and register Polars namespace - do this last
try:
    import piicleaner._polars_plugin

    print("Polars plugin imported successfully")
except ImportError as e:
    print(f"Polars plugin import failed: {e}")

# Make everything available at the top level
__all__ = [
    "detect_pii",
    "clean_pii",
    "detect_pii_with_cleaners",
    "get_available_cleaners",
    "Cleaner",
]
