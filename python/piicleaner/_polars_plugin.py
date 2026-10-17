from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl
    from polars import Expr

    from piicleaner._types import Cleaning

try:
    import polars as pl
    from polars import Expr
    from polars.plugins import register_plugin_function

    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False

import piicleaner
from piicleaner import _internal

# The Polars plugin functions are compiled into the extension module itself.
# Point Polars at that exact file: given a directory, it loads the first
# library it finds there
_PLUGIN_PATH = Path(_internal.__file__)


def _clean_pii_expr(
    expr: Expr,
    cleaning: Cleaning,
    cleaners: list[str],
    ignore_case: bool,
    replace_string: str | None,
) -> Expr:
    """Expression that cleans PII from a string column in Rust.

    Nulls stay null. Cleaner names and the cleaning method are validated
    here, when the expression is built. A non-string column fails when the
    query is planned, with a Polars error.
    """
    piicleaner.clean_pii_with_cleaners_batch(
        [], cleaners, cleaning, ignore_case, replace_string
    )
    return register_plugin_function(
        plugin_path=_PLUGIN_PATH,
        function_name="clean_pii",
        args=expr,
        kwargs={
            "cleaners": cleaners,
            "cleaning": cleaning,
            "ignore_case": ignore_case,
            "replace_string": replace_string,
        },
        is_elementwise=True,
    )


def _detect_pii_expr(
    expr: Expr, cleaners: list[str], ignore_case: bool
) -> Expr:
    """Expression that detects PII in a string column in Rust.

    Returns a list of ``{start, end, text, type}`` structs per row, with
    ``start``/``end`` as Int64 character offsets. Null rows give null.
    Cleaner names are validated here, when the expression is built. A
    non-string column fails when the query is planned, with a Polars error.
    """
    piicleaner.detect_pii_with_cleaners_batch([], cleaners, ignore_case)
    return register_plugin_function(
        plugin_path=_PLUGIN_PATH,
        function_name="detect_pii",
        args=expr,
        kwargs={"cleaners": cleaners, "ignore_case": ignore_case},
        is_elementwise=True,
    )


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
            return _detect_pii_expr(self._expr, cleaners, ignore_case)

        def clean_pii(
            self,
            cleaning: Cleaning,
            cleaners: str | list[str] = "all",
            ignore_case: bool = True,
            replace_string: str | None = None,
        ) -> Expr:
            """Clean PII from text."""
            if isinstance(cleaners, str):
                cleaners = [cleaners]
            return _clean_pii_expr(
                self._expr, cleaning, cleaners, ignore_case, replace_string
            )
