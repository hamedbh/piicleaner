"""Tests for Pandas namespace API functionality"""

import pytest

# Skip all tests if pandas is not available
pytest.importorskip("pandas")

import numpy as np
import pandas as pd
import piicleaner  # noqa: F401
from piicleaner import Cleaner


class TestPandasNamespace:
    """Test the .pii namespace extension for Pandas"""

    def test_namespace_clean_pii_redact(self):
        """Test .pii.clean_pii() with redact mode"""
        df = pd.DataFrame(
            {
                "text": [
                    "Contact john@example.com",
                    "My NINO is AB123456C",
                    "Cost was £1,500",
                    "No PII here",
                ]
            }
        )

        result = df["text"].pii.clean_pii("redact")

        # Check that we get a Series back
        assert isinstance(result, pd.Series)

        cleaned_texts = result.tolist()

        # Email should be redacted
        assert "john@example.com" not in cleaned_texts[0]
        assert "-" in cleaned_texts[0]  # Should contain dashes

        # NINO should be redacted
        assert "AB123456C" not in cleaned_texts[1]
        assert "-" in cleaned_texts[1]

        # Cash amount should be redacted
        assert "£1,500" not in cleaned_texts[2]
        assert "-" in cleaned_texts[2]

        # Clean text should remain unchanged
        assert cleaned_texts[3] == "No PII here"

    def test_namespace_clean_pii_replace(self):
        """Test .pii.clean_pii() with replace mode"""
        df = pd.DataFrame(
            {
                "text": [
                    "Contact john@example.com",
                    "No PII here",
                ]
            }
        )

        result = df["text"].pii.clean_pii("replace")

        cleaned_texts = result.tolist()

        # Text with PII should be replaced entirely
        assert cleaned_texts[0] == "[PII detected, text redacted]"

        # Clean text should remain unchanged
        assert cleaned_texts[1] == "No PII here"

    def test_namespace_detect_pii(self):
        """Test .pii.detect_pii() namespace method"""
        df = pd.DataFrame(
            {
                "text": [
                    "Contact john@example.com",
                    "My NINO is AB123456C",
                    "No PII here",
                ]
            }
        )

        result = df["text"].pii.detect_pii()

        # Check that we get a Series back
        assert isinstance(result, pd.Series)

        pii_results = result.tolist()

        # First text should have detected PII (email)
        assert len(pii_results[0]) >= 1
        email_found = any(
            "john@example.com" in match["text"] for match in pii_results[0]
        )
        assert email_found

        # Second text should have detected PII (NINO)
        assert len(pii_results[1]) >= 1
        nino_found = any(
            "AB123456C" in match["text"] for match in pii_results[1]
        )
        assert nino_found

        # Third text should have no PII detected
        assert len(pii_results[2]) == 0

    def test_namespace_with_multiple_columns(self):
        """Test namespace methods work with multiple text columns"""
        df = pd.DataFrame(
            {
                "text1": ["Email: john@example.com", "No PII here"],
                "text2": ["NINO: AB123456C", "Clean text"],
            }
        )

        # Process both columns
        df["cleaned1"] = df["text1"].pii.clean_pii("redact")
        df["cleaned2"] = df["text2"].pii.clean_pii("redact")

        # Check both columns were processed
        assert "cleaned1" in df.columns
        assert "cleaned2" in df.columns

        # Verify cleaning worked
        assert "john@example.com" not in df["cleaned1"].iloc[0]
        assert "AB123456C" not in df["cleaned2"].iloc[0]
        assert df["cleaned1"].iloc[1] == "No PII here"
        assert df["cleaned2"].iloc[1] == "Clean text"

    def test_namespace_invalid_cleaning_method(self):
        """Test namespace raises an error for invalid cleaning method"""
        df = pd.DataFrame({"text": ["Email: john@example.com"]})

        # Invalid cleaning method should raise an exception
        with pytest.raises(ValueError, match="Invalid cleaning method"):
            df["text"].pii.clean_pii("invalid_method")

    def test_invalid_cleaning_method_variations(self):
        """Test various invalid cleaning method inputs"""
        df = pd.DataFrame({"text": ["Email: john@example.com"]})

        invalid_methods = ["REPLACE", "REDACT", "remove", "mask", "", "delete"]

        for invalid_method in invalid_methods:
            with pytest.raises(ValueError, match="Invalid cleaning method"):
                df["text"].pii.clean_pii(invalid_method)

    def test_valid_cleaning_methods_case_sensitivity(self):
        """Test that only exact case matches work for cleaning methods"""
        df = pd.DataFrame({"text": ["Email: john@example.com"]})

        # These should all fail (case sensitivity)
        invalid_cases = ["Replace", "REPLACE", "Redact", "REDACT"]

        for invalid_case in invalid_cases:
            with pytest.raises(ValueError, match="Invalid cleaning method"):
                df["text"].pii.clean_pii(invalid_case)

    def test_empty_and_none_cleaning_method(self):
        """Test edge cases for cleaning method parameter"""
        df = pd.DataFrame({"text": ["Email: john@example.com"]})

        # Empty string
        with pytest.raises(ValueError, match="Invalid cleaning method"):
            df["text"].pii.clean_pii("")

        # None should also fail if passed somehow
        with pytest.raises((ValueError, TypeError)):
            df["text"].pii.clean_pii(None)

    def test_namespace_with_null_values(self):
        """Test namespace API handles null values correctly"""
        df = pd.DataFrame(
            {"text": ["Email: test@example.com", None, "Clean text"]}
        )

        cleaned = df["text"].pii.clean_pii("redact")
        detected = df["text"].pii.detect_pii()

        assert pd.isna(cleaned.iloc[1])  # Null should remain null
        assert detected.iloc[1] == []  # Null should return empty list

        assert "test@example.com" not in cleaned.iloc[0]
        assert cleaned.iloc[2] == "Clean text"

    def test_namespace_with_specific_cleaners(self):
        """Test namespace methods with specific cleaner types"""
        df = pd.DataFrame(
            {
                "text": [
                    "Email alice@test.com and call +44 20 1234 5678",
                    "NINO: AB123456C",
                ]
            }
        )

        # Test with email-only cleaner
        email_cleaned = df["text"].pii.clean_pii("redact", cleaners=["email"])
        email_detected = df["text"].pii.detect_pii(cleaners=["email"])

        # Should only clean/detect emails
        assert "alice@test.com" not in email_cleaned.iloc[0]
        assert (
            "+44 20 1234 5678" in email_cleaned.iloc[0]
        )  # Phone should remain
        assert email_cleaned.iloc[1] == "NINO: AB123456C"  # NINO should remain

        # Detection should only find emails
        assert len(email_detected.iloc[0]) > 0  # Should detect email in 1st row
        detected_texts_row1 = [
            match["text"] for match in email_detected.iloc[0]
        ]
        assert "alice@test.com" in detected_texts_row1
        assert "+44 20 1234 5678" not in detected_texts_row1

        # Second row should have no detections (no email)
        assert len(email_detected.iloc[1]) == 0

    def test_namespace_custom_replacement_string(self):
        """Test namespace methods with custom replacement strings"""
        df = pd.DataFrame(
            {
                "text": [
                    "Email: test@example.com",
                    "No PII here",
                ]
            }
        )

        # Test with custom replacement string
        result = df["text"].pii.clean_pii(
            "replace", replace_string="***REMOVED***"
        )

        assert result.iloc[0] == "***REMOVED***"
        assert result.iloc[1] == "No PII here"

    def test_namespace_ignore_case_parameter(self):
        """Test namespace methods with ignore_case parameter"""
        df = pd.DataFrame(
            {
                "text": [
                    "EMAIL: TEST@EXAMPLE.COM",  # Uppercase email
                    "email: test@example.com",  # Lowercase email
                ]
            }
        )

        # Test with case sensitivity
        case_sensitive = df["text"].pii.clean_pii("redact", ignore_case=False)
        case_insensitive = df["text"].pii.clean_pii("redact", ignore_case=True)

        # Both should be cleaned when ignore_case=True (default behavior)
        assert "TEST@EXAMPLE.COM" not in case_insensitive.iloc[0]
        assert "test@example.com" not in case_insensitive.iloc[1]

        # Case sensitive should still work (exact behavior depends on patterns)
        # At minimum, verify the parameter doesn't cause errors
        assert isinstance(case_sensitive, pd.Series)
        assert len(case_sensitive) == 2

    def test_namespace_with_empty_series(self):
        """Test namespace methods with empty Series"""
        empty_series = pd.Series([], dtype=str, name="text")

        cleaned = empty_series.pii.clean_pii("redact")
        detected = empty_series.pii.detect_pii()

        assert len(cleaned) == 0
        assert len(detected) == 0
        assert isinstance(cleaned, pd.Series)
        assert isinstance(detected, pd.Series)

    def test_namespace_method_chaining(self):
        """Test that namespace methods can be chained with other pandas
        operations"""
        df = pd.DataFrame(
            {
                "text": [
                    "Contact john@example.com for help",
                    "My NINO is AB123456C",
                    "Clean text here",
                ],
                "category": ["support", "personal", "other"],
            }
        )

        # Chain namespace method with other pandas operations
        result = (
            df["text"]
            .pii.clean_pii("redact")
            .str.upper()
            .str.contains("REDACTED")
        )

        assert isinstance(result, pd.Series)
        assert result.iloc[0]  # Should contain "REDACTED"
        assert result.iloc[1]  # Should contain "REDACTED"
        assert not result.iloc[2]  # Should not contain "REDACTED"


