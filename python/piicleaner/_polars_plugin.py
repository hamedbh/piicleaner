import polars as pl
from polars import Expr

import piicleaner


@pl.api.register_expr_namespace("pii")
class PIIExprNamespace:
    """PII operations for Polars expressions."""

    def __init__(self, expr: Expr):
        self._expr = expr

    def detect_pii(self) -> Expr:
        """Detect PII in text and return matches as list of structs."""

        def _convert_matches(text_val):
            if text_val is None:
                return []
            matches = piicleaner.detect_pii(text_val)
            # Convert tuples to dictionaries for Polars struct format
            return [
                {"start": start, "end": end, "text": text}
                for start, end, text in matches
            ]

        return self._expr.map_elements(
            _convert_matches,
            return_dtype=pl.List(
                pl.Struct(
                    [
                        pl.Field("start", pl.UInt32),
                        pl.Field("end", pl.UInt32),
                        pl.Field("text", pl.String),
                    ]
                )
            ),
        )

    def clean_pii(self, method: str = "redact") -> Expr:
        """Clean PII from text."""

        def _clean_text(text_val):
            if text_val is None:
                return None
            return piicleaner.clean_pii(text_val, method)

        return self._expr.map_elements(_clean_text, return_dtype=pl.String)

    def detect_pii_with_cleaners(self, cleaners: list[str]) -> Expr:
        """Detect PII using specific cleaners."""

        def _convert_matches_with_cleaners(text_val):
            if text_val is None:
                return []
            matches = piicleaner.detect_pii_with_cleaners(text_val, cleaners)
            return [
                {"start": start, "end": end, "text": text}
                for start, end, text in matches
            ]

        return self._expr.map_elements(
            _convert_matches_with_cleaners,
            return_dtype=pl.List(
                pl.Struct(
                    [
                        pl.Field("start", pl.UInt32),
                        pl.Field("end", pl.UInt32),
                        pl.Field("text", pl.String),
                    ]
                )
            ),
        )


print("PIIExprNamespace registered successfully")
