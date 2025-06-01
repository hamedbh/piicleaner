import polars as pl
from piicleaner import Cleaner

# Test data
df = pl.DataFrame(
    {
        "text": [
            "Contact john@example.com",
            "My NINO is AB123456C",
            "Cost was £1,500",
            "No PII here",
        ]
    }
)

print("Original DataFrame:")
print(df)

# Test the new namespace API
try:
    result = df.with_columns(
        pl.col("text").pii.clean_pii("redact").alias("cleaned_text")
    )

    print("\nUsing .pii.clean_pii() namespace:")
    print(result)

except Exception as e:
    print(f"Error with .pii.clean_pii(): {e}")

# Test detection
try:
    detect_result = df.with_columns(
        pl.col("text").pii.detect_pii().alias("pii_found")
    )
    print("\nUsing .pii.detect_pii() namespace:")
    print(detect_result)

except Exception as e:
    print(f"Error with .pii.detect_pii(): {e}")
