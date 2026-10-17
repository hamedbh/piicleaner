"""The four DataFrame entry points behave the same way (#54, #59):
`Cleaner.clean_dataframe()`/`detect_dataframe()` with a Polars or pandas
DataFrame, the Polars `.pii` expressions and the pandas `.pii` accessor."""

import datetime as dt
import decimal

import pytest

pl = pytest.importorskip("polars")
pd = pytest.importorskip("pandas")

import piicleaner  # noqa: E402, F401
from piicleaner import Cleaner  # noqa: E402

TEXTS = ["Email a@b.com", None, "nothing here"]


def as_list(column):
    """A Polars or pandas column as a list of Python values"""
    return (
        column.to_list() if isinstance(column, pl.Series) else column.tolist()
    )


class TestNulls:
    """Null values stay null: cleaning returns them unchanged and detection
    gives null, not an empty list"""

    def test_polars(self):
        df = pl.DataFrame({"t": TEXTS})
        for detected in [
            df.select(pl.col("t").pii.detect_pii())["t"],
            Cleaner().detect_dataframe(df, "t")["t_pii_detected"],
        ]:
            assert detected[1] is None
            assert detected.to_list()[2] == []
        for cleaned in [
            df.select(pl.col("t").pii.clean_pii("redact"))["t"],
            Cleaner().clean_dataframe(df, "t", "redact")["t"],
        ]:
            assert cleaned[1] is None

    def test_pandas(self):
        df = pd.DataFrame({"t": TEXTS})
        for detected in [
            df["t"].pii.detect_pii(),
            Cleaner().detect_dataframe(df, "t")["t_pii_detected"],
        ]:
            assert detected.iloc[1] is None
            assert detected.iloc[2] == []
        for cleaned in [
            df["t"].pii.clean_pii("redact"),
            Cleaner().clean_dataframe(df, "t", "redact")["t"],
        ]:
            assert pd.isna(cleaned.iloc[1])

    def test_all_null_columns(self):
        """An all-null Polars column has dtype Null, not String"""
        cleaner = Cleaner()
        for df in [
            pl.DataFrame({"t": [None, None]}),
            pd.DataFrame({"t": [None, None]}),
        ]:
            assert as_list(
                cleaner.detect_dataframe(df, "t")["t_pii_detected"]
            ) == [
                None,
                None,
            ]
            cleaned = cleaner.clean_dataframe(df, "t", "redact")["t"]
            assert all(pd.isna(v) for v in as_list(cleaned))


POLARS_NON_STRING = {
    "Int64": pl.Series("x", [1]),
    "Int8": pl.Series("x", [1], dtype=pl.Int8),
    "UInt64": pl.Series("x", [1], dtype=pl.UInt64),
    "Float64": pl.Series("x", [1.5]),
    "Boolean": pl.Series("x", [True]),
    "Decimal": pl.Series("x", [decimal.Decimal("1.5")]),
    "Date": pl.Series("x", [dt.date(2020, 1, 1)]),
    "Datetime": pl.Series("x", [dt.datetime(2020, 1, 1)]),
    "Duration": pl.Series("x", [dt.timedelta(1)]),
    "Time": pl.Series("x", [dt.time(1)]),
    "Binary": pl.Series("x", [b"a"]),
    "Categorical": pl.Series("x", ["a@b.com"], dtype=pl.Categorical),
    "Enum": pl.Series("x", ["a@b.com"], dtype=pl.Enum(["a@b.com"])),
    "List": pl.Series("x", [["a@b.com"]]),
    "Array": pl.Series("x", [["a@b.com"]], dtype=pl.Array(pl.String, 1)),
    "Struct": pl.Series("x", [{"a": "a@b.com"}]),
}
if hasattr(pl, "Int128"):
    POLARS_NON_STRING["Int128"] = pl.Series("x", [1], dtype=pl.Int128)


class TestNonStringValues:
    """piicleaner only cleans strings. Other values raise an error naming the
    column, instead of being converted to strings"""

    @pytest.mark.parametrize(
        "series", POLARS_NON_STRING.values(), ids=POLARS_NON_STRING.keys()
    )
    def test_polars_dataframe_methods(self, series):
        df = pl.DataFrame([series])
        with pytest.raises(TypeError, match="column 'x' has dtype"):
            Cleaner().clean_dataframe(df, "x", "redact")
        with pytest.raises(TypeError, match="column 'x' has dtype"):
            Cleaner().detect_dataframe(df, "x")

    @pytest.mark.parametrize(
        "series", POLARS_NON_STRING.values(), ids=POLARS_NON_STRING.keys()
    )
    def test_polars_expressions(self, series):
        """The plugin rejects the column while the query is planned. Some of
        these dtypes, such as Categorical, used to crash the process"""
        df = pl.DataFrame([series])
        for expr in [
            pl.col("x").pii.clean_pii("redact"),
            pl.col("x").pii.detect_pii(),
        ]:
            with pytest.raises(
                pl.exceptions.PolarsError, match="column `x` has dtype"
            ):
                df.select(expr)
            with pytest.raises(
                pl.exceptions.PolarsError, match="column `x` has dtype"
            ):
                df.lazy().select(expr).collect()

    @pytest.mark.parametrize(
        ("values", "dtype", "found"),
        [
            ([1, 2], None, "int values such as 1"),
            ([1.5, None], None, "float values such as 1.5"),
            (["a@b.com", 7, None], object, "int values such as 7"),
            (["a@b.com", b"x"], object, "bytes values"),
            (["a@b.com"], "category", "category values"),
        ],
        ids=["int64", "float64", "mixed-object", "bytes", "category"],
    )
    def test_pandas(self, values, dtype, found):
        series = pd.Series(values, dtype=dtype, name="x")
        df = pd.DataFrame({"x": series})
        for call in [
            lambda: series.pii.clean_pii("redact"),
            lambda: series.pii.detect_pii(),
            lambda: Cleaner().clean_dataframe(df, "x", "redact"),
            lambda: Cleaner().detect_dataframe(df, "x"),
        ]:
            with pytest.raises(TypeError, match=f"'x'.*contains {found}"):
                call()

    def test_pandas_string_dtypes_accepted(self):
        for dtype in [object, "string"]:
            series = pd.Series(["a@b.com", None], dtype=dtype)
            assert series.pii.clean_pii("redact").iloc[0] == "[email-redacted]"


