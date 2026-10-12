from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

import piicleaner

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
            function. Cleaner names are validated immediately, even if the
            Series is empty or all null.
            """
            if isinstance(cleaners, str):
                cleaners = [cleaners]

            not_null = self._obj.notna().tolist()
            texts = [
                v
                for v, ok in zip(self._obj.tolist(), not_null, strict=True)
                if ok
            ]
            batch = iter(
                piicleaner.detect_pii_with_cleaners_batch(
                    texts, cleaners, ignore_case
                )
            )
            results = [
                [
                    {"start": start, "end": end, "text": text, "type": pii_type}
                    for start, end, text, pii_type in next(batch)
                ]
                if ok
                else []
                for ok in not_null
            ]
            return pd.Series(
                results,
                index=self._obj.index,
                name=self._obj.name,
                dtype=object,
            )

        def clean_pii(
            self,
            cleaning: str,
            cleaners: str | list[str] = "all",
            ignore_case: bool = True,
            replace_string: str | None = None,
        ) -> pd.Series:
            """Clean PII from text.

            All non-null values are processed in one call to the batch Rust
            function; null values are returned unchanged. Cleaner names and the
            cleaning method are validated immediately, even if the Series is
            empty or all null.
            """
            if isinstance(cleaners, str):
                cleaners = [cleaners]

            values = self._obj.tolist()
            not_null = self._obj.notna().tolist()
            texts = [v for v, ok in zip(values, not_null, strict=True) if ok]
            batch = iter(
                piicleaner.clean_pii_with_cleaners_batch(
                    texts, cleaners, cleaning, ignore_case, replace_string
                )
            )
            results = [
                next(batch) if ok else v
                for v, ok in zip(values, not_null, strict=True)
            ]
            # Let pandas infer the dtype, as Series.apply does: object on
            # pandas 2, str on pandas 3
            return pd.Series(
                results, index=self._obj.index, name=self._obj.name
            )
