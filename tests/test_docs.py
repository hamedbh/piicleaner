"""Run the Python code examples in the README and docs, so they can't go
stale.

Blocks in each file run in order in a shared namespace, because later
examples build on names (e.g. ``cleaner``) defined by earlier ones.
"""

import re
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent

DOC_FILES = ["README.md", "docs/quickstart.rst", "docs/examples.rst"]


def markdown_blocks(text):
    """Yield (line number, code) for each ```python block."""
    for match in re.finditer(r"^```python\n(.*?)^```", text, re.S | re.M):
        line = text.count("\n", 0, match.start()) + 2
        yield line, match.group(1)


def rst_blocks(text):
    """Yield (line number, code) for each ``.. code-block:: python``."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() == ".. code-block:: python":
            i += 1
            # Skip directive options and the blank line before the body
            while i < len(lines) and (
                not lines[i].strip() or lines[i].strip().startswith(":")
            ):
                i += 1
            start = i
            indent = len(lines[i]) - len(lines[i].lstrip())
            while i < len(lines) and (
                not lines[i].strip()
                or len(lines[i]) - len(lines[i].lstrip()) >= indent
            ):
                i += 1
            yield start + 1, textwrap.dedent("\n".join(lines[start:i]))
        else:
            i += 1


def code_blocks(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    blocks = markdown_blocks if path.endswith(".md") else rst_blocks
    return list(blocks(text))


@pytest.mark.parametrize("path", DOC_FILES)
def test_doc_has_examples(path):
    assert code_blocks(path), f"No Python examples found in {path}"


@pytest.mark.parametrize("path", DOC_FILES)
def test_doc_examples_run(path, capsys):
    namespace = {"__name__": "__doc_example__"}
    for line, code in code_blocks(path):
        try:
            exec(compile(code, f"{path}:{line}", "exec"), namespace)
        except Exception as exc:
            pytest.fail(
                f"Example at {path}:{line} raised "
                f"{type(exc).__name__}: {exc}\n\n{code}"
            )
