"""Tests for Polars namespace API functionality"""

import pytest

# Skip all tests if polars is not available
pytest.importorskip("polars")

import piicleaner
import polars as pl
from piicleaner import Cleaner


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
        assert cleaned_texts[0] == "[PII detected, text redacted]"

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

    def test_namespace_invalid_cleaning_method(self):
        """Test namespace raises an error for invalid cleaning method"""
        df = pl.DataFrame({"text": ["Email: john@example.com"]})

        # Invalid cleaning method should raise an exception
        with pytest.raises(ValueError, match="Invalid cleaning method"):
            df.with_columns(
                pl.col("text").pii.clean_pii("invalid_method").alias("cleaned")
            )

    def test_invalid_cleaning_method_variations(self):
        """Test various invalid cleaning method inputs"""
        df = pl.DataFrame({"text": ["Email: john@example.com"]})

        invalid_methods = ["REPLACE", "REDACT", "remove", "mask", "", "delete"]

        for invalid_method in invalid_methods:
            with pytest.raises(ValueError, match="Invalid cleaning method"):
                df.with_columns(
                    pl.col("text")
                    .pii.clean_pii(invalid_method)
                    .alias("cleaned")
                )

    def test_valid_cleaning_methods_case_sensitivity(self):
        """Test that only exact case matches work for cleaning methods"""
        df = pl.DataFrame({"text": ["Email: john@example.com"]})

        # These should all fail (case sensitivity)
        invalid_cases = ["Replace", "REPLACE", "Redact", "REDACT"]

        for invalid_case in invalid_cases:
            with pytest.raises(ValueError, match="Invalid cleaning method"):
                df.with_columns(
                    pl.col("text").pii.clean_pii(invalid_case).alias("cleaned")
                )

    def test_empty_and_none_cleaning_method(self):
        """Test edge cases for cleaning method parameter"""
        df = pl.DataFrame({"text": ["Email: john@example.com"]})

        # Empty string
        with pytest.raises(ValueError, match="Invalid cleaning method"):
            df.with_columns(pl.col("text").pii.clean_pii("").alias("cleaned"))

        # None should also fail if passed somehow
        with pytest.raises((ValueError, TypeError)):
            df.with_columns(pl.col("text").pii.clean_pii(None).alias("cleaned"))


class TestPolarsPlugin:
    """The namespace and DataFrame methods run as a native Polars plugin"""

    TEXTS = [
        "Contact a@b.com",
        None,
        "No PII here",
        "Café a@b.com and AB123456C",
        "東京 W1 2BC £1,500",
        "",
    ]

    @staticmethod
    def _expected_detect(texts, cleaners=None):
        return [
            None
            if t is None
            else [
                {"start": s, "end": e, "text": x, "type": y}
                for s, e, x, y in (
                    piicleaner.detect_pii(t)
                    if cleaners is None
                    else piicleaner.detect_pii_with_cleaners(t, cleaners)
                )
            ]
            for t in texts
        ]

    def test_results_match_list_functions(self):
        df = pl.DataFrame({"t": self.TEXTS}, schema={"t": pl.String})
        out = df.select(
            clean=pl.col("t").pii.clean_pii("redact"),
            detect=pl.col("t").pii.detect_pii(),
        )
        assert out["clean"].to_list() == [
            None if t is None else piicleaner.clean_pii(t, "redact")
            for t in self.TEXTS
        ]
        assert out["detect"].to_list() == self._expected_detect(self.TEXTS)

    def test_offsets_are_characters(self):
        df = pl.DataFrame({"t": ["Café a@b.com"]})
        (match,) = df.select(pl.col("t").pii.detect_pii())["t"][0]
        assert "Café a@b.com"[match["start"] : match["end"]] == "a@b.com"

    def test_detection_dtype_is_the_same_for_both_apis(self):
        """Regression test for #35: offsets are Int64 in both APIs"""
        df = pl.DataFrame({"t": ["a@b.com"]})
        expected = pl.List(
            pl.Struct(
                {
                    "start": pl.Int64,
                    "end": pl.Int64,
                    "text": pl.String,
                    "type": pl.String,
                }
            )
        )
        namespace = df.select(pl.col("t").pii.detect_pii())["t"]
        method = Cleaner().detect_dataframe(df, "t")["t_pii_detected"]
        assert namespace.dtype == expected
        assert method.dtype == expected

    def test_lazy_frame(self):
        lf = pl.LazyFrame({"t": self.TEXTS}, schema={"t": pl.String})
        out = lf.select(
            clean=pl.col("t").pii.clean_pii("replace", replace_string="X"),
            detect=pl.col("t").pii.detect_pii(["email"]),
        ).collect()
        assert out["clean"].to_list() == [
            None
            if t is None
            else piicleaner.clean_pii(t, "replace", replace_string="X")
            for t in self.TEXTS
        ]
        assert out["detect"].to_list() == self._expected_detect(
            self.TEXTS, ["email"]
        )

    def test_multiple_chunks(self):
        df = pl.DataFrame({"t": self.TEXTS}, schema={"t": pl.String})
        chunked = pl.concat([df, df], rechunk=False)
        assert chunked["t"].n_chunks() == 2
        out = chunked.select(pl.col("t").pii.clean_pii("redact"))["t"]
        assert out.to_list() == (
            df.select(pl.col("t").pii.clean_pii("redact"))["t"].to_list() * 2
        )

    def test_empty_and_all_null_columns(self):
        for values in ([], [None, None]):
            df = pl.DataFrame({"t": values}, schema={"t": pl.String})
            out = df.select(
                clean=pl.col("t").pii.clean_pii("redact"),
                detect=pl.col("t").pii.detect_pii(),
            )
            assert out["clean"].to_list() == values
            assert out["detect"].to_list() == values

    @pytest.mark.parametrize(
        "build",
        [
            lambda: pl.col("t").pii.clean_pii("redact", cleaners="nope"),
            lambda: pl.col("t").pii.detect_pii(["email", "nope"]),
        ],
    )
    def test_unknown_cleaner_raises_when_expression_is_built(self, build):
        with pytest.raises(ValueError, match="Unknown cleaner"):
            build()

    @pytest.mark.parametrize(
        "build",
        [
            lambda: pl.col("t").pii.clean_pii("redact", cleaners=[]),
            lambda: pl.col("t").pii.detect_pii([]),
            lambda: pl.col("t").pii.clean_pii(
                "redact", cleaners=["all", "email"]
            ),
            lambda: pl.col("t").pii.detect_pii(["all", "email"]),
        ],
    )
    def test_invalid_cleaner_list_raises_when_expression_is_built(self, build):
        """An empty list, or "all" mixed with other names, raises (#53)"""
        with pytest.raises(ValueError, match="No cleaners|can't be combined"):
            build()

    def test_dataframe_methods_use_cleaner_settings(self):
        cleaner = Cleaner(cleaners=["email"], replace_string="X")
        df = pl.DataFrame({"t": ["a@b.com and AB123456C", None]})
        cleaned = cleaner.clean_dataframe(df, "t", "replace")["t"]
        assert cleaned.to_list() == ["X", None]
        detected = cleaner.detect_dataframe(df, "t")["t_pii_detected"]
        assert [[m["type"] for m in row] for row in detected] == [["email"], []]

    def test_clean_dataframe_casts_non_string_columns(self):
        df = pl.DataFrame({"n": [1234567890, None]})
        cleaned = Cleaner().clean_dataframe(df, "n", "redact")["n"]
        assert cleaned.dtype == pl.String
        assert cleaned.to_list() == [
            piicleaner.clean_pii("1234567890", "redact"),
            None,
        ]
