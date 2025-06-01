"""Main Cleaner class for PII detection and cleaning"""

from piicleaner._internal import clean_pii as rust_clean_pii
from piicleaner._internal import detect_pii as rust_detect_pii
from piicleaner._internal import (
    detect_pii_with_cleaners,
    get_available_cleaners,
)
from piicleaner._polars import PolarsCleanerMixin


class Cleaner(PolarsCleanerMixin):
    """A Cleaner object contains methods to clean Personal
    Identifiable Information (PII) from text data using regex patterns.

    :param cleaners: The cleaners to use. Default "all" uses all
        available cleaners. Available: "email", "postcode", "telephone"
    :type cleaners: str or list[str], default is "all"
    """

    def __init__(self, cleaners="all"):
        """Cleaner initialisation."""
        if isinstance(cleaners, str):
            if cleaners == "all":
                self.cleaners = "all"
            else:
                self.cleaners = [cleaners]
        elif isinstance(cleaners, list):
            self.cleaners = cleaners
        else:
            raise TypeError(
                "Unsupported type, please provide a string or list of strings"
            )

    def detect_pii(self, string, ignore_case=True):
        """Detect PII in a string and return match information"""
        # For now, ignore the ignore_case parameter
        if self.cleaners == "all":
            matches = rust_detect_pii(string)
        else:
            matches = detect_pii_with_cleaners(string, self.cleaners)

        # Convert to the format your original API returns
        return [
            {"start": start, "end": end, "text": text}
            for start, end, text in matches
        ]

    def clean_pii(self, string, cleaning, ignore_case=True):
        """Clean PII from a string"""
        # Use cleaner-specific cleaning if not using all patterns
        if self.cleaners == "all":
            return rust_clean_pii(string, cleaning)
        else:
            # For specific cleaners, we need to implement custom logic
            # since there's no rust function for cleaner-specific cleaning yet
            # For now, detect with specific cleaners and replace manually
            matches = self.detect_pii(string)
            if not matches:
                return string

            if cleaning == "replace":
                return "[PII detected, comment redacted]"
            else:  # redact
                result = string
                # Sort matches by start position in reverse to avoid index
                # shifting
                sorted_matches = sorted(
                    matches, key=lambda x: x["start"], reverse=True
                )
                for match in sorted_matches:
                    start, end = match["start"], match["end"]
                    replacement = "-" * (end - start)
                    result = result[:start] + replacement + result[end:]
                return result

    def clean_list(self, string_list, cleaning, ignore_case=True):
        """Method for cleaning PII in a list of strings.

        :param string_list: list of strings to clean
        :param cleaning: cleaning method to use (replace or redact)
        :param ignore_case: Should we ignore case when detecting PII?
        """
        if not isinstance(string_list, list):
            raise TypeError("string_list must be a list")

        if not all(isinstance(x, str) for x in string_list):
            raise TypeError("All values in list must be `str`.")

        # Use vectorized function for better performance
        if self.cleaners == "all":
            from piicleaner._internal import clean_pii_batch

            return clean_pii_batch(string_list, cleaning)
        else:
            # Use vectorized function for specific cleaners too
            from piicleaner._internal import clean_pii_with_cleaners_batch

            return clean_pii_with_cleaners_batch(
                string_list, self.cleaners, cleaning
            )

    @staticmethod
    def get_available_cleaners():
        """Get list of available cleaner names"""
        return sorted(get_available_cleaners())
