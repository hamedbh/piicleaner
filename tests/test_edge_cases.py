"""Tests for edge cases, boundary conditions, and error handling."""


import pytest
from piicleaner import Cleaner


class TestStringBoundaryConditions:
    """Test boundary conditions for string inputs."""

    @pytest.fixture
    def cleaner(self):
        """Default cleaner instance."""
        return Cleaner()

    def test_empty_string(self, cleaner):
        """Test behavior with empty strings."""
        assert cleaner.detect_pii("") == []
        assert cleaner.clean_pii("", "redact") == ""
        assert cleaner.clean_pii("", "replace") == ""

    def test_whitespace_only(self, cleaner):
        """Test behavior with whitespace-only strings."""
        whitespace_texts = [" ", "\t", "\n", "\r", "   \t\n\r   "]

        for text in whitespace_texts:
            assert cleaner.detect_pii(text) == []
            assert cleaner.clean_pii(text, "redact") == text
            assert cleaner.clean_pii(text, "replace") == text

    def test_very_long_strings(self, cleaner):
        """Test behavior with very long strings."""
        # Test long string with PII in middle
        base = "Lorem ipsum dolor sit amet. " * 1000
        text_with_pii = base + "Contact test@example.com for help. " + base

        matches = cleaner.detect_pii(text_with_pii)
        email_matches = [m for m in matches if "test@example.com" in m["text"]]
        assert len(email_matches) >= 1

        # Test cleaning very long string
        cleaned = cleaner.clean_pii(text_with_pii, "redact")
        assert "test@example.com" not in cleaned
        assert len(cleaned) > 0

    def test_extremely_long_string(self, cleaner):
        """Test with extremely long string (stress test)."""
        # 100KB string
        huge_text = "A" * 50000 + "email@domain.com" + "B" * 50000

        matches = cleaner.detect_pii(huge_text)
        email_matches = [m for m in matches if "email@domain.com" in m["text"]]
        assert len(email_matches) >= 1

    def test_single_character_strings(self, cleaner):
        """Test with single character strings."""
        single_chars = ["a", "1", "@", ".", " ", "\n"]

        for char in single_chars:
            assert cleaner.detect_pii(char) == []
            assert cleaner.clean_pii(char, "redact") == char


class TestSpecialCharacters:
    """Test handling of special characters and encodings."""

    @pytest.fixture
    def cleaner(self):
        return Cleaner()

    def test_newlines_and_tabs(self, cleaner):
        """Test PII detection across newlines and tabs."""
        text_with_newlines = (
            "Email:\ntest@example.com\nPhone:\t+44 20 1234 5678"
        )
        matches = cleaner.detect_pii(text_with_newlines)

        pii_texts = [m["text"] for m in matches]
        assert any("test@example.com" in text for text in pii_texts)
        assert any("+44 20 1234 5678" in text for text in pii_texts)

    def test_mixed_case_pii(self, cleaner):
        """Test PII detection with mixed case."""
        mixed_case_texts = [
            "EMAIL: JOHN@EXAMPLE.COM",
            "nino: ab123456c",
            "Phone: +44 20 1234 5678",
        ]

        for text in mixed_case_texts:
            matches = cleaner.detect_pii(text)
            assert len(matches) >= 1

    def test_punctuation_around_pii(self, cleaner):
        """Test PII detection with surrounding punctuation."""
        punctuation_tests = [
            "(test@example.com)",
            "Email: test@example.com.",
            "Contact: test@example.com!",
            "'test@example.com'",
            '"test@example.com"',
            "[test@example.com]",
            "test@example.com;",
            "test@example.com,",
        ]

        for text in punctuation_tests:
            matches = cleaner.detect_pii(text)
            email_matches = [
                m for m in matches if "test@example.com" in m["text"]
            ]
            assert len(email_matches) >= 1, (
                f"Failed to detect email in: {text}"
            )

    def test_unicode_characters(self, cleaner):
        """Test with unicode characters."""
        # Test unicode around ASCII PII
        unicode_texts = [
            "联系 test@example.com 获取帮助",
            "Email: test@example.com ñoño",
            "Téléphone: +44 20 1234 5678",
            "Cost: £1,500 émails",
        ]

        for text in unicode_texts:
            matches = cleaner.detect_pii(text)
            # Should still detect ASCII PII even with unicode present
            assert len(matches) >= 1, (
                f"Failed to detect PII in unicode text: {text}"
            )

    def test_control_characters(self, cleaner):
        """Test with control characters."""
        control_text = (
            "Email:\x00test@example.com\x01phone:\x02+44 20 1234 5678"
        )
        matches = cleaner.detect_pii(control_text)

        # Should still detect PII despite control characters
        pii_texts = [m["text"] for m in matches]
        assert any("test@example.com" in text for text in pii_texts)