class TestPandasNamespaceBatch:
    """The .pii accessor processes a Series in one batch call (#34)"""

    @pytest.mark.parametrize(
        "series",
        [
            pd.Series([], dtype=object),
            pd.Series([], dtype="string"),
            pd.Series([None, None]),
            pd.Series([pd.NA, pd.NA], dtype="string"),
        ],
        ids=["empty", "empty-string-dtype", "all-none", "all-na"],
    )
    def test_unknown_cleaner_raises_without_data(self, series):
        """A typo in cleaners is reported even if there's nothing to clean"""
        with pytest.raises(ValueError, match="Unknown cleaner"):
            series.pii.clean_pii("redact", cleaners=["emial"])
        with pytest.raises(ValueError, match="Unknown cleaner"):
            series.pii.detect_pii(cleaners=["emial"])

    @pytest.mark.parametrize(
        "series",
        [pd.Series([], dtype=object), pd.Series([None, None])],
        ids=["empty", "all-none"],
    )
    def test_invalid_cleaning_method_raises_without_data(self, series):
        with pytest.raises(ValueError, match="Invalid cleaning method"):
            series.pii.clean_pii("redcat")

    def test_nulls_are_returned_unchanged(self):
        series = pd.Series(["a@b.com", None, np.nan, "x"])
        cleaned = series.pii.clean_pii("redact")
        assert cleaned.iloc[0] == "[email-redacted]"
        assert cleaned.iloc[1] is None
        assert np.isnan(cleaned.iloc[2])
        assert cleaned.iloc[3] == "x"

        detected = series.pii.detect_pii()
        assert detected.tolist()[1:] == [[], [], []]

    def test_string_dtype_na(self):
        series = pd.Series(["a@b.com", pd.NA, "x"], dtype="string")
        cleaned = series.pii.clean_pii("redact")
        assert cleaned.iloc[0] == "[email-redacted]"
        assert cleaned.iloc[1] is pd.NA
        assert cleaned.iloc[2] == "x"
        assert series.pii.detect_pii().iloc[1] == []

    def test_index_and_name_preserved(self):
        series = pd.Series(["a@b.com", None, "y"], index=[30, 10, 20], name="t")
        for result in [series.pii.clean_pii("redact"), series.pii.detect_pii()]:
            assert list(result.index) == [30, 10, 20]
            assert result.name == "t"

    def test_results_match_cleaner_list_methods(self):
        """The accessor gives the same results as the batch Cleaner methods"""
        texts = [
            "Contact john@example.com",
            "NINO: AB-12-34-56-C",
            "Café at SW1A  1AA",
            "No PII here",
        ]
        series = pd.Series(texts)
        cleaner = Cleaner()
        assert series.pii.clean_pii("redact").tolist() == (
            cleaner.clean_pii_list(texts, "redact")
        )
        assert series.pii.detect_pii().tolist() == cleaner.detect_pii_list(
            texts
        )
