from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl
    from polars import Expr

try:
    import polars as pl
    from polars import Expr

    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False

import piicleaner

if POLARS_AVAILABLE:

    @pl.api.register_expr_namespace("pii")
    class PIIExprNamespace:
        """PII operations for Polars expressions."""

        def __init__(self, expr: Expr):
            self._expr = expr

        def detect_pii(
            self, cleaners: str | list[str] = "all", ignore_case: bool = True
        ) -> Expr:
            """Detect PII in text and return matches as list of structs."""

            if isinstance(cleaners, str):
                cleaners = [cleaners]

            def _convert_matches(text_val):
                if text_val is None:
                    return []
                matches = piicleaner.detect_pii_with_cleaners(
                    text_val, cleaners, ignore_case
                )
                # Convert tuples to dictionaries for Polars struct format
                return [
                    {
                        "start": start,
                        "end": end,
                        "text": text,
                        "type": pii_type,
                    }
                    for start, end, text, pii_type in matches
                ]

            return self._expr.map_elements(
                _convert_matches,
                return_dtype=pl.List(
                    pl.Struct(
                        [
                            pl.Field("start", pl.UInt32),
                            pl.Field("end", pl.UInt32),
                            pl.Field("text", pl.String),
                            pl.Field("type", pl.String),
                        ]
                    )
                ),
            )

        def clean_pii(
            self,
            cleaning: str,
            cleaners: str | list[str] = "all",
            ignore_case: bool = True,
            replace_string: str | None = None,
        ) -> Expr:
            """Clean PII from text."""

            if isinstance(cleaners, str):
                cleaners = [cleaners]

            def _clean_text(text_val):
                if text_val is None:
                    return None
                return piicleaner.clean_pii_with_cleaners(
                    text_val, cleaners, cleaning, ignore_case, replace_string
                )

            return self._expr.map_elements(_clean_text, return_dtype=pl.String)
