"""Tests for Polars DataFrame integration functionality."""

import polars as pl
import pytest
from piicleaner import Cleaner


class TestPolarsDataFrameMethods:
    """Test Cleaner class DataFrame methods."""

    @pytest.fixture
    def sample_df(self):
        """Sample DataFrame with PII data for testing."""
        return pl.DataFrame(
            {
                "id": [1, 2, 3, 4],
                "text": [
                    "Contact john@example.com for help",
                    "My NINO is AB123456C",
                    "Call +44 20 7946 0958",
                    "No PII in this text",
                ],
                "category": ["email", "nino", "phone", "clean"],
            }
        )

    @pytest.fixture
    def cleaner(self):
        """Default cleaner instance."""
        return Cleaner()

    def test_clean_dataframe_redact(self, cleaner, sample_df):
        """Test cleaning DataFrame with redact method."""
        result = cleaner.clean_dataframe(
            sample_df, "text", "redact", "cleaned_text"
        )

        assert result.shape == (4, 4)  # Original columns + new column
        assert "cleaned_text" in result.columns

        cleaned_texts = result["cleaned_text"].to_list()
        assert "john@example.com" not in cleaned_texts[0]
        assert "AB123456C" not in cleaned_texts[1]
        assert "+44 20 7946 0958" not in cleaned_texts[2]
        assert cleaned_texts[3] == "No PII in this text"  # No change

    def test_clean_dataframe_replace(self, cleaner, sample_df):
        """Test cleaning DataFrame with replace method."""
        result = cleaner.clean_dataframe(
            sample_df, "text", "replace", "cleaned_text"
        )

        assert result.shape == (4, 4)
        cleaned_texts = result["cleaned_text"].to_list()

        # Replace method should change entire string if PII found
        assert cleaned_texts[0] != "Contact john@example.com for help"
        assert cleaned_texts[1] != "My NINO is AB123456C"
        assert cleaned_texts[2] != "Call +44 20 7946 0958"
        assert cleaned_texts[3] == "No PII in this text"  # No change

    def test_clean_dataframe_overwrite_column(self, cleaner, sample_df):
        """Test cleaning DataFrame by overwriting original column."""
        original_texts = sample_df["text"].to_list()
        result = cleaner.clean_dataframe(sample_df, "text", "redact")

        assert result.shape == sample_df.shape
        assert "text" in result.columns

        new_texts = result["text"].to_list()
        assert new_texts != original_texts
        assert "john@example.com" not in new_texts[0]

    def test_detect_dataframe(self, cleaner, sample_df):
        """Test PII detection in DataFrame."""
        result = cleaner.detect_dataframe(sample_df, "text")

        assert isinstance(result, pl.DataFrame)
        assert "row_index" in result.columns
        assert "start" in result.columns
        assert "end" in result.columns
        assert "text" in result.columns

        # Should detect PII in rows 0, 1, 2 but not 3
        row_indices = result["row_index"].to_list()
        assert 0 in row_indices  # email row
        assert 1 in row_indices  # nino row
        assert 2 in row_indices  # phone row
        # Row 3 might not be present if no PII detected

        pii_texts = result["text"].to_list()
        assert any("john@example.com" in text for text in pii_texts)
        assert any("AB123456C" in text for text in pii_texts)
        assert any("+44 20 7946 0958" in text for text in pii_texts)

    def test_clean_dataframe_invalid_column(self, cleaner, sample_df):
        """Test error when column doesn't exist."""
        with pytest.raises(ValueError, match="Column 'nonexistent' not found"):
            cleaner.clean_dataframe(sample_df, "nonexistent", "redact")

    def test_detect_dataframe_invalid_column(self, cleaner, sample_df):
        """Test error when column doesn't exist."""
        with pytest.raises(ValueError, match="Column 'nonexistent' not found"):
            cleaner.detect_dataframe(sample_df, "nonexistent")

    def test_clean_dataframe_invalid_df_type(self, cleaner):
        """Test error with non-DataFrame input."""
        with pytest.raises(TypeError, match="df must be a polars DataFrame"):
            cleaner.clean_dataframe(
                ["not", "a", "dataframe"], "text", "redact"
            )

    def test_detect_dataframe_invalid_df_type(self, cleaner):
        """Test error with non-DataFrame input."""
        with pytest.raises(TypeError, match="df must be a polars DataFrame"):
            cleaner.detect_dataframe({"not": "a dataframe"}, "text")


