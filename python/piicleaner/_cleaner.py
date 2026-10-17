"""Main Cleaner class for PII detection and cleaning"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from piicleaner._internal import (
    clean_pii as _clean_pii,
    clean_pii_batch as _clean_pii_batch,
    clean_pii_with_cleaners as _clean_pii_with_cleaners,
    clean_pii_with_cleaners_batch as _clean_pii_with_cleaners_batch,
    detect_pii as _detect_pii,
    detect_pii_batch as _detect_pii_batch,
    detect_pii_with_cleaners as _detect_pii_with_cleaners,
    detect_pii_with_cleaners_batch as _detect_pii_with_cleaners_batch,
    get_available_cleaners,
)
from piicleaner._pandas import PANDAS_AVAILABLE, PandasCleanerMixin
from piicleaner._polars import POLARS_AVAILABLE, PolarsCleanerMixin

if TYPE_CHECKING:
    import pandas as pd
    import polars as pl

    from piicleaner._types import Cleaning

if PANDAS_AVAILABLE:
    import pandas as pd
if POLARS_AVAILABLE:
    import polars as pl

DataFrameT = TypeVar("DataFrameT", "pl.DataFrame", "pd.DataFrame")


class Cleaner(PolarsCleanerMixin, PandasCleanerMixin):
    """A Cleaner object contains methods to detect and clean Personal
    Identifiable Information (PII) from text data using regex patterns.

    Args:
        cleaners (str | list[str]): The cleaners to use. Default "all" uses all
            available cleaners. Available cleaners include: "email", "postcode",
            "telephone", "international-telephone", "nino", "address",
            "cash-amount", "case-id", "tag", "ip_address". Defaults to "all".
        replace_string (str | None): Custom replacement string for "replace"
            cleaning method. If None, uses default "[PII detected, text
            redacted]". Defaults to None.
        ignore_case (bool): Whether to ignore case when matching patterns.
            Used by every method unless the method is given its own
            `ignore_case`. Defaults to True.
    """

    def __init__(
        self,
        cleaners: str | list[str] = "all",
        replace_string: str | None = None,
        ignore_case: bool = True,
    ):
        """Cleaner initialisation.

        Args:
            cleaners (str | list[str]): PII types to detect/clean.
            replace_string (str | None): Custom replacement text for
                "replace" mode.
            ignore_case (bool): Default for every method's `ignore_case`.

        Raises:
            TypeError: If `cleaners` is not a string or list of strings.
            ValueError: If `cleaners` is an empty list, mixes "all" with
                other names, or contains a name not returned by
                `get_available_cleaners()`.
        """
        if isinstance(cleaners, str):
            if cleaners == "all":
                self.cleaners = ["all"]
            else:
                self.cleaners = [cleaners]
        elif isinstance(cleaners, list):
            self.cleaners = cleaners
        else:
            raise TypeError("`cleaners` must be a string or list of strings")

        # The Rust check raises ValueError for an empty list, "all" mixed
        # with other names, or unknown names
        _detect_pii_with_cleaners_batch([], self.cleaners, True)

        self.replace_string = replace_string
        self.ignore_case = ignore_case

    def _ignore_case(self, ignore_case: bool | None) -> bool:
        """A method's `ignore_case`, falling back to the Cleaner's"""
        return self.ignore_case if ignore_case is None else ignore_case

    def detect_pii(
        self, string: str, ignore_case: bool | None = None
    ) -> list[dict[str, str | int]]:
        """Detect PII in a string and return match information.

        Args:
            string (str): Text to analyse for PII.
            ignore_case (bool | None): Whether to ignore case when matching
                patterns. Defaults to the Cleaner's `ignore_case`.

        Returns:
            list[dict[str, str | int]]: List of dictionaries with keys 'start',
                'end', 'text', 'type'. 'start' and 'end' are character
                offsets, so ``string[start:end] == text``.
        """
        ignore_case = self._ignore_case(ignore_case)
        if self.cleaners == ["all"]:
            matches = _detect_pii(string, ignore_case)
        else:
            matches = _detect_pii_with_cleaners(
                string, self.cleaners, ignore_case
            )

        return [
            {"start": start, "end": end, "text": text, "type": pii_type}
            for start, end, text, pii_type in matches
        ]

    def detect_pii_list(
        self, texts: list[str], ignore_case: bool | None = None
    ) -> list[list[dict[str, str | int]]]:
        """Detect PII in a list of strings and return match information.

        Args:
            texts (list[str]): List of strings to analyse for PII.
            ignore_case (bool | None): Whether to ignore case when matching
                patterns. Defaults to the Cleaner's `ignore_case`.

        Returns:
            list[list[dict[str, str | int]]]: List of lists of dictionaries with
                keys 'start', 'end', 'text', 'type'. 'start' and 'end' are
                character offsets into the corresponding string.
        """
        ignore_case = self._ignore_case(ignore_case)
        if self.cleaners == ["all"]:
            matches = _detect_pii_batch(texts, ignore_case)
        else:
            matches = _detect_pii_with_cleaners_batch(
                texts, self.cleaners, ignore_case
            )

        return [
            [
                {"start": start, "end": end, "text": text, "type": pii_type}
                for start, end, text, pii_type in match
            ]
            for match in matches
        ]

    def clean_pii(
        self,
        text: str,
        cleaning: Cleaning,
        ignore_case: bool | None = None,
    ) -> str:
        """Clean PII from a string.

        Args:
            text (str): Text to clean.
            cleaning (Literal["redact", "replace"]): Cleaning method.
            ignore_case (bool | None): Whether to ignore case when matching
                patterns. Defaults to the Cleaner's `ignore_case`.

        Returns:
            str: Cleaned text with PII removed or redacted.
        """
        ignore_case = self._ignore_case(ignore_case)
        if self.cleaners == ["all"]:
            return _clean_pii(text, cleaning, ignore_case, self.replace_string)
        else:
            return _clean_pii_with_cleaners(
                text, self.cleaners, cleaning, ignore_case, self.replace_string
            )

    def clean_pii_list(
        self,
        texts: list[str],
        cleaning: Cleaning,
        ignore_case: bool | None = None,
    ) -> list[str]:
        """Clean PII from a list of strings.

        Args:
            texts (list[str]): List of strings to clean.
            cleaning (Literal["redact", "replace"]): Cleaning method.
            ignore_case (bool | None): Whether to ignore case when matching
                patterns. Defaults to the Cleaner's `ignore_case`.

        Returns:
            list[str]: List of cleaned strings.
        """
        ignore_case = self._ignore_case(ignore_case)
        if self.cleaners == ["all"]:
            return _clean_pii_batch(
                texts, cleaning, ignore_case, self.replace_string
            )
        else:
            return _clean_pii_with_cleaners_batch(
                texts,
                self.cleaners,
                cleaning,
                ignore_case,
                self.replace_string,
            )

    def clean_dataframe(
        self,
        df: DataFrameT,
        column_name: str,
        cleaning: Cleaning,
        *,
        ignore_case: bool | None = None,
        new_column_name: str | None = None,
    ) -> DataFrameT:
        """Clean PII in a column of a Polars or pandas DataFrame.

        Polars columns are cleaned in Rust by the Polars plugin; pandas
        columns in one batch call. Null values stay null.

        Args:
            df (pl.DataFrame | pd.DataFrame): The DataFrame.
            column_name (str): Name of the column to clean.
            cleaning (Literal["redact", "replace"]): Cleaning method.
            ignore_case (bool | None): Whether to ignore case when matching
                patterns. Defaults to the Cleaner's `ignore_case`.
            new_column_name (str | None): Name for the cleaned column. If
                None, overwrites the original. Defaults to None.

        Returns:
            pl.DataFrame | pd.DataFrame: A DataFrame of the same type with the
                cleaned column.

        Raises:
            TypeError: If `df` is not a Polars or pandas DataFrame, or the
                column holds non-string values.
            ValueError: If the column is not in the DataFrame.
        """
        ignore_case = self._ignore_case(ignore_case)
        if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
            return self._clean_polars_dataframe(
                df, column_name, cleaning, ignore_case, new_column_name
            )
        if PANDAS_AVAILABLE and isinstance(df, pd.DataFrame):
            return self._clean_pandas_dataframe(
                df, column_name, cleaning, ignore_case, new_column_name
            )
        raise TypeError("df must be a Polars or pandas DataFrame")

    def detect_dataframe(
        self,
        df: DataFrameT,
        column_name: str,
        *,
        ignore_case: bool | None = None,
        new_column_name: str | None = None,
    ) -> DataFrameT:
        """Detect PII in a column of a Polars or pandas DataFrame.

        Each row of the new column is a list of matches with keys 'start',
        'end', 'text' and 'type', where 'start' and 'end' are character
        offsets. Null rows give null. In Polars the column has dtype
        ``list[struct{start: Int64, end: Int64, text: String, type: String}]``;
        in pandas it holds lists of dicts.

        Args:
            df (pl.DataFrame | pd.DataFrame): The DataFrame.
            column_name (str): Name of the column to analyse.
            ignore_case (bool | None): Whether to ignore case when matching
                patterns. Defaults to the Cleaner's `ignore_case`.
            new_column_name (str | None): Name for the detection column. If
                None, uses "{column_name}_pii_detected". Defaults to None.

        Returns:
            pl.DataFrame | pd.DataFrame: A DataFrame of the same type with the
                detection column added.

        Raises:
            TypeError: If `df` is not a Polars or pandas DataFrame, or the
                column holds non-string values.
            ValueError: If the column is not in the DataFrame.
        """
        ignore_case = self._ignore_case(ignore_case)
        if POLARS_AVAILABLE and isinstance(df, pl.DataFrame):
            return self._detect_polars_dataframe(
                df, column_name, ignore_case, new_column_name
            )
        if PANDAS_AVAILABLE and isinstance(df, pd.DataFrame):
            return self._detect_pandas_dataframe(
                df, column_name, ignore_case, new_column_name
            )
        raise TypeError("df must be a Polars or pandas DataFrame")

    @staticmethod
    def get_available_cleaners() -> list[str]:
        """Get list of available cleaner names.

        Returns:
            list[str]: Sorted list of available cleaner names.
        """
        return sorted(get_available_cleaners())
