"""Pandas extensions for PII cleaning"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class PandasCleanerMixin:
    """Mixin class to add Pandas functionality to Cleaner"""

    def clean_pandas_dataframe(
        self,
        df: pd.DataFrame,
        column_name: str,
        cleaning: str,
        ignore_case: bool = True,
        new_column_name: str = None,
    ):
        """Clean PII in a Pandas DataFrame column

        :param df: Pandas DataFrame
        :param column_name: Name of the column to clean
        :param cleaning: Cleaning method ("redact" or "replace")
        :param ignore_case: Should we ignore case when detecting PII?
        :param new_column_name: Name for the new cleaned column. If
            None, overwrites original
        :return: DataFrame with cleaned column
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for DataFrame operations")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Use the clean_pii_list method which respects specific cleaners
        texts = df[column_name].tolist()
        # Handle null values - replace with empty strings for processing
        processed_texts = [
            str(text) if pd.notna(text) else "" for text in texts
        ]
        cleaned_texts = self.clean_pii_list(
            processed_texts, cleaning, ignore_case
        )

        # Restore null values in the results
        for i, original_text in enumerate(texts):
            if pd.isna(original_text):
                cleaned_texts[i] = original_text

        # Create new DataFrame with cleaned column
        result_df = df.copy()
        if new_column_name is None:
            new_column_name = column_name

        result_df[new_column_name] = cleaned_texts

        return result_df

    def detect_pandas_dataframe(
        self,
        df: pd.DataFrame,
        column_name: str,
        ignore_case: bool = True,
        new_column_name: str = None,
    ):
        """Detect PII in a Pandas DataFrame column

        :param df: Pandas DataFrame
        :param column_name: Name of the column to analyse
        :param ignore_case: Should we ignore case when detecting PII?
        :param new_column_name: Name for the new detection column. If
            None, uses "{column_name}_pii_detected"
        :return: DataFrame with detection results added as a list column
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for DataFrame operations")

        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Set default column name
        if new_column_name is None:
            new_column_name = f"{column_name}_pii_detected"

        # Get texts and use Cleaner's detect_pii_list method
        texts = df[column_name].tolist()
        # Handle null values - replace with empty strings for processing
        processed_texts = [
            str(text) if pd.notna(text) else "" for text in texts
        ]
        batch_results = self.detect_pii_list(processed_texts, ignore_case)

        # Set empty results for null values
        for i, original_text in enumerate(texts):
            if pd.isna(original_text):
                batch_results[i] = []

        # Create new DataFrame with detection results
        result_df = df.copy()
        result_df[new_column_name] = batch_results

        return result_df
