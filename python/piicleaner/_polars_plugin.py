"""Polars plugin registration for PII cleaning"""

try:
    import polars as pl
    from polars.type_aliases import IntoExpr

    POLARS_AVAILABLE = True

    # Direct namespace registration approach
    @pl.api.register_expr_namespace("pii")
    class PIINamespace:
        """PII cleaning namespace for Polars expressions."""

        def __init__(self, expr: pl.Expr):
            self._expr = expr

        def clean(self, method: str = "redact") -> pl.Expr:
            """Clean PII from the expression.

            Parameters
            ----------
            method : str, default "redact"
                Cleaning method: "redact" or "replace"

            Returns
            -------
            pl.Expr
                Expression with PII cleaned
            """

            def _clean_text(text: str) -> str:
                from piicleaner._internal import clean_pii

                return clean_pii(text, method)

            return self._expr.map_elements(_clean_text, return_dtype=pl.String)

        def detect(self) -> pl.Expr:
            """Detect PII in the expression, returning a list of matches.

            Returns
            -------
            pl.Expr
                Expression returning list of PII matches
            """

            def _detect_pii(text: str) -> list:
                from piicleaner._internal import detect_pii

                matches = detect_pii(text)
                # Convert to list of dicts for Polars
                return [
                    {"start": start, "end": end, "text": text}
                    for start, end, text in matches
                ]

            return self._expr.map_elements(
                _detect_pii,
                return_dtype=pl.List(
                    pl.Struct(
                        [
                            pl.Field("start", pl.Int64),
                            pl.Field("end", pl.Int64),
                            pl.Field("text", pl.String),
                        ]
                    )
                ),
            )

    # Print debug info
    print(f"PIINamespace registered successfully: {PIINamespace}")

except ImportError as e:
    print(f"Polars not available: {e}")
    POLARS_AVAILABLE = False
