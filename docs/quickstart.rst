Quickstart Guide
================

This guide will get you up and running with PIICleaner quickly.

Installation
------------

Basic installation:

.. code-block:: bash

   # Using uv
   uv add piicleaner

   # Using  pip
   pip install piicleaner

With optional dependencies:

.. code-block:: bash

   # Using uv
   # With Polars support
   uv add 'piicleaner[polars]'
   # With Pandas support
   uv add 'piicleaner[pandas]'
   
   # Using  pip
   # With Polars support
   pip install 'piicleaner[polars]'
   # With Pandas support  
   pip install 'piicleaner[pandas]'

Platform Support
~~~~~~~~~~~~~~~~

PIICleaner provides pre-built wheels for:

- **Windows**: x86_64 (Intel/AMD 64-bit)
- **macOS**: x86_64 (Intel) and arm64 (Apple Silicon)  
- **Linux**: x86_64 (Intel/AMD 64-bit)

**Note**: Linux ARM64 (aarch) wheels are not currently provides. Users on ARM64 Linux systems (e.g. Raspberry Pi, AWS Graviton) will need to build from source. See Building from Source below.

Building from Source
~~~~~~~~~~~~~~~~~~~~

For platforms without pre-built wheels you'll need:

- Rust toolchain (1.70 or newer), install from `rustup.rs <https://rustup.rs>`_
- Python development headers

.. code-block:: bash

   # Using uv
   uv add piicleaner --no-binary piicleaner

   # Using  pip
   pip install piicleaner --no-binary piicleaner

Basic Usage
-----------

Single String Processing
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

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
   #  {'start': 41, 'end': 58, 'text': '+44 20 7946 0958', 'type': 'telephone'}]

   # Case-sensitive detection
   matches_sensitive = cleaner.detect_pii("nino: ab123456c", ignore_case=False)
   print(matches_sensitive)  # [] - no match because NINO pattern expects uppercase

   matches_insensitive = cleaner.detect_pii("nino: ab123456c", ignore_case=True)
   print(matches_insensitive)  # [{'start': 6, 'end': 15, 'text': 'ab123456c', 'type': 'nino'}]

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Process multiple strings at once
   texts = [
       "Email me at alice@company.com",
       "NINO: AB123456C",
       "Call +44 20 7946 0958"
   ]

   # Clean all texts
   cleaned_texts = cleaner.clean_pii_list(texts, "redact")
   print(cleaned_texts)

   # Detect PII in all texts
   all_matches = cleaner.detect_pii_list(texts)
   print(all_matches)

DataFrame Integration
---------------------

Polars DataFrames
~~~~~~~~~~~~~~~~~

.. code-block:: python

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

   # Using namespace API
   result = df.with_columns(
       pl.col("text").pii.clean_pii("redact").alias("cleaned")
   )

Pandas DataFrames  
~~~~~~~~~~~~~~~~~

.. code-block:: python

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

   # Clean PII in DataFrame
   cleaned_df = cleaner.clean_pandas_dataframe(df, "text", "redact", "cleaned_text")
   print(cleaned_df)

   # Detect PII in DataFrame  
   pii_df = cleaner.detect_pandas_dataframe(df, "text")
   print(pii_df)

   # Using Series accessor API
   df["cleaned"] = df["text"].pii.clean_pii("redact")
   df["pii_detected"] = df["text"].pii.detect_pii()

Customization
-------------

Specific PII Types
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Use specific cleaners
   email_cleaner = Cleaner(cleaners=["email"])
   phone_cleaner = Cleaner(cleaners=["telephone", "postcode"])

   # Case-insensitive cleaning with specific cleaners
   text = "EMAIL: JOHN@EXAMPLE.COM"
   cleaned = email_cleaner.clean_pii(text, "redact", ignore_case=True)
   print(cleaned)  # "EMAIL: [email-redacted]"

Custom Replacement Strings
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Custom replacement string
   custom_cleaner = Cleaner(replace_string="[CONFIDENTIAL]")
   text = "Contact john@example.com"
   replaced = custom_cleaner.clean_pii(text, "replace")
   print(replaced)  # "[CONFIDENTIAL]"

Available PII Types
-------------------

.. code-block:: python

   # See available cleaners
   print(Cleaner.get_available_cleaners())
   # ['address', 'case-id', 'cash-amount', 'email', 'ip_address', 'nino', 'postcode', 'tag', 'telephone']

========================  =============================================  ===================
Type                      Description                                    Example
========================  =============================================  ===================
``email``                 Email addresses                                john@example.com
``telephone``             UK phone numbers                               +44 20 7946 0958  
``postcode``              UK postcodes                                   SW1A 1AA
``nino``                  National Insurance numbers                     AB123456C
``address``               Street addresses                               123 High Street
``cash-amount``           Currency amounts                               £1,500, $2000
``case-id``               Case/reference IDs                             UUIDs, reference numbers
``tag``                   HTML/XML tags                                  <script>, <div>
``ip_address``            IP addresses                                   192.168.1.1
========================  =============================================  ===================

Cleaning Methods
----------------

PIICleaner supports two cleaning methods:

**"redact"**
  Redact the PII, replacing it with semantic labels like ``[email-redacted]``, ``[telephone-redacted]``

**"replace"** 
  Replace the entire string if *any* PII is detected (uses custom replacement string if provided)

.. code-block:: python

   text = "Contact john@example.com for details"
   
   # Redact method
   redacted = cleaner.clean_pii(text, "redact")
   print(redacted)  # "Contact [email-redacted] for details"
   
   # Replace method
   replaced = cleaner.clean_pii(text, "replace")
   print(replaced)  # "[PII detected, text redacted]"

Case Sensitivity
----------------

By default, PIICleaner performs **case-insensitive** matching to catch PII regardless of how it's formatted:

- ``ignore_case=True`` (default): Detects ``ab123456c``, ``AB123456C``, and ``Ab123456C`` as valid NINOs
- ``ignore_case=False``: Only detects patterns matching the exact case defined in regex patterns

This ensures maximum PII detection while allowing precise control when needed.