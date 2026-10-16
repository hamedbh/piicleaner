"""Polars extensions for PII cleaning"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl

try:
    import polars as pl

    from piicleaner._polars_plugin import _clean_pii_expr, _detect_pii_expr

    POLARS_AVAILABLE = True

    _DETECTION_DTYPE = pl.List(
        pl.Struct(
            [
                pl.Field("start", pl.Int64),
                pl.Field("end", pl.Int64),
                pl.Field("text", pl.String),
                pl.Field("type", pl.String),
            ]
        )
    )
except ImportError:
    POLARS_AVAILABLE = False


class PolarsCleanerMixin:
    """Mixin class to add Polars functionality to Cleaner"""

    def clean_dataframe(
        self,
        df: pl.DataFrame,
        column_name: str,
        cleaning: str,
        *,
        ignore_case: bool = True,
        new_column_name: str | None = None,
    ):
        """Clean PII in a Polars DataFrame column.

        Args:
            df (pl.DataFrame): Polars DataFrame.
            column_name (str): Name of the column to clean.
            cleaning (str): Cleaning method ("redact" or "replace").
            ignore_case (bool): Should we ignore case when detecting PII?
                Defaults to True.
            new_column_name (str | None): Name for the new cleaned column. If
                None, overwrites original. Defaults to None.

        Returns:
            pl.DataFrame: DataFrame with cleaned column.
        """
        if not POLARS_AVAILABLE:
            raise ImportError("polars is required for DataFrame operations")

        if not isinstance(df, pl.DataFrame):
            raise TypeError("df must be a polars DataFrame")

        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Overwrite the original column by default
        if new_column_name is None:
            new_column_name = column_name

        # Non-string columns are cleaned as their string form
        result_df = df.with_columns(
            _clean_pii_expr(
                pl.col(column_name).cast(pl.String),
                cleaning,
                self.cleaners,
                ignore_case,
                self.replace_string,
            ).alias(new_column_name)
        )

        return result_df

    def detect_dataframe(
        self,
        df: pl.DataFrame,
        column_name: str,
        *,
        ignore_case: bool = True,
        new_column_name: str | None = None,
    ):
        """Detect PII in a Polars DataFrame column.

        Args:
            df (pl.DataFrame): Polars DataFrame.
            column_name (str): Name of the column to analyse.
            ignore_case (bool): Should we ignore case when detecting PII?
                Defaults to True.
            new_column_name (str | None): Name for the new detection column. If
                None, uses "{column_name}_pii_detected". Defaults to None.

        Returns:
            pl.DataFrame: DataFrame with detection results added as a
                list column.
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

        # Null rows give an empty list of matches, not null
        detected = _detect_pii_expr(
            pl.col(column_name).cast(pl.String), self.cleaners, ignore_case
        )
        result_df = df.with_columns(
            pl.when(pl.col(column_name).is_null())
            .then(pl.lit([], dtype=_DETECTION_DTYPE))
            .otherwise(detected)
            .alias(new_column_name)
        )

        return result_df
