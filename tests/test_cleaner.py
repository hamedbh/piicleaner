"""Tests for the Cleaner class core functionality."""

import pytest
from piicleaner import Cleaner


class TestCleanerInitialization:
    """Test Cleaner class initialization and configuration."""

    def test_init_default(self):
        """Test default initialization uses all cleaners."""
        cleaner = Cleaner()
        assert cleaner.cleaners == "all"

    def test_init_single_cleaner_string(self):
        """Test initialization with single cleaner as string."""
        cleaner = Cleaner("email")
        assert cleaner.cleaners == ["email"]

    def test_init_cleaner_list(self):
        """Test initialization with list of cleaners."""
        cleaners_list = ["email", "telephone", "postcode"]
        cleaner = Cleaner(cleaners_list)
        assert cleaner.cleaners == cleaners_list

    def test_init_invalid_type(self):
        """Test initialization with invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Unsupported type"):
            Cleaner(123)

    def test_get_available_cleaners(self):
        """Test static method returns available cleaner types."""
        cleaners = Cleaner.get_available_cleaners()
        assert isinstance(cleaners, list)
        assert len(cleaners) > 0
        assert "email" in cleaners
        assert "telephone" in cleaners
        assert "postcode" in cleaners
        assert "nino" in cleaners


class TestPIIDetection:
    """Test PII detection functionality."""

    @pytest.fixture
    def cleaner(self):
        """Default cleaner instance for testing."""
        return Cleaner()

    def test_detect_email(self, cleaner):
        """Test email detection."""
        text = "Contact john@example.com for more info"
        matches = cleaner.detect_pii(text)

        # Email pattern may match multiple times (different regex patterns)
        assert len(matches) >= 1
        email_matches = [m for m in matches if m["text"] == "john@example.com"]
        assert len(email_matches) >= 1
        assert email_matches[0]["start"] == 8
        assert email_matches[0]["end"] == 24

    def test_detect_nino(self, cleaner):
        """Test National Insurance number detection."""
        text = "My NINO is AB123456C"
        matches = cleaner.detect_pii(text)

        # NINO may also match as case-id pattern
        nino_matches = [m for m in matches if m["text"] == "AB123456C"]
        assert len(nino_matches) >= 1

    def test_detect_telephone(self, cleaner):
        """Test telephone number detection."""
        text = "Call me at +44 20 7946 0958"
        matches = cleaner.detect_pii(text)

        assert len(matches) == 1
        assert matches[0]["text"] == "+44 20 7946 0958"

    def test_detect_postcode(self, cleaner):
        """Test postcode detection."""
        text = "Send it to SW1A 1AA please"
        matches = cleaner.detect_pii(text)

        assert len(matches) == 1
        assert matches[0]["text"] == "SW1A 1AA"

    def test_detect_cash_amount(self, cleaner):
        """Test cash amount detection."""
        text = "The cost was £1,500 exactly"
        matches = cleaner.detect_pii(text)

        assert len(matches) == 1
        assert matches[0]["text"] == "£1,500"

    def test_detect_multiple_pii(self, cleaner):
        """Test detection of multiple PII types in one text."""
        text = "Email john@test.com or call +44 20 1234 5678"
        matches = cleaner.detect_pii(text)

        # May have duplicate email matches
        pii_texts = [match["text"] for match in matches]
        assert "john@test.com" in pii_texts
        assert "+44 20 1234 5678" in pii_texts

    def test_detect_no_pii(self, cleaner):
        """Test text with no PII returns empty list."""
        text = "This is just regular text with no sensitive information"
        matches = cleaner.detect_pii(text)

        assert matches == []

    def test_detect_specific_cleaners(self):
        """Test detection with specific cleaner types."""
        email_cleaner = Cleaner(["email"])
        text = "Email john@test.com or call +44 20 1234 5678"
        matches = email_cleaner.detect_pii(text)

        # Should only detect email, may have duplicates
        pii_texts = [match["text"] for match in matches]
        assert "john@test.com" in pii_texts
        assert "+44 20 1234 5678" not in pii_texts


class TestPIICleaning:
    """Test PII cleaning functionality."""

    @pytest.fixture
    def cleaner(self):
        """Default cleaner instance for testing."""
        return Cleaner()

    def test_clean_redact(self, cleaner):
        """Test redaction cleaning method."""
        text = "Contact john@example.com for help"
        cleaned = cleaner.clean_pii(text, "redact")

        assert "john@example.com" not in cleaned
        assert "Contact" in cleaned
        assert "for help" in cleaned

    def test_clean_replace(self, cleaner):
        """Test replace cleaning method."""
        text = "Contact john@example.com for help"
        cleaned = cleaner.clean_pii(text, "replace")

        assert "john@example.com" not in cleaned
        # Replace method should replace entire string if any PII found
        assert cleaned != text

    def test_clean_no_pii(self, cleaner):
        """Test cleaning text with no PII returns unchanged."""
        text = "This has no sensitive information"
        cleaned_redact = cleaner.clean_pii(text, "redact")
        cleaned_replace = cleaner.clean_pii(text, "replace")

        assert cleaned_redact == text
        assert cleaned_replace == text

    def test_clean_list_valid(self, cleaner):
        """Test cleaning list of strings."""
        text_list = [
            "Email: john@test.com",
            "Phone: +44 20 1234 5678",
            "No PII here",
        ]
        cleaned = cleaner.clean_list(text_list, "redact")

        assert len(cleaned) == 3
        assert "john@test.com" not in cleaned[0]
        assert "+44 20 1234 5678" not in cleaned[1]
        assert cleaned[2] == "No PII here"  # Unchanged

    def test_clean_list_invalid_input(self, cleaner):
        """Test clean_list with invalid input raises TypeError."""
        with pytest.raises(TypeError, match="string_list must be a list"):
            cleaner.clean_list("not a list", "redact")

    def test_clean_list_invalid_elements(self, cleaner):
        """Test clean_list with non-string elements raises TypeError."""
        with pytest.raises(
            TypeError, match="All values in list must be `str`"
        ):
            cleaner.clean_list(
                ["valid string", 123, "another string"], "redact"
            )


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_string_detection(self):
        """Test detection on empty string."""
        cleaner = Cleaner()
        matches = cleaner.detect_pii("")
        assert matches == []

    def test_empty_string_cleaning(self):
        """Test cleaning empty string."""
        cleaner = Cleaner()
        cleaned = cleaner.clean_pii("", "redact")
        assert cleaned == ""

    def test_whitespace_only_text(self):
        """Test detection and cleaning on whitespace-only text."""
        cleaner = Cleaner()
        text = "   \t\n  "

        matches = cleaner.detect_pii(text)
        assert matches == []

        cleaned = cleaner.clean_pii(text, "redact")
        assert cleaned == text

    def test_very_long_text(self):
        """Test with very long text containing PII."""
        cleaner = Cleaner()
        base_text = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10
        )
        text_with_pii = (
            base_text + " Contact john@example.com for help " + base_text
        )

        matches = cleaner.detect_pii(text_with_pii)
        email_matches = [m for m in matches if "john@example.com" in m["text"]]
        assert len(email_matches) >= 1

    def test_unicode_text(self):
        """Test with unicode characters."""
        cleaner = Cleaner()
        # Use ASCII email as unicode may not be supported
        text = "Contact user@example.com for 帮助"
        matches = cleaner.detect_pii(text)

        email_matches = [m for m in matches if "user@example.com" in m["text"]]
        assert len(email_matches) >= 1


class TestSpecificCleaners:
    """Test behavior with specific cleaner configurations."""

    def test_email_only_cleaner(self):
        """Test cleaner configured for emails only."""
        cleaner = Cleaner(["email"])
        text = "Email john@test.com or call +44 20 1234 5678"
        matches = cleaner.detect_pii(text)

        # Should only detect email
        pii_texts = [match["text"] for match in matches]
        assert "john@test.com" in pii_texts
        assert "+44 20 1234 5678" not in pii_texts

    def test_multiple_specific_cleaners(self):
        """Test cleaner with multiple specific types."""
        cleaner = Cleaner(["email", "telephone"])
        text = "Email john@test.com, NINO AB123456C, call +44 20 1234 5678"
        matches = cleaner.detect_pii(text)

        # Should only detect email and telephone, not NINO
        pii_texts = [match["text"] for match in matches]
        assert "john@test.com" in pii_texts
        assert "+44 20 1234 5678" in pii_texts
        assert "AB123456C" not in pii_texts

    def test_nonexistent_cleaner(self):
        """Test behavior with non-existent cleaner type."""
        cleaner = Cleaner(["nonexistent"])
        text = "Email john@test.com"
        matches = cleaner.detect_pii(text)

        # Should not detect anything with invalid cleaner
        assert matches == []