class TestDataFrameDispatch:
    """One pair of DataFrame methods takes Polars and pandas DataFrames"""

    def test_results_match_across_libraries(self):
        cleaner = Cleaner()
        texts = ["Email a@b.com", "NINO AB123456C", None]
        pl_df = pl.DataFrame({"t": texts})
        pd_df = pd.DataFrame({"t": texts})

        pl_clean = cleaner.clean_dataframe(pl_df, "t", "redact")
        pd_clean = cleaner.clean_dataframe(pd_df, "t", "redact")
        assert isinstance(pl_clean, pl.DataFrame)
        assert isinstance(pd_clean, pd.DataFrame)
        assert pl_clean["t"].to_list()[:2] == pd_clean["t"].tolist()[:2]

        pl_detect = cleaner.detect_dataframe(pl_df, "t")["t_pii_detected"]
        pd_detect = cleaner.detect_dataframe(pd_df, "t")["t_pii_detected"]
        assert pl_detect.to_list() == pd_detect.tolist()

    def test_pandas_methods_match_accessor(self):
        df = pd.DataFrame({"t": ["Email a@b.com", None]})
        cleaner = Cleaner(cleaners=["email"], replace_string="X")
        pd.testing.assert_series_equal(
            cleaner.clean_dataframe(df, "t", "replace")["t"],
            df["t"].pii.clean_pii(
                "replace", cleaners=["email"], replace_string="X"
            ),
        )
        pd.testing.assert_series_equal(
            cleaner.detect_dataframe(df, "t", new_column_name="t")["t"],
            df["t"].pii.detect_pii(cleaners=["email"]),
        )

    @pytest.mark.parametrize("df", [["not", "a", "df"], {"t": ["a"]}])
    def test_other_types_rejected(self, df):
        with pytest.raises(TypeError, match="df must be a Polars or pandas"):
            Cleaner().clean_dataframe(df, "t", "redact")
        with pytest.raises(TypeError, match="df must be a Polars or pandas"):
            Cleaner().detect_dataframe(df, "t")


class TestDeprecatedPandasMethods:
    """`clean_pandas_dataframe()`/`detect_pandas_dataframe()` still work,
    with a DeprecationWarning, until they're removed in 0.8.0"""

    def test_warn_and_match_new_methods(self):
        cleaner = Cleaner()
        df = pd.DataFrame({"t": ["Email a@b.com", None]})
        with pytest.deprecated_call(match="removed in 0.8.0"):
            cleaned = cleaner.clean_pandas_dataframe(df, "t", "redact")
        with pytest.deprecated_call(match="removed in 0.8.0"):
            detected = cleaner.detect_pandas_dataframe(df, "t")
        pd.testing.assert_frame_equal(
            cleaned, cleaner.clean_dataframe(df, "t", "redact")
        )
        pd.testing.assert_frame_equal(
            detected, cleaner.detect_dataframe(df, "t")
        )

    def test_still_pandas_only(self):
        df = pl.DataFrame({"t": ["a"]})
        with pytest.deprecated_call():
            with pytest.raises(TypeError, match="df must be a pandas"):
                Cleaner().clean_pandas_dataframe(df, "t", "redact")
        with pytest.deprecated_call():
            with pytest.raises(TypeError, match="df must be a pandas"):
                Cleaner().detect_pandas_dataframe(df, "t")


class TestCleanerIgnoreCase:
    """`Cleaner(ignore_case=...)` sets the default for every method; a
    method's own `ignore_case` overrides it"""

    TEXT = "nino: ab123456c"

    def test_default_is_case_insensitive(self):
        assert Cleaner(["nino"]).detect_pii(self.TEXT) != []

    def test_cleaner_setting_used_by_every_method(self):
        cleaner = Cleaner(["nino"], ignore_case=False)
        assert cleaner.detect_pii(self.TEXT) == []
        assert cleaner.detect_pii_list([self.TEXT]) == [[]]
        assert cleaner.clean_pii(self.TEXT, "redact") == self.TEXT
        assert cleaner.clean_pii_list([self.TEXT], "redact") == [self.TEXT]
        for df in [
            pl.DataFrame({"t": [self.TEXT]}),
            pd.DataFrame({"t": [self.TEXT]}),
        ]:
            assert as_list(cleaner.clean_dataframe(df, "t", "redact")["t"]) == [
                self.TEXT
            ]
            assert as_list(
                cleaner.detect_dataframe(df, "t")["t_pii_detected"]
            ) == [[]]

    def test_method_argument_overrides_cleaner_setting(self):
        cleaner = Cleaner(["nino"], ignore_case=False)
        assert cleaner.detect_pii(self.TEXT, ignore_case=True) != []
        assert cleaner.clean_pii(self.TEXT, "redact", True) != self.TEXT
        df = pl.DataFrame({"t": [self.TEXT]})
        assert cleaner.clean_dataframe(df, "t", "redact", ignore_case=True)[
            "t"
        ].to_list() == ["nino: [nino-redacted]"]

        lenient = Cleaner(["nino"])
        assert lenient.detect_pii(self.TEXT, ignore_case=False) == []
