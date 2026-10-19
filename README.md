# PIICleaner

A fast, Rust-powered Python library for detecting and cleaning Personal Identifiable Information (PII) from text data, with seamless Polars and Pandas integration.

## Features

- **Fast PII Detection**: Rust-based regex engine for high-performance text processing
- **Case-Insensitive Matching**: Detects PII regardless of case by default, with optional case-sensitive mode
- **Multiple PII Types**: Detects emails, phone numbers, postcodes, National Insurance numbers, addresses, and more
- **Flexible Cleaning**: Replace or redact detected PII with customisable strategies
- **Semantic Redaction**: Replace PII with meaningful labels like `[email-redacted]` instead of generic dashes
- **Custom Replacement Strings**: Define your own replacement text for the "replace" cleaning method
- **PII Type Detection**: Get detailed information about what type of PII was detected
- **Polars Integration**: A native Polars plugin cleans whole columns in Rust, in parallel, in eager and lazy queries
- **Pandas Integration**: Native support for cleaning DataFrames and Series
- **Easy to Use**: Simple API for both single strings and batch processing

## Installation

```bash
# Using uv
uv add piicleaner
# With Polars support
uv add 'piicleaner[polars]'
# With Pandas support
uv add 'piicleaner[pandas]'

# Using  pip
pip install piicleaner
# With Polars support
pip install 'piicleaner[polars]'
# With Pandas support
pip install 'piicleaner[pandas]'
```

### Platform Support

PIICleaner provides pre-built wheels for the platforms below. Each wheel works on every Python version from 3.11 onwards, including new releases.

- **Windows**: x86_64 (Intel/AMD 64-bit)
- **macOS**: x86_64 (Intel) and arm64 (Apple Silicon)
- **Linux**: x86_64 (Intel/AMD 64-bit) and aarch64 (ARM64, e.g. AWS Graviton, Raspberry Pi), for both glibc (manylinux) and musl (musllinux, e.g. Alpine) distributions

### Building from Source

On other platforms pip builds piicleaner from source, which needs:

