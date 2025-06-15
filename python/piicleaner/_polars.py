"""Polars extensions for PII cleaning"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl

try:
    import polars as pl

    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False


class PolarsCleanerMixin:
    """Mixin class to add Polars functionality to Cleaner"""

    def clean_dataframe(
        self,
        df: pl.DataFrame,
        column_name: str,
        cleaning: str,
        ignore_case: bool = True,
        new_column_name: str = None,
    ):
        """Clean PII in a Polars DataFrame column

        :param df: Polars DataFrame
        :param column_name: Name of the column to clean
        :param cleaning: Cleaning method ("redact" or "replace")
        :param ignore_case: Should we ignore case when detecting PII?
        :param new_column_name: Name for the new cleaned column. If
            None, overwrites original
        :return: DataFrame with cleaned column
        """
        if not POLARS_AVAILABLE:
            raise ImportError("polars is required for DataFrame operations")

        if not isinstance(df, pl.DataFrame):
            raise TypeError("df must be a polars DataFrame")

        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Use the clean_pii_list method which respects specific cleaners
        texts = df.get_column(column_name).to_list()
        cleaned_texts = self.clean_pii_list(texts, cleaning, ignore_case)

        # Create new DataFrame with cleaned column
        if new_column_name is None:
            new_column_name = column_name

        result_df = df.with_columns(
            pl.Series(name=new_column_name, values=cleaned_texts)
        )

        return result_df

    def detect_dataframe(
        self,
        df: pl.DataFrame,
        column_name: str,
        ignore_case: bool = True,
        new_column_name: str = None,
    ):
        """Detect PII in a Polars DataFrame column

        :param df: Polars DataFrame
        :param column_name: Name of the column to analyse
        :param ignore_case: Should we ignore case when detecting PII?
        :param new_column_name: Name for the new detection column. If
            None, uses "{column_name}_pii_detected"
        :return: DataFrame with detection results added as a list column
        """
        if not POLARS_AVAILABLE:
            raise ImportError("polars is required for DataFrame operations")

        if not isinstance(df, pl.DataFrame):
            raise TypeError("df must be a polars DataFrame")

        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Set default column name
        if new_column_name is None:
            new_column_name = f"{column_name}_pii_detected"

        # Get texts and use Cleaner's detect_pii_list method
        texts = df.get_column(column_name).to_list()
        batch_results = self.detect_pii_list(texts, ignore_case)

        # Convert to Polars list of structs format
        detection_results = []
        for matches in batch_results:
            # Convert each row's matches to list of dicts for Polars
            row_matches = [
                {
                    "start": match["start"],
                    "end": match["end"],
                    "text": match["text"],
                    "type": match["type"],
                }
                for match in matches
            ]
            detection_results.append(row_matches)

        # Add detection results as new column
        result_df = df.with_columns(
            pl.Series(
                name=new_column_name,
                values=detection_results,
                dtype=pl.List(
                    pl.Struct(
                        [
                            pl.Field("start", pl.Int64),
                            pl.Field("end", pl.Int64),
                            pl.Field("text", pl.String),
                            pl.Field("type", pl.String),
                        ]
                    )
                ),
            )
        )

        return result_df
