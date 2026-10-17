"""Tests that detection offsets index the original Python string.

The Rust core works in UTF-8 byte offsets; these tests check that every
Python entry point returns character offsets instead, so that
``text[match["start"]:match["end"]] == match["text"]`` holds for non-ASCII
text.
"""

import pandas as pd
import polars as pl
import pytest
from piicleaner import (
    Cleaner,
    detect_pii,
    detect_pii_batch,
    detect_pii_with_cleaners,
    detect_pii_with_cleaners_batch,
)

# Non-ASCII text before, around and inside matches: 2-byte (é, £), 3-byte
# (CJK), 4-byte (emoji) characters, and a combining accent (two code points)
TEXTS = [
    "Café owner: test@example.com",
    "£100 paid by john@example.com",
    "😀 call 07700 900123 😀 or email a@b.com",
    "東京 office: SW1A 1AA, NINO AB123456C",
    "Café at 192.168.1.1 then £1,500",
    "No PII here, just ünïcödé",
    "Plain ASCII: test@example.com",
]


def assert_offsets_slice_text(text, matches):
    for match in matches:
        assert text[match["start"] : match["end"]] == match["text"], (
            text,
            match,
        )


def tuples_to_dicts(matches):
    return [
        {"start": start, "end": end, "text": text, "type": pii_type}
        for start, end, text, pii_type in matches
    ]


class TestCharacterOffsets:
    @pytest.mark.parametrize("text", TEXTS)
    def test_cleaner_detect_pii(self, text):
        assert_offsets_slice_text(text, Cleaner().detect_pii(text))

    @pytest.mark.parametrize("text", TEXTS)
    def test_cleaner_detect_pii_specific_cleaners(self, text):
        cleaner = Cleaner(["email", "cash-amount", "postcode"])
        assert_offsets_slice_text(text, cleaner.detect_pii(text))

    def test_cleaner_detect_pii_list(self):
        for cleaners in ["all", ["email", "nino", "telephone"]]:
            results = Cleaner(cleaners).detect_pii_list(TEXTS)
            for text, matches in zip(TEXTS, results, strict=True):
                assert_offsets_slice_text(text, matches)

    @pytest.mark.parametrize("text", TEXTS)
    def test_module_level_functions(self, text):
        assert_offsets_slice_text(text, tuples_to_dicts(detect_pii(text)))
        assert_offsets_slice_text(
            text,
            tuples_to_dicts(detect_pii_with_cleaners(text, ["email"])),
        )

    def test_module_level_batch_functions(self):
        for results in [
            detect_pii_batch(TEXTS),
            detect_pii_with_cleaners_batch(TEXTS, ["email", "postcode"]),
        ]:
            for text, matches in zip(TEXTS, results, strict=True):
                assert_offsets_slice_text(text, tuples_to_dicts(matches))

    def test_known_offsets(self):
        """Pin exact values, not just self-consistency."""
        matches = Cleaner(["email"]).detect_pii("Café owner: test@example.com")
        assert matches == [
            {
                "start": 12,
                "end": 28,
                "text": "test@example.com",
                "type": "email",
            }
        ]

    def test_polars_detect_dataframe(self):
        df = pl.DataFrame({"text": TEXTS})
        result = Cleaner().detect_dataframe(df, "text")
        for text, matches in zip(
            TEXTS, result["text_pii_detected"].to_list(), strict=True
        ):
            assert_offsets_slice_text(text, matches)

    def test_polars_namespace(self):
        df = pl.DataFrame({"text": TEXTS})
        result = df.select(pl.col("text").pii.detect_pii().alias("pii"))
        for text, matches in zip(TEXTS, result["pii"].to_list(), strict=True):
            assert_offsets_slice_text(text, matches)

    def test_pandas_detect_dataframe(self):
        df = pd.DataFrame({"text": TEXTS})
        result = Cleaner().detect_dataframe(df, "text")
        for text, matches in zip(
            TEXTS, result["text_pii_detected"], strict=True
        ):
            assert_offsets_slice_text(text, matches)

    def test_pandas_accessor(self):
        series = pd.Series(TEXTS)
        for text, matches in zip(TEXTS, series.pii.detect_pii(), strict=True):
            assert_offsets_slice_text(text, matches)