- Rust toolchain (1.95 or newer), install from [rustup.rs](https://rustup.rs)
- Python development headers

```bash
# Using uv
uv add piicleaner --no-binary piicleaner

# Using pip
pip install piicleaner --no-binary piicleaner
```

## Quick Start

### Basic Usage

```python
from piicleaner import Cleaner

# Instantiate a cleaner
cleaner = Cleaner()

# Clean a single string (case-insensitive by default)
text = "Contact John at JOHN@EXAMPLE.COM or call +44 20 7946 0958"
cleaned = cleaner.clean_pii(text, "redact")
print(cleaned)  # "Contact John at [email-redacted] or call [telephone-redacted]"

# Detect PII locations with type information
matches = cleaner.detect_pii(text)
print(matches)  
# [{'start': 16, 'end': 32, 'text': 'JOHN@EXAMPLE.COM', 'type': 'email'},
#  {'start': 41, 'end': 57, 'text': '+44 20 7946 0958', 'type': 'telephone'},
#  {'start': 41, 'end': 57, 'text': '+44 20 7946 0958', 'type': 'international-telephone'}]
# Every cleaner's match is listed, so one piece of text can appear more than once
# 'start' and 'end' are character offsets, so they slice the original string:
# text[16:32] == 'JOHN@EXAMPLE.COM', even when the text contains non-ASCII
# characters such as '£' or 'é'

# Case-sensitive detection
nino_cleaner = Cleaner(cleaners=["nino"])
matches_sensitive = nino_cleaner.detect_pii("nino: ab123456c", ignore_case=False)
print(matches_sensitive)  # [] - no match because NINO pattern expects uppercase

matches_insensitive = nino_cleaner.detect_pii("nino: ab123456c", ignore_case=True)
print(matches_insensitive)  # [{'start': 6, 'end': 15, 'text': 'ab123456c', 'type': 'nino'}]
```

### Polars Integration

```python
import polars as pl
from piicleaner import Cleaner

# Create DataFrame with PII
df = pl.DataFrame({
    "text": [
        "Email: alice@company.com",
        "NINO: AB123456C", 
        "Phone: +44 20 7946 0958"
    ],
    "id": [1, 2, 3]
})

cleaner = Cleaner()

# Clean PII in DataFrame
cleaned_df = cleaner.clean_dataframe(df, "text", "redact", new_column_name="cleaned_text")
print(cleaned_df)

# Detect PII in DataFrame  
pii_df = cleaner.detect_dataframe(df, "text")
print(pii_df)

# Using namespace API
result = df.with_columns(
    pl.col("text").pii.clean_pii("redact").alias("cleaned")
)
```

### Pandas Integration

```python
import pandas as pd
from piicleaner import Cleaner

# Create DataFrame with PII
df = pd.DataFrame({
    "text": [
        "Email: alice@company.com",
        "NINO: AB123456C", 
        "Phone: +44 20 7946 0958"
    ],
    "id": [1, 2, 3]
})

cleaner = Cleaner()

# The same DataFrame methods as for Polars
cleaned_df = cleaner.clean_dataframe(df, "text", "redact", new_column_name="cleaned_text")
print(cleaned_df)

# Detect PII in DataFrame
pii_df = cleaner.detect_dataframe(df, "text")
print(pii_df)

# Using Series accessor API
df["cleaned"] = df["text"].pii.clean_pii("redact")
df["pii_detected"] = df["text"].pii.detect_pii()
```

### Specific PII Types and Custom Replacement

```python
# Use specific cleaners
email_cleaner = Cleaner(cleaners=["email"])
phone_cleaner = Cleaner(cleaners=["telephone", "postcode"])

# Case-insensitive cleaning with specific cleaners
text = "EMAIL: JOHN@EXAMPLE.COM"
cleaned = email_cleaner.clean_pii(text, "redact", ignore_case=True)
print(cleaned)  # "EMAIL: [email-redacted]"

# Custom replacement string
custom_cleaner = Cleaner(replace_string="[CONFIDENTIAL]")
text = "Contact john@example.com"
replaced = custom_cleaner.clean_pii(text, "replace")
print(replaced)  # "[CONFIDENTIAL]"

# See available cleaners
print(Cleaner.get_available_cleaners())
# ['address', 'case-id', 'cash-amount', 'email', 'international-telephone', 'ip_address', 'nino', 'postcode', 'tag', 'telephone']
```

## Supported PII Types

| Type | Description | Example |
|------|-------------|---------|
| `email` | Email addresses | `john@example.com` |
| `telephone` | UK phone numbers | `+44 20 7946 0958` |
| `international-telephone` | Phone numbers with a `+` or `00` international prefix | `+1 415 555 0132`, `+33 1 23 45 67 89` |
| `postcode` | UK postcodes, with any whitespace (or none) between the two halves | `SW1A 1AA`, `SW1A1AA` |
| `nino` | National Insurance numbers, with spaces, dashes or dots between groups | `AB123456C`, `AB-12-34-56-C`, `AB 123 456 C` |
| `address` | Street addresses | `123 High Street` |
| `cash-amount` | Currency amounts | `£1,500`, `$2000` |
| `case-id` | Case/reference IDs | UUIDs, reference numbers |
| `tag` | HTML/XML tags | `<script>`, `<div>` |
| `ip_address` | IPv4 and IPv6 addresses | `192.168.1.1`, `2001:db8::1`, `fe80::1%eth0` |

## Cleaning Methods

- **`"redact"`**: Redact the PII, replacing it with semantic labels like `[email-redacted]`, `[telephone-redacted]`. Where matches from different cleaners overlap, the whole overlapping region is redacted and labelled with the highest-priority cleaner, in the order returned by `piicleaner.get_available_cleaners()`. The same input always produces the same output.
- **`"replace"`**: Replace the entire string if _any_ PII is detected (uses custom replacement string if provided)

## Over-Matching Is Expected

PIICleaner errs towards redaction. Missing PII costs far more than redacting text that isn't PII, so the patterns are deliberately broad and some false positives are expected behaviour, not bugs. For example, with the default case-insensitive matching, `item a1 1aa` is redacted as a postcode.

If you need fewer false positives, choose only the cleaners you need, or use `ignore_case=False`. Both make it more likely that some PII is missed.

## Case Sensitivity

By default, PIICleaner performs **case-insensitive** matching to catch PII regardless of how it's formatted:

- `ignore_case=True` (default): Detects `ab123456c`, `AB123456C`, and `Ab123456C` as valid NINOs
- `ignore_case=False`: Only detects patterns matching the exact case defined in regex patterns

Case-insensitive matching finds more PII, and also more false positives, notably for `nino`, `postcode` and `case-id`. Set it once for a `Cleaner` with `Cleaner(ignore_case=False)`, or pass `ignore_case` to a single call.

## API Reference

### Cleaner Class

```python
Cleaner(cleaners="all", replace_string=None, ignore_case=True)
```

**Parameters:**
- `cleaners` (str | list[str]): PII types to detect. Use `"all"` for all types or specify a list like `["email", "telephone"]`
- `replace_string` (str | None): Custom replacement string for "replace" cleaning method
- `ignore_case` (bool): Default for every method's `ignore_case`

**Methods** (`cleaning` is `"redact"` or `"replace"`; `ignore_case=None` means the `Cleaner`'s setting):
- `detect_pii(text, ignore_case=None)`: Detect PII and return match locations with type information
- `detect_pii_list(texts, ignore_case=None)`: Detect PII in list of strings
- `clean_pii(text, cleaning, ignore_case=None)`: Clean PII from text
- `clean_pii_list(texts, cleaning, ignore_case=None)`: Clean list of strings
- `clean_dataframe(df, column, cleaning, *, ignore_case=None, new_column_name=None)`: Clean a column of a Polars or pandas DataFrame
- `detect_dataframe(df, column, *, ignore_case=None, new_column_name=None)`: Detect PII in a column of a Polars or pandas DataFrame
- `get_available_cleaners()`: Get list of available PII types

In the DataFrame methods, `ignore_case` and `new_column_name` are keyword-only, e.g. `clean_dataframe(df, "text", "redact", new_column_name="cleaned_text")`.

`clean_pandas_dataframe()` and `detect_pandas_dataframe()` are deprecated and will be removed in 0.8.0. Use `clean_dataframe()` and `detect_dataframe()`, which take pandas DataFrames too.

**DataFrame Integration Features:**
- **Polars**: `.pii.clean_pii()` and `.pii.detect_pii()` expressions, which run as a native Polars plugin (no per-row Python) and work in lazy queries. `clean_dataframe()`/`detect_dataframe()` use the same plugin
- **Pandas**: Series accessor `.pii.clean_pii()` and `.pii.detect_pii()` methods
- **Nulls**: null values stay null. Cleaning returns them unchanged, and detection gives null rather than an empty list
- **Strings only**: a column of non-string values raises an error instead of being converted. `clean_dataframe()`/`detect_dataframe()` and the pandas `.pii` accessor raise `TypeError`; the Polars `.pii` expressions raise a Polars error when the query runs. If the column holds text, cast it to strings first
- **Vectorized Processing**: Efficient batch processing for large datasets

## Performance

PIICleaner is built with Rust for maximum performance:
- Compiled regex patterns for fast matching
- Efficient string processing 
- Minimal Python overhead
- Scales well with large datasets

## Requirements

- Python ≥ 3.11
- Polars ≥ 1.0.0 (optional, for Polars DataFrame support)
- Pandas ≥ 2.3.0 (optional, for Pandas DataFrame support)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please see the [GitHub repository](https://github.com/hamedbh/piicleaner) for development setup and guidelines.