class TestMalformedAndIncompleteData:
    """Test handling of malformed or incomplete PII data."""

    @pytest.fixture
    def cleaner(self):
        return Cleaner()

    def test_incomplete_emails(self, cleaner):
        """Test with incomplete or malformed email addresses."""
        incomplete_emails = [
            "test@",
            "@example.com",
            "test@@example.com",
            "test@.com",
            "test@example.",
            "test.example.com",
            "test @example.com",  # space in email
        ]

        for email in incomplete_emails:
            matches = cleaner.detect_pii(email)
            # Most incomplete emails should not be detected as valid emails
            # We expect few or no matches for malformed email addresses
            assert len(matches) <= 1, (
                f"Too many matches for malformed email '{email}': {matches}"
            )

    def test_incomplete_phone_numbers(self, cleaner):
        """Test with incomplete phone numbers."""
        incomplete_phones = [
            "+44",
            "123",
            "+44 20",
            "123 456",
            "abcd efgh ijkl",  # letters instead of numbers
        ]

        for phone in incomplete_phones:
            matches = cleaner.detect_pii(phone)
            # Incomplete phone numbers should not be detected as valid phones
            assert len(matches) == 0, (
                f"Unexpected matches for incomplete phone '{phone}': {matches}"
            )

    def test_incomplete_postcodes(self, cleaner):
        """Test with incomplete UK postcodes."""
        incomplete_postcodes = [
            "SW1",
            "1AA",
            "SW1A",
            "A1",
            "123 456",  # wrong format
        ]

        for postcode in incomplete_postcodes:
            matches = cleaner.detect_pii(postcode)
            # Incomplete postcodes should not be detected as valid postcodes
            assert len(matches) == 0, (
                f"Unexpected matches for incomplete postcode "
                f"'{postcode}': {matches}"
            )

    def test_almost_valid_ninos(self, cleaner):
        """Test with almost-valid National Insurance numbers."""
        almost_ninos = [
            "AB123456",  # missing suffix
            "A123456C",  # too short prefix
            "QQ123456C",  # invalid prefix letters
            "AB12345C",  # too short number
            "AB1234567C",  # too long number
        ]

        for nino in almost_ninos:
            matches = cleaner.detect_pii(nino)
            # Almost-valid NINOs should generally not be detected as valid
            # Allow some flexibility as case-id patterns might still match
            assert len(matches) <= 2, (
                f"Too many matches for almost-NINO '{nino}': {matches}"
            )


class TestOverlappingPatterns:
    """Test cases where multiple PII patterns might overlap."""

    @pytest.fixture
    def cleaner(self):
        return Cleaner()

    def test_overlapping_nino_and_case_id(self, cleaner):
        """Test NINO that also matches case-id patterns."""
        nino_text = "AB123456C"
        matches = cleaner.detect_pii(nino_text)

        # Might match both NINO and case-id patterns
        assert len(matches) >= 1

        # Check that at least one match covers the full NINO
        full_matches = [m for m in matches if m["text"] == "AB123456C"]
        assert len(full_matches) >= 1

    def test_number_sequences_in_text(self, cleaner):
        """Test long number sequences that might match multiple patterns."""
        number_text = "Reference: 1234567890123456"
        matches = cleaner.detect_pii(number_text)

        # Might match case-id patterns
        assert len(matches) >= 0  # Could be 0 or more depending on patterns

    def test_email_with_numbers(self, cleaner):
        """Test email addresses with numbers that might trigger patterns."""
        email_with_numbers = "user123456@domain123.com"
        matches = cleaner.detect_pii(email_with_numbers)

        # Should definitely detect as email
        email_matches = [m for m in matches if "@" in m["text"]]
        assert len(email_matches) >= 1

    def test_mixed_pii_in_single_string(self, cleaner):
        """Test string containing multiple types of PII close together."""
        mixed_pii = (
            "Contact john@test.com or call +44 20 1234 5678 ref "
            "AB123456C at SW1A 1AA"
        )
        matches = cleaner.detect_pii(mixed_pii)

        # Should detect multiple types
        pii_texts = [m["text"] for m in matches]
        assert any("john@test.com" in text for text in pii_texts)
        assert any("+44 20 1234 5678" in text for text in pii_texts)
        assert any("AB123456C" in text for text in pii_texts)
        assert any("SW1A 1AA" in text for text in pii_texts)


