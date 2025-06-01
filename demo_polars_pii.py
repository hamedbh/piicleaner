# demo_polars_pii.py - Complete demonstration of Polars PII cleaning
import polars as pl
from piicleaner import Cleaner

# Create test data with various types of PII
data = {
    "id": [1, 2, 3, 4, 5],
    "text": [
        "Contact john.smith@company.com for details",
        "My National Insurance Number is AB123456C and phone is 07123456789",
        "Transaction of £15,000.50 processed successfully",
        "IP address 192.168.1.100 accessed the system",
        "No sensitive information in this record"
    ],
    "category": ["email", "personal", "financial", "technical", "clean"]
}

df = pl.DataFrame(data)

print("=== Original Data ===")
print(df)

print("\n=== Clean PII with Redaction ===")
result = df.with_columns(
    pl.col("text").pii.clean("redact").alias("cleaned_text")
)
print(result.select(["id", "text", "cleaned_text"]))

print("\n=== Clean PII with Replacement ===")
result = df.with_columns(
    pl.col("text").pii.clean("replace").alias("replaced_text")
)
print(result.select(["id", "text", "replaced_text"]))

print("\n=== Detect PII ===")
result = df.with_columns(
    pl.col("text").pii.detect().alias("pii_found")
)
print(result.select(["id", "category", "pii_found"]))

print("\n=== Count PII Matches per Row ===")
result = df.with_columns(
    pl.col("text").pii.detect().list.len().alias("pii_count")
)
print(result.select(["id", "category", "pii_count"]))

print("\n=== Filter Rows with PII ===")
result = df.filter(
    pl.col("text").pii.detect().list.len() > 0
).with_columns(
    pl.col("text").pii.clean("redact").alias("cleaned_text")
)
print(result.select(["id", "category", "cleaned_text"]))

print("\n=== Complex Pipeline: CSV → Clean → Export ===")
# Simulate reading from CSV, cleaning, and preparing for export
pipeline_result = (
    df
    .with_columns([
        pl.col("text").pii.detect().alias("pii_detected"),
        pl.col("text").pii.clean("redact").alias("cleaned_text"),
        pl.col("text").pii.detect().list.len().alias("pii_count")
    ])
    .with_columns(
        pl.when(pl.col("pii_count") > 0)
        .then(pl.lit("PII_FOUND"))
        .otherwise(pl.lit("CLEAN"))
        .alias("data_classification")
    )
)

print(pipeline_result.select([
    "id", "category", "data_classification", "pii_count", "cleaned_text"
]))

print("\n🎉 Polars PII cleaning is working perfectly!")
print("You can now use: pl.col('text').pii.clean('redact')")
print("And also: pl.col('text').pii.detect()")
