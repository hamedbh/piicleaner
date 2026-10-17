from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from piicleaner._types import Cleaning

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from piicleaner._pandas import _clean_series, _detect_series

if PANDAS_AVAILABLE:

    @pd.api.extensions.register_series_accessor("pii")
    class PIISeriesAccessor:
        """PII operations for Pandas Series."""

        def __init__(self, pandas_obj):
            self._obj = pandas_obj

        def detect_pii(
            self, cleaners: str | list[str] = "all", ignore_case: bool = True
        ) -> pd.Series:
            """Detect PII in text and return matches as list of dicts.

            All non-null values are processed in one call to the batch Rust
            function; null values give None. Cleaner names are validated
            immediately, even if the Series is empty or all null.

            Raises:
                TypeError: If the Series holds non-string values.
            """
            if isinstance(cleaners, str):
                cleaners = [cleaners]
            return _detect_series(self._obj, cleaners, ignore_case)

        def clean_pii(
            self,
            cleaning: Cleaning,
            cleaners: str | list[str] = "all",
            ignore_case: bool = True,
            replace_string: str | None = None,
        ) -> pd.Series:
            """Clean PII from text.

            All non-null values are processed in one call to the batch Rust
            function; null values are returned unchanged. Cleaner names and the
            cleaning method are validated immediately, even if the Series is
            empty or all null.

            Raises:
                TypeError: If the Series holds non-string values.
            """
            if isinstance(cleaners, str):
                cleaners = [cleaners]
            return _clean_series(
                self._obj, cleaning, cleaners, ignore_case, replace_string
            )
