# Try to speed up the build with some mocking
import os
import sys
from unittest.mock import MagicMock

# Mock Rust extensions when building on Read the Docs
if os.environ.get("READTHEDOCS"):

    class MockCleaner(MagicMock):
        def __init__(self, cleaners="all", replace_string=None):
            super().__init__()

        def clean_pii(self, text, method, ignore_case=True):
            return "[mocked]"

        def detect_pii(self, text, ignore_case=True):
            return []

        @classmethod
        def get_available_cleaners(cls):
            return [
                "address",
                "case-id",
                "cash-amount",
                "email",
                "ip_address",
                "nino",
                "postcode",
                "tag",
                "telephone",
            ]

    mock_piicleaner = MagicMock()
    mock_piicleaner.Cleaner = MockCleaner
    sys.modules["piicleaner"] = mock_piicleaner
    sys.modules["piicleaner._cleaner"] = MagicMock()
    sys.modules["piicleaner._internal"] = MagicMock()
    sys.modules["piicleaner._pandas"] = MagicMock()
    sys.modules["piicleaner._polars"] = MagicMock()

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "PIICleaner"
copyright = "2025, Hamed Bastan-Hagh"
author = "Hamed Bastan-Hagh"
release = "0.4.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

# -- Extension configuration -------------------------------------------------

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "polars": ("https://docs.pola.rs/py-polars/html/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

# MyST parser settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

# Generate anchors for headings automatically
myst_heading_anchors = 3
