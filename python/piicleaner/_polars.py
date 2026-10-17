"""Polars extensions for PII cleaning"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl

    from piicleaner._types import Cleaning

try:
    import polars as pl

    from piicleaner._polars_plugin import _clean_pii_expr, _detect_pii_expr

    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False


def _check_column(df: pl.DataFrame, column_name: str) -> None:
    """The column must exist and hold strings. An all-null column has dtype
    Null, and is accepted."""
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in DataFrame")
    dtype = df.schema[column_name]
    if dtype not in (pl.String, pl.Null):
        raise TypeError(
            f"piicleaner only works on strings, but column '{column_name}' "
            f"has dtype {dtype}. If it holds text, cast it with "
            ".cast(pl.String) first"
        )


class PolarsCleanerMixin:
    """Mixin class to add Polars functionality to Cleaner"""

    def _clean_polars_dataframe(
        self,
        df: pl.DataFrame,
        column_name: str,
        cleaning: Cleaning,
        ignore_case: bool,
        new_column_name: str | None,
    ) -> pl.DataFrame:
        _check_column(df, column_name)
        return df.with_columns(
            _clean_pii_expr(
                pl.col(column_name),
                cleaning,
                self.cleaners,
                ignore_case,
                self.replace_string,
            ).alias(column_name if new_column_name is None else new_column_name)
        )

    def _detect_polars_dataframe(
        self,
        df: pl.DataFrame,
        column_name: str,
        ignore_case: bool,
        new_column_name: str | None,
    ) -> pl.DataFrame:
        _check_column(df, column_name)
        return df.with_columns(
            _detect_pii_expr(
                pl.col(column_name), self.cleaners, ignore_case
            ).alias(
                f"{column_name}_pii_detected"
                if new_column_name is None
                else new_column_name
            )
        )
