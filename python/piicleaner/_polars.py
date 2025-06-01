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

        # Use the clean_list method which respects specific cleaners
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

        # Use vectorized detection for much better performance
        if len(df) == 0:
            # Return empty DataFrame with proper structure
            return pl.DataFrame(
                {"row_index": [], "start": [], "end": [], "text": []},
                schema={
                    "row_index": pl.Int64,
                    "start": pl.Int64,
                    "end": pl.Int64,
                    "text": pl.String,
                },
            )

        # Get texts and use vectorized detection
        texts = df[column_name].to_list()

        # Import and use vectorized function
        from piicleaner._internal import detect_pii_batch

        if self.cleaners == "all":
            batch_results = detect_pii_batch(texts)
        else:
            from piicleaner._internal import detect_pii_with_cleaners_batch

            batch_results = detect_pii_with_cleaners_batch(
                texts, self.cleaners
            )

        # Convert batch results to flat format
        results = []
        for row_idx, matches in enumerate(batch_results):
            for start, end, text in matches:
                results.append(
                    {
                        "row_index": row_idx,
                        "start": start,
                        "end": end,
                        "text": text,
                    }
                )

        return pl.DataFrame(results)
