"""Tests for Polars namespace API functionality"""

import piicleaner  # noqa: F401
import polars as pl


class TestPolarsNamespace:
    """Test the .pii namespace extension for Polars"""

    def test_namespace_clean_pii_redact(self):
        """Test .pii.clean_pii() with redact mode"""
        df = pl.DataFrame(
            {
                "text": [
                    "Contact john@example.com",
                    "My NINO is AB123456C",
                    "Cost was £1,500",
                    "No PII here",
                ]
            }
        )

        result = df.with_columns(
            pl.col("text").pii.clean_pii("redact").alias("cleaned_text")
        )

        # Check that we have the cleaned_text column
        assert "cleaned_text" in result.columns

        cleaned_texts = result["cleaned_text"].to_list()

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
        df = pl.DataFrame(
            {
                "text": [
                    "Contact john@example.com",
                    "No PII here",
                ]
            }
        )

        result = df.with_columns(
            pl.col("text").pii.clean_pii("replace").alias("cleaned_text")
        )

        cleaned_texts = result["cleaned_text"].to_list()

        # Text with PII should be replaced entirely
        assert cleaned_texts[0] == "[PII detected, comment redacted]"

        # Clean text should remain unchanged
        assert cleaned_texts[1] == "No PII here"

    def test_namespace_detect_pii(self):
        """Test .pii.detect_pii() namespace method"""
        df = pl.DataFrame(
            {
                "text": [
                    "Contact john@example.com",
                    "My NINO is AB123456C",
                    "No PII here",
                ]
            }
        )

        result = df.with_columns(
            pl.col("text").pii.detect_pii().alias("pii_found")
        )

        # Check that we have the pii_found column
        assert "pii_found" in result.columns

        pii_results = result["pii_found"].to_list()

        # First text should have detected PII (email)
        assert len(pii_results[0]) >= 1
        email_found = any(
            "john@example.com" in str(match) for match in pii_results[0]
        )
        assert email_found

        # Second text should have detected PII (NINO)
        assert len(pii_results[1]) >= 1
        nino_found = any("AB123456C" in str(match) for match in pii_results[1])
        assert nino_found

        # Third text should have no PII detected
        assert len(pii_results[2]) == 0

    def test_namespace_with_multiple_columns(self):
        """Test namespace methods work with multiple text columns"""
        df = pl.DataFrame(
            {
                "text1": ["Email: john@example.com", "No PII here"],
                "text2": ["NINO: AB123456C", "Clean text"],
            }
        )

        result = df.with_columns(
            [
                pl.col("text1").pii.clean_pii("redact").alias("cleaned1"),
                pl.col("text2").pii.clean_pii("redact").alias("cleaned2"),
            ]
        )

        # Check both columns were processed
        assert "cleaned1" in result.columns
        assert "cleaned2" in result.columns

        # Verify cleaning worked
        assert "john@example.com" not in result["cleaned1"][0]
        assert "AB123456C" not in result["cleaned2"][0]
        assert result["cleaned1"][1] == "No PII here"
        assert result["cleaned2"][1] == "Clean text"

    def test_namespace_error_handling(self):
        """Test namespace handles invalid cleaning methods gracefully"""
        df = pl.DataFrame({"text": ["Email: john@example.com"]})

        # Invalid cleaning method should default to redact
        result = df.with_columns(
            pl.col("text").pii.clean_pii("invalid_method").alias("cleaned")
        )

        cleaned_text = result["cleaned"][0]
        assert "john@example.com" not in cleaned_text
        assert "-" in cleaned_text  # Should use redact as default
