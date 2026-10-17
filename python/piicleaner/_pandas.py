"""Pandas extensions for PII cleaning"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from piicleaner._types import Cleaning

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from piicleaner._internal import (
    clean_pii_with_cleaners_batch,
    detect_pii_with_cleaners_batch,
)


def _check_not_categorical(series: pd.Series) -> None:
    if isinstance(series.dtype, pd.CategoricalDtype):
        raise _non_string_error(series, "category values")


def _non_string_error(series: pd.Series, found: str) -> TypeError:
    return TypeError(
        f"piicleaner only works on strings, but '{series.name}' "
        f"(dtype {series.dtype}) contains {found}. If it holds text, "
        "convert it to strings first"
    )


def _non_null_texts(series: pd.Series) -> tuple[list, list[bool]]:
    """The Series values and which of them are not null"""
    _check_not_categorical(series)
    values = series.tolist()
    not_null = series.notna().tolist()
    return values, not_null


def _batch(series: pd.Series, values: list, not_null: list[bool], call):
    """Run a batch Rust function on the non-null values only. Rust rejects
    anything that isn't a str; find the first such value for the error."""
    texts = [v for v, ok in zip(values, not_null, strict=True) if ok]
    try:
        return call(texts)
    except TypeError:
        bad = next((v for v in texts if not isinstance(v, str)), None)
        if bad is None:
            raise
        raise _non_string_error(
            series, f"{type(bad).__name__} values such as {bad!r}"
        ) from None


def _clean_series(
    series: pd.Series,
    cleaning: Cleaning,
    cleaners: list[str],
    ignore_case: bool,
    replace_string: str | None,
) -> pd.Series:
    """Clean PII from a Series of strings in one batch call.

    Nulls are returned unchanged. Cleaner names and the cleaning method are
    validated even if the Series is empty or all null.
    """
    values, not_null = _non_null_texts(series)
    batch = iter(
        _batch(
            series,
            values,
            not_null,
            lambda texts: clean_pii_with_cleaners_batch(
                texts, cleaners, cleaning, ignore_case, replace_string
            ),
        )
    )
    results = [
        next(batch) if ok else v for v, ok in zip(values, not_null, strict=True)
    ]
    # Let pandas infer the dtype, as Series.apply does: object on pandas 2,
    # str on pandas 3
    return pd.Series(results, index=series.index, name=series.name)


def _detect_series(
    series: pd.Series, cleaners: list[str], ignore_case: bool
) -> pd.Series:
    """Detect PII in a Series of strings in one batch call.

    Each row is a list of ``{start, end, text, type}`` dicts with character
    offsets. Null rows give None. Cleaner names are validated even if the
    Series is empty or all null.
    """
    values, not_null = _non_null_texts(series)
    batch = iter(
        _batch(
            series,
            values,
            not_null,
            lambda texts: detect_pii_with_cleaners_batch(
                texts, cleaners, ignore_case
            ),
        )
    )
    results = [
        [
            {"start": start, "end": end, "text": text, "type": pii_type}
            for start, end, text, pii_type in next(batch)
        ]
        if ok
        else None
        for ok in not_null
    ]
    return pd.Series(
        results, index=series.index, name=series.name, dtype=object
    )


def _check_column(df: pd.DataFrame, column_name: str) -> None:
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in DataFrame")


class PandasCleanerMixin:
    """Mixin class to add Pandas functionality to Cleaner"""

    def _clean_pandas_dataframe(
        self,
        df: pd.DataFrame,
        column_name: str,
        cleaning: Cleaning,
        ignore_case: bool,
        new_column_name: str | None,
    ) -> pd.DataFrame:
        _check_column(df, column_name)
        result_df = df.copy()
        if new_column_name is None:
            new_column_name = column_name
        result_df[new_column_name] = _clean_series(
            df[column_name],
            cleaning,
            self.cleaners,
            ignore_case,
            self.replace_string,
        )
        return result_df

    def _detect_pandas_dataframe(
        self,
        df: pd.DataFrame,
        column_name: str,
        ignore_case: bool,
        new_column_name: str | None,
    ) -> pd.DataFrame:
        _check_column(df, column_name)
        result_df = df.copy()
        if new_column_name is None:
            new_column_name = f"{column_name}_pii_detected"
        result_df[new_column_name] = _detect_series(
            df[column_name], self.cleaners, ignore_case
        )
        return result_df

    def clean_pandas_dataframe(
        self,
        df: pd.DataFrame,
        column_name: str,
        cleaning: Cleaning,
        *,
        ignore_case: bool | None = None,
        new_column_name: str | None = None,
    ) -> pd.DataFrame:
        """Clean PII in a Pandas DataFrame column.

        .. deprecated:: 0.7.0
            Use :meth:`clean_dataframe`, which takes pandas and Polars
            DataFrames. This method will be removed in 0.8.0.
        """
        warnings.warn(
            "clean_pandas_dataframe() is deprecated and will be removed in "
            "0.8.0. Use clean_dataframe(), which takes pandas and Polars "
            "DataFrames",
            DeprecationWarning,
            stacklevel=2,
        )
        if not PANDAS_AVAILABLE or not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")
        return self.clean_dataframe(
            df,
            column_name,
            cleaning,
            ignore_case=ignore_case,
            new_column_name=new_column_name,
        )

    def detect_pandas_dataframe(
        self,
        df: pd.DataFrame,
        column_name: str,
        *,
        ignore_case: bool | None = None,
        new_column_name: str | None = None,
    ) -> pd.DataFrame:
        """Detect PII in a Pandas DataFrame column.

        .. deprecated:: 0.7.0
            Use :meth:`detect_dataframe`, which takes pandas and Polars
            DataFrames. This method will be removed in 0.8.0.
        """
        warnings.warn(
            "detect_pandas_dataframe() is deprecated and will be removed in "
            "0.8.0. Use detect_dataframe(), which takes pandas and Polars "
            "DataFrames",
            DeprecationWarning,
            stacklevel=2,
        )
        if not PANDAS_AVAILABLE or not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")
        return self.detect_dataframe(
            df,
            column_name,
            ignore_case=ignore_case,
            new_column_name=new_column_name,
        )
