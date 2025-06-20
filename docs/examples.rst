Examples
========

This page contains comprehensive examples of using PIICleaner in various scenarios.

Basic Text Processing
---------------------

Simple PII Detection
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from piicleaner import Cleaner

   cleaner = Cleaner()
   
   # Sample text with various PII types
   text = """
   Hello, my name is John Smith and you can reach me at:
   - Email: john.smith@example.com
   - Phone: +44 20 7946 0958
   - Address: 123 High Street, London SW1A 1AA
   - NINO: AB123456C
   """

   # Detect all PII
   matches = cleaner.detect_pii(text)
   for match in matches:
       print(f"Found {match['type']}: '{match['text']}' at position {match['start']}-{match['end']}")

   # Clean the text
   cleaned = cleaner.clean_pii(text, "redact")
   print("Cleaned text:")
   print(cleaned)

Working with Specific PII Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Only detect emails and phone numbers
   email_phone_cleaner = Cleaner(cleaners=["email", "telephone"])
   
   text = "Contact john@example.com or call +44 20 7946 0958. Address: 123 High St."
   
   # This will only detect email and phone, ignoring the address
   matches = email_phone_cleaner.detect_pii(text)
   print(f"Found {len(matches)} matches")  # Will be 2
   
   # Clean only emails and phones
   cleaned = email_phone_cleaner.clean_pii(text, "redact")
   print(cleaned)  # Address remains unchanged

Case Sensitivity Examples
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   cleaner = Cleaner()
   
   # Mixed case examples
   test_cases = [
       "nino: ab123456c",      # lowercase
       "NINO: AB123456C",      # uppercase  
       "NiNo: Ab123456C",      # mixed case
       "email: JOHN@EXAMPLE.COM",  # uppercase email
   ]
   
   print("Case-insensitive detection (default):")
   for text in test_cases:
       matches = cleaner.detect_pii(text, ignore_case=True)
       print(f"'{text}' -> {len(matches)} matches")
   
   print("\nCase-sensitive detection:")
   for text in test_cases:
       matches = cleaner.detect_pii(text, ignore_case=False)
       print(f"'{text}' -> {len(matches)} matches")

Custom Replacement Strings
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Default replacement
   cleaner = Cleaner()
   text = "Contact john@example.com"
   print(cleaner.clean_pii(text, "replace"))
   # Output: "[PII detected, text redacted]"
   
   # Custom replacement
   custom_cleaner = Cleaner(replace_string="[CONFIDENTIAL]")
   print(custom_cleaner.clean_pii(text, "replace"))
   # Output: "[CONFIDENTIAL]"
   
   # Another custom replacement
   redacted_cleaner = Cleaner(replace_string="*** REDACTED ***")
   print(redacted_cleaner.clean_pii(text, "replace"))
   # Output: "*** REDACTED ***"

Batch Processing
----------------

Processing Lists of Strings
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from piicleaner import Cleaner

   cleaner = Cleaner()
   
   # Sample data
   documents = [
       "Employee John Smith (john.smith@company.com)",
       "Customer service: +44 20 7946 0958",
       "Invoice sent to billing@client.org",
       "Reference: Case-ID-12345, NINO: AB123456C",
       "No PII in this document",
   ]
   
   # Batch detection
   all_matches = cleaner.detect_pii_list(documents)
   for i, matches in enumerate(all_matches):
       print(f"Document {i+1}: {len(matches)} PII items found")
       for match in matches:
           print(f"  - {match['type']}: {match['text']}")
   
   # Batch cleaning
   cleaned_documents = cleaner.clean_pii_list(documents, "redact")
   for i, (original, cleaned) in enumerate(zip(documents, cleaned_documents)):
       print(f"\nDocument {i+1}:")
       print(f"Original: {original}")
       print(f"Cleaned:  {cleaned}")

DataFrame Processing
--------------------

Polars Examples
~~~~~~~~~~~~~~~

.. code-block:: python

   import polars as pl
   from piicleaner import Cleaner

   # Create sample DataFrame
   df = pl.DataFrame({
       "id": [1, 2, 3, 4, 5],
       "customer_info": [
           "John Smith - john@example.com",
           "Call customer at +44 20 7946 0958",
           "Address: 123 High Street, SW1A 1AA", 
           "NINO: AB123456C for tax purposes",
           "No sensitive information here",
       ],
       "category": ["email", "phone", "address", "nino", "clean"]
   })

   cleaner = Cleaner()

   # Method 1: Using cleaner methods
   cleaned_df = cleaner.clean_dataframe(df, "customer_info", "redact", "cleaned_info")
   print("Cleaned DataFrame:")
   print(cleaned_df)

   # Method 2: Using Polars namespace (requires polars extra)
   result = df.with_columns([
       pl.col("customer_info").pii.clean_pii("redact").alias("redacted"),
       pl.col("customer_info").pii.detect_pii().alias("pii_detected")
   ])
   print("\nUsing namespace API:")
   print(result)

   # Method 3: Detection only
   detection_df = cleaner.detect_dataframe(df, "customer_info")
   print("\nDetection results:")
   print(detection_df)

