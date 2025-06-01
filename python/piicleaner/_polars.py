"""Polars extensions for PII cleaning"""

try:
    import polars as pl

    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False


class PolarsCleanerMixin:
    """Mixin class to add Polars functionality to Cleaner"""

    def clean_dataframe(
        self, df, column_name, cleaning="redact", new_column_name=None
    ):
        """Clean PII in a Polars DataFrame column

        :param df: Polars DataFrame
        :param column_name: Name of the column to clean
        :param cleaning: Cleaning method ("redact" or "replace")
        :param new_column_name: Name for the new cleaned column. If None, overwrites original
        :return: DataFrame with cleaned column
        """
        if not POLARS_AVAILABLE:
            raise ImportError("polars is required for DataFrame operations")

        if not isinstance(df, pl.DataFrame):
            raise TypeError("df must be a polars DataFrame")

        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Clean the column using our existing clean_list method
        texts = df[column_name].to_list()
        cleaned_texts = self.clean_list(texts, cleaning)

        # Create new DataFrame with cleaned column
        if new_column_name is None:
            new_column_name = column_name

        result_df = df.with_columns(
            pl.Series(name=new_column_name, values=cleaned_texts)
        )

        return result_df

    def detect_dataframe(self, df, column_name):
        """Detect PII in a Polars DataFrame column

        :param df: Polars DataFrame
        :param column_name: Name of the column to analyze
        :return: DataFrame with PII detection results
        """
        if not POLARS_AVAILABLE:
            raise ImportError("polars is required for DataFrame operations")

        if not isinstance(df, pl.DataFrame):
            raise TypeError("df must be a polars DataFrame")

        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Detect PII in each row
        texts = df[column_name].to_list()
        results = []

        for i, text in enumerate(texts):
            pii_matches = self.detect_pii(text)
            for match in pii_matches:
                results.append(
                    {
                        "row_index": i,
                        "start": match["start"],
                        "end": match["end"],
                        "text": match["text"],
                    }
                )

        return pl.DataFrame(results)
