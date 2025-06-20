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
            """Detect PII in text and return matches as list of dicts."""

            if isinstance(cleaners, str):
                cleaners = [cleaners]

            def _convert_matches(text_val):
                if pd.isna(text_val):
                    return []
                matches = piicleaner.detect_pii_with_cleaners(
                    text_val, cleaners, ignore_case
                )
                # Convert tuples to dictionaries
                return [
                    {
                        "start": start,
                        "end": end,
                        "text": text,
                        "type": pii_type,
                    }
                    for start, end, text, pii_type in matches
                ]

            return self._obj.apply(_convert_matches)

        def clean_pii(
            self,
            cleaning: str,
            cleaners: str | list[str] = "all",
            ignore_case: bool = True,
            replace_string: str | None = None,
        ) -> pd.Series:
            """Clean PII from text."""

            if isinstance(cleaners, str):
                cleaners = [cleaners]

            def _clean_text(text_val):
                if pd.isna(text_val):
                    return text_val
                return piicleaner.clean_pii_with_cleaners(
                    text_val, cleaners, cleaning, ignore_case, replace_string
                )

            return self._obj.apply(_clean_text)