class TestPolarsNamespaceAPI:
    """Test Polars namespace API (.pii.* methods)."""

    @pytest.fixture
    def sample_df(self):
        """Sample DataFrame for namespace testing."""
        return pl.DataFrame(
            {
                "text": [
                    "Email: alice@company.com",
                    "Phone: +44 20 1234 5678",
                    "NINO: JK987654D",
                    "Clean text here",
                ]
            }
        )

    def test_namespace_clean_pii_redact(self, sample_df):
        """Test namespace .pii.clean_pii() with redact."""
        result = sample_df.with_columns(
            pl.col("text").pii.clean_pii("redact").alias("cleaned")
        )

        assert result.shape == (4, 2)
        assert "cleaned" in result.columns

        cleaned_texts = result["cleaned"].to_list()
        assert "alice@company.com" not in cleaned_texts[0]
        assert "+44 20 1234 5678" not in cleaned_texts[1]
        assert "JK987654D" not in cleaned_texts[2]
        assert cleaned_texts[3] == "Clean text here"

    def test_namespace_clean_pii_replace(self, sample_df):
        """Test namespace .pii.clean_pii() with replace."""
        result = sample_df.with_columns(
            pl.col("text").pii.clean_pii("replace").alias("cleaned")
        )

        cleaned_texts = result["cleaned"].to_list()
        original_texts = sample_df["text"].to_list()

        # Should change strings with PII
        assert cleaned_texts[0] != original_texts[0]
        assert cleaned_texts[1] != original_texts[1]
        assert cleaned_texts[2] != original_texts[2]
        assert cleaned_texts[3] == original_texts[3]  # No change

    def test_namespace_detect_pii(self, sample_df):
        """Test namespace .pii.detect_pii()."""
        result = sample_df.with_columns(
            pl.col("text").pii.detect_pii().alias("pii_matches")
        )

        assert result.shape == (4, 2)
        assert "pii_matches" in result.columns

        matches = result["pii_matches"].to_list()

        # Check that matches are returned as list of structs
        assert isinstance(matches[0], list)  # Email row should have matches
        assert isinstance(matches[1], list)  # Phone row should have matches
        assert isinstance(matches[2], list)  # NINO row should have matches
        assert matches[3] == []  # Clean text should have no matches

        # Check structure of matches
        if matches[0]:  # If email matches found
            match = matches[0][0]
            assert "start" in match
            assert "end" in match
            assert "text" in match

    def test_namespace_detect_pii_with_cleaners(self, sample_df):
        """Test namespace .pii.detect_pii_with_cleaners()."""
        result = sample_df.with_columns(
            pl.col("text")
            .pii.detect_pii_with_cleaners(["email"])
            .alias("email_matches")
        )

        matches = result["email_matches"].to_list()

        # Should only detect email, not phone or NINO
        assert len(matches[0]) >= 1  # Email row should have matches
        # Other rows might have no matches or fewer matches

        # Check that detected text contains email
        if matches[0]:
            email_match_text = matches[0][0]["text"]
            assert "@" in email_match_text

    def test_namespace_with_null_values(self):
        """Test namespace API handles null values correctly."""
        df = pl.DataFrame(
            {"text": ["Email: test@example.com", None, "Clean text"]}
        )

        result = df.with_columns(
            [
                pl.col("text").pii.clean_pii("redact").alias("cleaned"),
                pl.col("text").pii.detect_pii().alias("detected"),
            ]
        )

        cleaned = result["cleaned"].to_list()
        detected = result["detected"].to_list()

        assert cleaned[1] is None  # Null should remain null
        assert detected[1] is None  # Null should return None, not empty list

        assert "test@example.com" not in cleaned[0]
        assert cleaned[2] == "Clean text"


class TestPolarsEdgeCases:
    """Test edge cases and error conditions for Polars integration."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        cleaner = Cleaner()
        empty_df = pl.DataFrame({"text": []})

        cleaned = cleaner.clean_dataframe(empty_df, "text", "redact")
        detected = cleaner.detect_dataframe(empty_df, "text")

        assert cleaned.shape == (0, 1)
        # Empty DataFrame detection returns empty DataFrame with no columns
        assert detected.shape[0] == 0  # No rows
        # Column count may be 0 for empty results

    def test_vectorized_batch_processing(self):
        """Test vectorized DataFrame operations with larger dataset."""
        cleaner = Cleaner()
        # Now we can handle larger datasets efficiently with vectorization
        batch_data = ["Email: test@example.com"] * 200 + ["No PII"] * 200
        batch_df = pl.DataFrame({"text": batch_data})

        cleaned = cleaner.clean_dataframe(
            batch_df, "text", "redact", "cleaned"
        )
        detected = cleaner.detect_dataframe(batch_df, "text")

        assert cleaned.shape == (400, 2)
        assert detected.shape[0] >= 200  # Should detect PII in first 200 rows

        cleaned_texts = cleaned["cleaned"].to_list()
        # First 200 should be cleaned, last 200 unchanged
        assert "test@example.com" not in cleaned_texts[0]
        assert cleaned_texts[399] == "No PII"

    def test_multiple_columns_cleaning(self):
        """Test cleaning multiple columns."""
        df = pl.DataFrame(
            {
                "emails": ["Contact alice@test.com", "No email here"],
                "phones": ["Call +44 20 1234 5678", "No phone here"],
            }
        )

        # Clean both columns
        result = df.with_columns(
            [
                pl.col("emails").pii.clean_pii("redact").alias("clean_emails"),
                pl.col("phones").pii.clean_pii("redact").alias("clean_phones"),
            ]
        )

        assert result.shape == (2, 4)
        clean_emails = result["clean_emails"].to_list()
        clean_phones = result["clean_phones"].to_list()

        assert "alice@test.com" not in clean_emails[0]
        assert "+44 20 1234 5678" not in clean_phones[0]
        assert clean_emails[1] == "No email here"
        assert clean_phones[1] == "No phone here"

    def test_specific_cleaners_dataframe(self):
        """Test DataFrame methods with specific cleaners."""
        email_cleaner = Cleaner(["email"])
        df = pl.DataFrame(
            {
                "text": [
                    "Email alice@test.com and call +44 20 1234 5678",
                    "NINO: AB123456C",
                ]
            }
        )

        cleaned = email_cleaner.clean_dataframe(
            df, "text", "redact", "cleaned"
        )
        detected = email_cleaner.detect_dataframe(df, "text")

        cleaned_texts = cleaned["cleaned"].to_list()
        detected_texts = (
            detected["text"].to_list() if len(detected) > 0 else []
        )

        # Should only clean/detect emails
        assert "alice@test.com" not in cleaned_texts[0]
        assert "+44 20 1234 5678" in cleaned_texts[0]  # Phone should remain
        assert cleaned_texts[1] == "NINO: AB123456C"  # NINO should remain

        # Detection should only find emails
        if detected_texts:
            assert any("alice@test.com" in text for text in detected_texts)
            assert not any(
                "+44 20 1234 5678" in text for text in detected_texts
            )
            assert not any("AB123456C" in text for text in detected_texts)
