# test_polars.py
import polars as pl
from piicleaner import Cleaner

# Test data with PII
data = {
    "text": [
        "Contact John at john@example.com",
        "My NINO is AB123456C",
        "Call me at +44 20 7946 0958",
        "Address: 123 High Street",
        "Cost was £1,500",
        "No PII here",
    ],
    "id": [1, 2, 3, 4, 5, 6],
}

df = pl.DataFrame(data)
print("Original DataFrame:")
print(df)

# Test Polars cleaning
cleaner = Cleaner()
cleaned_df = cleaner.clean_dataframe(df, "text", "redact", "cleaned_text")
print("\nDataFrame with cleaned text:")
print(cleaned_df)

# Test PII detection
pii_df = cleaner.detect_dataframe(df, "text")
print("\nPII Detection results:")
print(pii_df)