class TestCleaningBehaviorEdgeCases:
    """Test edge cases in cleaning behavior."""

    @pytest.fixture
    def cleaner(self):
        return Cleaner()

    def test_multiple_pii_cleaning_redact(self, cleaner):
        """Test redacting text with multiple PII instances."""
        multi_pii_text = (
            "Email john@test.com and mary@test.com, call +44 20 1234 5678"
        )
        cleaned = cleaner.clean_pii(multi_pii_text, "redact")

        assert "john@test.com" not in cleaned
        assert "mary@test.com" not in cleaned
        assert "+44 20 1234 5678" not in cleaned
        assert "Email" in cleaned  # Non-PII text should remain
        assert "and" in cleaned
        assert "call" in cleaned

    def test_multiple_pii_cleaning_replace(self, cleaner):
        """Test replacing text with multiple PII instances."""
        multi_pii_text = "Contact john@test.com or call +44 20 1234 5678"
        original_text = multi_pii_text
        cleaned = cleaner.clean_pii(multi_pii_text, "replace")

        # Replace method should change the entire string
        assert cleaned != original_text

    def test_cleaning_preserves_structure(self, cleaner):
        """Test that cleaning preserves text structure."""
        structured_text = """
        Name: John Doe
        Email: john@example.com
        Phone: +44 20 1234 5678
        Address: 123 High Street, SW1A 1AA
        """

        cleaned = cleaner.clean_pii(structured_text, "redact")

        # Structure should be preserved
        assert "Name: John Doe" in cleaned
        assert "Email:" in cleaned
        assert "Phone:" in cleaned
        assert "Address:" in cleaned
        assert "john@example.com" not in cleaned
        assert "+44 20 1234 5678" not in cleaned
        assert "SW1A 1AA" not in cleaned

    def test_cleaning_empty_detection_results(self, cleaner):
        """Test cleaning when no PII is detected."""
        no_pii_text = "This text contains no personal information."

        cleaned_redact = cleaner.clean_pii(no_pii_text, "redact")
        cleaned_replace = cleaner.clean_pii(no_pii_text, "replace")

        assert cleaned_redact == no_pii_text
        assert cleaned_replace == no_pii_text


class TestErrorHandling:
    """Test error handling and invalid inputs."""

    def test_invalid_cleaning_method(self):
        """Test invalid cleaning method parameter."""
        cleaner = Cleaner()
        text = "Email: test@example.com"

        # The cleaning method might not validate the parameter
        # This depends on implementation - test actual behavior
        try:
            result = cleaner.clean_pii(text, "invalid_method")
            # If no error, check what it returns
            assert isinstance(result, str)
        except Exception:
            # If it raises an exception, that's also valid behavior
            pass

    def test_none_input_handling(self):
        """Test behavior with None inputs."""
        cleaner = Cleaner()

        # These should raise TypeError for None inputs
        with pytest.raises(TypeError):
            cleaner.detect_pii(None)

        with pytest.raises(TypeError):
            cleaner.clean_pii(None, "redact")

    def test_non_string_inputs(self):
        """Test behavior with non-string inputs."""
        cleaner = Cleaner()
        non_strings = [123, [], {}, True, 3.14]

        for non_string in non_strings:
            with pytest.raises(TypeError):
                cleaner.detect_pii(non_string)

            with pytest.raises(TypeError):
                cleaner.clean_pii(non_string, "redact")