Pandas Examples
~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   from piicleaner import Cleaner

   # Create sample DataFrame
   df = pd.DataFrame({
       "id": [1, 2, 3, 4, 5],
       "customer_info": [
           "John Smith - john@example.com",
           "Call customer at +44 20 7946 0958",
           "Address: 123 High Street, SW1A 1AA", 
           "NINO: AB123456C for tax purposes",
           "No sensitive information here",
       ],
       "category": ["email", "phone", "address", "nino", "clean"]
   })

   cleaner = Cleaner()

   # Method 1: Using cleaner methods
   cleaned_df = cleaner.clean_pandas_dataframe(df, "customer_info", "redact", "cleaned_info")
   print("Cleaned DataFrame:")
   print(cleaned_df)

   # Method 2: Using pandas accessor (requires pandas extra)
   df["redacted"] = df["customer_info"].pii.clean_pii("redact")
   df["pii_detected"] = df["customer_info"].pii.detect_pii()
   print("\nUsing accessor API:")
   print(df[["customer_info", "redacted", "pii_detected"]])

   # Method 3: Detection only
   detection_df = cleaner.detect_pandas_dataframe(df, "customer_info")
   print("\nDetection results:")
   print(detection_df)

Handling Missing Values
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   import polars as pl
   from piicleaner import Cleaner
   import numpy as np

   # DataFrame with missing values
   df_pandas = pd.DataFrame({
       "text": [
           "Email: john@example.com",
           None,
           np.nan,
           "Phone: +44 20 7946 0958",
           "",
       ]
   })

   df_polars = pl.DataFrame({
       "text": [
           "Email: john@example.com",
           None,
           None,
           "Phone: +44 20 7946 0958",
           "",
       ]
   })

   cleaner = Cleaner()

   # Both libraries handle nulls properly
   pandas_cleaned = cleaner.clean_pandas_dataframe(df_pandas, "text", "redact")
   polars_cleaned = cleaner.clean_dataframe(df_polars, "text", "redact")

   print("Pandas result:")
   print(pandas_cleaned)
   print("\nPolars result:")
   print(polars_cleaned)

Advanced Use Cases
------------------

Processing Large Datasets
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import polars as pl
   from piicleaner import Cleaner
   import time

   # Simulate large dataset
   n_rows = 100_000
   df = pl.DataFrame({
       "id": range(n_rows),
       "text": [
           f"User {i}: contact at user{i}@example.com or call +44 20 7946 {i:04d}"
           for i in range(n_rows)
       ]
   })

   cleaner = Cleaner()

   # Time the cleaning operation
   start_time = time.time()
   cleaned_df = cleaner.clean_dataframe(df, "text", "redact", "cleaned_text")
   end_time = time.time()

   print(f"Processed {n_rows:,} rows in {end_time - start_time:.2f} seconds")
   print(f"Rate: {n_rows / (end_time - start_time):,.0f} rows/second")

Multiple Column Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import polars as pl
   from piicleaner import Cleaner

   # DataFrame with multiple text columns
   df = pl.DataFrame({
       "name": ["John Smith", "Jane Doe", "Bob Wilson"],
       "email": ["john@example.com", "jane@company.org", "bob@test.net"],
       "notes": [
           "Call +44 20 7946 0958 for details",
           "Address: 123 High Street, SW1A 1AA",
           "NINO: AB123456C on file"
       ]
   })

   cleaner = Cleaner()

   # Clean multiple columns
   text_columns = ["email", "notes"]
   
   for col in text_columns:
       df = cleaner.clean_dataframe(df, col, "redact", f"{col}_cleaned")

   print("Multi-column cleaning:")
   print(df)

   # Alternative: using expressions for multiple columns at once
   result = df.with_columns([
       pl.col(col).pii.clean_pii("redact").alias(f"{col}_redacted")
       for col in text_columns
   ])
   print("\nUsing expressions:")
   print(result)

Integration with Data Pipelines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import polars as pl
   from piicleaner import Cleaner

   def process_customer_data(input_df: pl.DataFrame) -> pl.DataFrame:
       """Example data processing pipeline with PII cleaning"""
       
       cleaner = Cleaner()
       
       return (
           input_df
           # Standard data cleaning
           .filter(pl.col("customer_info").is_not_null())
           .with_columns([
               pl.col("customer_info").str.strip().alias("customer_info_clean")
           ])
           # PII detection and cleaning
           .pipe(lambda df: cleaner.clean_dataframe(
               df, "customer_info_clean", "redact", "customer_info_redacted"
           ))
           .pipe(lambda df: cleaner.detect_dataframe(
               df, "customer_info_clean", new_column_name="pii_found"
           ))
           # Add metadata
           .with_columns([
               pl.col("pii_found").list.len().alias("pii_count"),
               pl.lit("processed").alias("status")
           ])
       )

   # Sample data
   raw_data = pl.DataFrame({
       "id": [1, 2, 3, 4],
       "customer_info": [
           "  John Smith - john@example.com  ",
           None,
           "Phone: +44 20 7946 0958",
           "Clean text with no PII"
       ]
   })

   # Process the data
   processed_data = process_customer_data(raw_data)
   print("Processed data:")
   print(processed_data)