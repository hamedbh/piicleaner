# PIICleaner

A fast, Rust-powered Python library for detecting and cleaning Personal Identifiable Information (PII) from text data, with seamless Polars integration.

## Features

- **Fast PII Detection**: Rust-based regex engine for high-performance text processing
- **Multiple PII Types**: Detects emails, phone numbers, postcodes, National Insurance numbers, addresses, and more
- **Flexible Cleaning**: Replace or redact detected PII with customizable strategies
- **Polars Integration**: Native support for cleaning DataFrames and Series
- **Easy to Use**: Simple API for both single strings and batch processing

## Installation

```bash
# Using uv
uv add piicleaner

# Using  pip
pip install piicleaner
```

### Platform Support

PIICleaner provides pre-built wheels for:

- **Windows**: x86_64 (Intel/AMD 64-bit)
- **macOS**: x86_64 (Intel) and arm64 (Apple Silicon)
- **Linux**: x86_64 (Intel/AMD 64-bit)

**Note**: Linux ARM64 (aarch) wheels are not currently provides. Users on ARM64 Linux systems (e.g. Raspberry Pi, AWS Graviton) will need to build from source. See [Building from Source](#building-from-source) below.

### Building from Source

For platforms without pre-built wheels you'll need:

- Rust toolchain (1.70 or newer), install from [rustup.rs](https://rustup.rs)
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

# Initialize cleaner
cleaner = Cleaner()

# Clean a single string
text = "Contact John at john@example.com or call +44 20 7946 0958"
cleaned = cleaner.clean_pii(text, "redact")
print(cleaned)  # "Contact John at [REDACTED] or call [REDACTED]"

# Detect PII locations
matches = cleaner.detect_pii(text)
print(matches)  
# [{'start': 17, 'end': 34, 'text': 'john@example.com'}, 
#  {'start': 43, 'end': 58, 'text': '+44 20 7946 0958'}]
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
cleaned_df = cleaner.clean_dataframe(df, "text", "redact", "cleaned_text")
print(cleaned_df)

# Detect PII in DataFrame  
pii_df = cleaner.detect_dataframe(df, "text")
print(pii_df)
```

### Specific PII Types

```python
# Use specific cleaners
email_cleaner = Cleaner(cleaners=["email"])
phone_cleaner = Cleaner(cleaners=["telephone", "postcode"])

# See available cleaners
print(Cleaner.get_available_cleaners())
# ['address', 'case-id', 'cash-amount', 'email', 'nino', 'postcode', 'tag', 'telephone']
```

## Supported PII Types

| Type | Description | Example |
|------|-------------|---------|
| `email` | Email addresses | `john@example.com` |
| `telephone` | UK phone numbers | `+44 20 7946 0958` |
| `postcode` | UK postcodes | `SW1A 1AA` |
| `nino` | National Insurance numbers | `AB123456C` |
| `address` | Street addresses | `123 High Street` |
| `cash-amount` | Currency amounts | `£1,500`, `$2000` |
| `case-id` | Case/reference IDs | UUIDs, reference numbers |
| `tag` | HTML/XML tags | `<script>`, `<div>` |

## Cleaning Methods

- **`"redact"`**: Redact the PII, replacing it with `---------`
- **`"replace"`**: Replace the string entirely if _any_ PII is detected

## API Reference

### Cleaner Class

```python
class Cleaner(cleaners="all")
```

**Parameters:**
- `cleaners` (str | list[str]): PII types to detect. Use `"all"` for all types or specify a list like `["email", "telephone"]`

**Methods:**
- `detect_pii(text, ignore_case=True)`: Detect PII and return match locations
- `clean_pii(text, cleaning, ignore_case=True)`: Clean PII from text
- `clean_list(text_list, cleaning, ignore_case=True)`: Clean list of strings
- `clean_dataframe(df, column, cleaning, output_column)`: Clean Polars DataFrame
- `detect_dataframe(df, column)`: Detect PII in Polars DataFrame
- `get_available_cleaners()`: Get list of available PII types

## Performance

PIICleaner is built with Rust for maximum performance:
- Compiled regex patterns for fast matching
- Efficient string processing 
- Minimal Python overhead
- Scales well with large datasets

## Requirements

- Python ≥ 3.9
- Polars ≥ 1.0.0 (optional, for DataFrame support)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please see the [GitHub repository](https://github.com/hamedbh/piicleaner) for development setup and guidelines.