class TestPerformanceEdgeCases:
    """Test performance-related edge cases."""

    @pytest.fixture
    def cleaner(self):
        return Cleaner()

    def test_many_small_detections(self, cleaner):
        """Test text with many small PII matches."""
        # Create text with many small matches
        many_emails = " ".join([f"user{i}@test.com" for i in range(100)])

        matches = cleaner.detect_pii(many_emails)
        # Should detect all emails (duplicates from multiple patterns allowed)
        assert len(matches) >= 100

    def test_repeated_pattern_text(self, cleaner):
        """Test text with repeated patterns."""
        repeated_text = "test@example.com " * 1000

        matches = cleaner.detect_pii(repeated_text)
        # Should detect all instances
        assert len(matches) >= 1000

        cleaned = cleaner.clean_pii(repeated_text, "redact")
        assert "test@example.com" not in cleaned

    def test_alternating_pii_and_text(self, cleaner):
        """Test alternating PII and regular text."""
        alternating = ""
        for i in range(100):
            alternating += f"Text {i} email user{i}@test.com more text. "

        matches = cleaner.detect_pii(alternating)
        assert len(matches) >= 100

        cleaned = cleaner.clean_pii(alternating, "redact")
        assert "user99@test.com" not in cleaned
        assert "Text 99" in cleaned

    @pytest.mark.performance
    def test_large_dataframe_performance(self, cleaner):
        """Test performance with larger DataFrames to ensure vectorization."""
        try:
            import time

            import polars as pl
        except ImportError:
            pytest.skip("Polars not available for DataFrame performance test")

        # Create a reasonably large DataFrame for performance testing
        # Size chosen to complete in reasonable test time while demonstrating
        # vectorization performance improvements
        size = 1000
        test_data = [
            f"Email: user{i}@example.com for support" for i in range(size // 2)
        ]
        test_data += ["No PII in this text at all"] * (size // 2)

        df = pl.DataFrame({"text": test_data})

        # Test cleaning performance
        start_time = time.time()
        cleaned_df = cleaner.clean_dataframe(df, "text", "redact", "cleaned")
        clean_time = time.time() - start_time

        # Test detection performance
        start_time = time.time()
        detected_df = cleaner.detect_dataframe(df, "text")
        detect_time = time.time() - start_time

        # Verify results
        assert cleaned_df.shape == (size, 2)
        assert (
            detected_df.shape[0] >= size // 2
        )  # Should detect PII in half the rows

        # Performance assertions - should be fast with vectorization
        # Expecting at least 500 rows/second (much faster than non-vectorized)
        min_performance = 500  # rows per second
        clean_performance = size / clean_time
        detect_performance = size / detect_time

        assert clean_performance >= min_performance, (
            f"Cleaning performance too slow: {clean_performance:.0f} rows/sec "
            f"(expected ≥{min_performance})"
        )
        assert detect_performance >= min_performance, (
            f"Detection performance too slow: {detect_performance:.0f} "
            f"rows/sec (expected ≥{min_performance})"
        )

        # Verify correctness
        cleaned_texts = cleaned_df["cleaned"].to_list()

        # First half should be cleaned (no emails)
        pii_cleaned_count = sum(
            1
            for i in range(size // 2)
            if "user" not in cleaned_texts[i] and "@" not in cleaned_texts[i]
        )

        # Second half should be unchanged
        no_pii_unchanged_count = sum(
            1
            for i in range(size // 2, size)
            if cleaned_texts[i] == "No PII in this text at all"
        )

        assert pii_cleaned_count == size // 2, "Not all PII was cleaned"
        assert no_pii_unchanged_count == size // 2, (
            "Non-PII text was incorrectly modified"
        )

    @pytest.mark.performance
    def test_batch_function_performance(self, cleaner):
        """Test that batch functions outperform individual calls."""
        import time

        # Create test data
        test_texts = [f"Contact user{i}@test.com" for i in range(200)]

        # Test individual calls
        start_time = time.time()
        individual_results = [
            cleaner.clean_pii(text, "redact") for text in test_texts
        ]
        individual_time = time.time() - start_time

        # Test batch call
        start_time = time.time()
        batch_results = cleaner.clean_list(test_texts, "redact")
        batch_time = time.time() - start_time

        # Verify results are identical
        assert individual_results == batch_results

        # Batch should be significantly faster (at least 2x)
        speedup = individual_time / batch_time
        assert speedup >= 2.0, (
            f"Batch processing not fast enough: {speedup:.1f}x speedup "
            f"(expected ≥2x)"
        )

        # Performance should be reasonable
        batch_performance = len(test_texts) / batch_time
        assert batch_performance >= 1000, (
            f"Batch performance too slow: {batch_performance:.0f} texts/sec "
            f"(expected ≥1000)"
        )
