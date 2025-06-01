"""PII Cleaner - A fast library for detecting and cleaning personally identifiable information"""

# Import the Rust functions (keep these available)
from piicleaner._internal import detect_pii, clean_pii

# Import the main Cleaner class
from piicleaner._cleaner import Cleaner

# Make everything available at the top level
__all__ = ["detect_pii", "clean_pii", "Cleaner"]
