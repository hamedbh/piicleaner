"""Main Cleaner class for PII detection and cleaning"""

from piicleaner._internal import detect_pii as rust_detect_pii, clean_pii as rust_clean_pii


class Cleaner:
    """A Cleaner object contains methods to clean Personal
    Identifiable Information (PII) from text data using regex patterns.
    """
    
    def __init__(self, cleaners="all"):
        """Cleaner initialisation."""
        # For now, we'll just store the cleaner type
        # Later we'll add support for selecting specific cleaners
        self.cleaners = cleaners
    
    def detect_pii(self, string, ignore_case=True):
        """Detect PII in a string and return match information"""
        # For now, ignore the ignore_case parameter - we'll add it later
        matches = rust_detect_pii(string)
        
        # Convert to the format your original API returns
        return [
            {
                "start": start,
                "end": end, 
                "text": text
            }
            for start, end, text in matches
        ]
    
    def clean_pii(self, string, cleaning, ignore_case=True):
        """Clean PII from a string"""
        # For now, ignore the ignore_case parameter
        return rust_clean_pii(string, cleaning)
