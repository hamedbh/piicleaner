"""Main Cleaner class for PII detection and cleaning"""

from piicleaner._internal import (
    clean_pii as _clean_pii,
    clean_pii_batch as _clean_pii_batch,
    clean_pii_with_cleaners as _clean_pii_with_cleaners,
    clean_pii_with_cleaners_batch as _clean_pii_with_cleaners_batch,
    detect_pii as _detect_pii,
    detect_pii_batch as _detect_pii_batch,
    detect_pii_with_cleaners as _detect_pii_with_cleaners,
    detect_pii_with_cleaners_batch as _detect_pii_with_cleaners_batch,
    get_available_cleaners,
)
from piicleaner._polars import PolarsCleanerMixin


class Cleaner(PolarsCleanerMixin):
    """A Cleaner object contains methods to detect and clean Personal
    Identifiable Information (PII) from text data using regex patterns.

    :param cleaners: The cleaners to use. Default "all" uses all
        available cleaners. Available cleaners include: "email", "postcode",
        "telephone", "nino", "address", "cash-amount", "case-id",
        "tag", "ip_address"
    :type cleaners: str or list[str], default is "all"
    :param replace_string: Custom replacement string for "replace"
        cleaning method. If None, uses default "[PII detected, text
        redacted]"
    :type replace_string: str or None, default is None
    """

    def __init__(
        self,
        cleaners: str | list[str] = "all",
        replace_string: str | None = None,
    ):
        """Cleaner initialisation.

        :param cleaners: PII types to detect/clean
        :param replace_string: Custom replacement text for "replace" mode
        """
        if isinstance(cleaners, str):
            if cleaners == "all":
                self.cleaners = ["all"]
            else:
                self.cleaners = [cleaners]
        elif isinstance(cleaners, list):
            self.cleaners = cleaners
        else:
            raise TypeError("`cleaners` must be a string or list of strings")

        self.replace_string = replace_string

    def detect_pii(
        self, string: str, ignore_case: bool = True
    ) -> list[dict[str, str | int]]:
        """Detect PII in a string and return match information.

        :param string: Text to analyse for PII
        :param ignore_case: Whether to ignore case when matching patterns
        :return: List of dictionaries with keys 'start', 'end', 'text', 'type'
        """
        if self.cleaners == ["all"]:
            matches = _detect_pii(string, ignore_case)
        else:
            matches = _detect_pii_with_cleaners(
                string, self.cleaners, ignore_case
            )

        # Convert to the format your original API returns
        return [
            {"start": start, "end": end, "text": text, "type": pii_type}
            for start, end, text, pii_type in matches
        ]

    def detect_pii_list(
        self, texts: list[str], ignore_case: bool = True
    ) -> list[list[dict[str, str | int]]]:
        """Detect PII in a list of strings and return match information.

        :param texts: List of strings to analyse for PII
        :param ignore_case: Whether to ignore case when matching patterns
        :return: List of lists of dictionaries with keys 'start',
            'end', 'text', 'type'
        """
        if self.cleaners == ["all"]:
            matches = _detect_pii_batch(texts, ignore_case)
        else:
            matches = _detect_pii_with_cleaners_batch(
                texts, self.cleaners, ignore_case
            )

        # Convert to the format your original API returns
        return [
            [
                {"start": start, "end": end, "text": text, "type": pii_type}
                for start, end, text, pii_type in match
            ]
            for match in matches
        ]

    def clean_pii(
        self,
        text: str,
        cleaning: str,
        ignore_case: bool = True,
    ) -> str:
        """Clean PII from a string.

        :param text: Text to clean
        :param cleaning: Cleaning method - either "redact" or "replace"
        :param ignore_case: Whether to ignore case when matching patterns
        :return: Cleaned text with PII removed or redacted
        """
        # Use cleaner-specific cleaning if not using all patterns
        if self.cleaners == ["all"]:
            return _clean_pii(text, cleaning, ignore_case, self.replace_string)
        else:
            return _clean_pii_with_cleaners(
                text, self.cleaners, cleaning, ignore_case, self.replace_string
            )

    def clean_pii_list(
        self,
        texts: list[str],
        cleaning: str,
        ignore_case: bool = True,
    ) -> list[str]:
        """Clean PII from a list of strings.

        :param texts: List of strings to clean
        :param cleaning: Cleaning method to use ("redact" or "replace")
        :param ignore_case: Whether to ignore case when detecting PII
        :return: List of cleaned strings
        """
        if self.cleaners == ["all"]:
            return _clean_pii_batch(
                texts, cleaning, ignore_case, self.replace_string
            )
        else:
            return _clean_pii_with_cleaners_batch(
                texts,
                self.cleaners,
                cleaning,
                ignore_case,
                self.replace_string,
            )

    @staticmethod
    def get_available_cleaners():
        """Get list of available cleaner names"""
        return sorted(get_available_cleaners())
