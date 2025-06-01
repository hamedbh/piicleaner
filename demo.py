#!/usr/bin/env python3
"""
PIICleaner Demo Script

Demonstrates all the features of the PIICleaner package including:
- Basic PII detection and cleaning
- Polars DataFrame integration
- Specific cleaner selection
"""

import polars as pl
import piicleaner


def demo_basic_functions():
    """Demonstrate basic PII detection and cleaning functions."""
    print("=" * 60)
    print("BASIC PII DETECTION AND CLEANING")
    print("=" * 60)

    # Sample texts with various PII types
    texts = [
        "My NINO is AB123456C and I live at 123 Main St, London SW1A 1AA",
        "Contact me at john.doe@example.com or call 07700 900123",
        "Case ID: 987654, amount: £1,234.50, IP: 192.168.1.1",
        "No sensitive information in this text",
    ]

    for i, text in enumerate(texts, 1):
        print(f"\nText {i}: {text}")

        # Detect PII
        matches = piicleaner.detect_pii(text)
        print(f"PII detected: {len(matches)} matches")
        for start, end, matched in matches:
            print(f"  - '{matched}' at position {start}-{end}")

        # Clean with redact
        redacted = piicleaner.clean_pii(text, "redact")
        print(f"Redacted: {redacted}")

        # Clean with replace
        replaced = piicleaner.clean_pii(text, "replace")
        print(f"Replaced: {replaced}")


def demo_specific_cleaners():
    """Demonstrate using specific cleaners."""
    print("\n" + "=" * 60)
    print("SPECIFIC CLEANER SELECTION")
    print("=" * 60)

    # Get available cleaners
    cleaners = piicleaner.get_available_cleaners()
    print(f"Available cleaners: {cleaners}")

    text = "NINO: AB123456C, Email: test@example.com, Phone: 07700 900123"
    print(f"\nTest text: {text}")

    # Test specific cleaners
    test_cleaners = ["nino", "email", "telephone"]
    for cleaner in test_cleaners:
        matches = piicleaner.detect_pii_with_cleaners(text, [cleaner])
        print(f"\n{cleaner.upper()} cleaner found {len(matches)} matches:")
        for start, end, matched in matches:
            print(f"  - '{matched}' at position {start}-{end}")


def demo_polars_integration():
    """Demonstrate Polars DataFrame integration."""
    print("\n" + "=" * 60)
    print("POLARS DATAFRAME INTEGRATION")
    print("=" * 60)

    # Create sample DataFrame
    df = pl.DataFrame(
        {
            "customer_id": [1, 2, 3, 4, 5],
            "feedback": [
                "My NINO is AB123456C, very satisfied",
                "Email me at customer@example.com with updates",
                "Called from 07700 900123, issue resolved",
                "Great service, no complaints!",
                "Address: 123 Main St, London SW1A 1AA",
            ],
            "category": [
                "complaint",
                "request",
                "support",
                "praise",
                "update",
            ],
        }
    )

    print("Original DataFrame:")
    print(df)

    # Detect PII
    print("\nDetecting PII:")
    with_pii = df.with_columns(
        pl.col("feedback").pii.detect_pii().alias("pii_detected")
    )
    print(with_pii)

    # Clean PII with redact
    print("\nCleaning PII (redact mode):")
    redacted_df = df.with_columns(
        pl.col("feedback").pii.clean_pii("redact").alias("feedback_redacted")
    )
    print(redacted_df.select(["customer_id", "feedback", "feedback_redacted"]))

    # Clean PII with replace
    print("\nCleaning PII (replace mode):")
    replaced_df = df.with_columns(
        pl.col("feedback").pii.clean_pii("replace").alias("feedback_replaced")
    )
    print(replaced_df.select(["customer_id", "feedback", "feedback_replaced"]))

    # Filter rows with PII
    print("\nRows containing PII:")
    has_pii = with_pii.filter(pl.col("pii_detected").list.len() > 0)
    print(has_pii.select(["customer_id", "feedback", "category"]))


def demo_data_analysis():
    """Demonstrate PII analysis capabilities."""
    print("\n" + "=" * 60)
    print("PII DATA ANALYSIS")
    print("=" * 60)

    # Create larger sample dataset
    df = pl.DataFrame(
        {
            "record_id": range(1, 11),
            "text_data": [
                "NINO: AB123456C, clean record",
                "Email: user1@company.com",
                "Phone: 07700 900123, urgent",
                "Clean text with no PII",
                "Multiple: AB987654D and test@example.com",
                "Address: 456 Oak St, Manchester M1 1AA",
                "Another clean record",
                "Case: 123456, Email: admin@site.org",
                "IP address: 192.168.1.100",
                "Final clean record",
            ],
        }
    )

    # Analyze PII distribution
    analysis = df.with_columns(
        [
            pl.col("text_data").pii.detect_pii().alias("pii_matches"),
        ]
    ).with_columns(
        [
            pl.col("pii_matches").list.len().alias("pii_count"),
            (pl.col("pii_matches").list.len() > 0).alias("has_pii"),
        ]
    )

    print("PII Analysis Results:")
    print(analysis)

    # Summary statistics
    summary = analysis.select(
        [
            pl.col("has_pii").sum().alias("records_with_pii"),
            pl.col("pii_count").sum().alias("total_pii_instances"),
            pl.col("pii_count").mean().alias("avg_pii_per_record"),
            (pl.col("has_pii").sum() / pl.len() * 100).alias("pii_percentage"),
        ]
    )

    print("\nSummary Statistics:")
    print(summary)


if __name__ == "__main__":
    demo_basic_functions()
    demo_specific_cleaners()
    demo_polars_integration()
    demo_data_analysis()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
