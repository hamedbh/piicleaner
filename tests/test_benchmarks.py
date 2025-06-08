"""Performance benchmarks for PII detection and cleaning operations."""

import pytest
from piicleaner import Cleaner


def create_sample_strings() -> list[str]:
    """Create sample strings containing PII data."""
    return [
        "My email address is person@example.com",
        "Sophie Taylor at 1 High Street, London, W1 2BC",
        "Call me at +44 7890 123 456 urgently",
        (
            "I am owed a refund in the amount of £1,234.56. "
            "I expect payment promptly."
        ),
        "My reference number is 1234567890",
        "I am Ali Mahmood, my National Insurance number is AB123 456A",
        "Here goes: <some-sort-of-tag>",
        "The request came from 192.168.0.0",
    ]


def create_clean_strings() -> list[str]:
    """Create sample strings without PII data."""
    return [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco.",
        "Duis aute irure dolor in reprehenderit in voluptate velit esse.",
        "Excepteur sint occaecat cupidatat non proident, sunt in culpa.",
        "Nulla pariatur. At vero eos et accusamus et iusto odio dignissimos.",
        "Et harum quidem rerum facilis est et expedita distinctio.",
        "Nam libero tempore, cum soluta nobis est eligendi optio cumque.",
    ]


def generate_large_list(size: int, pii_ratio: float = 0.2) -> list[str]:
    """Generate a large list of strings with a specified ratio of PII data."""
    pii_samples = create_sample_strings()
    clean_samples = create_clean_strings()
    pii_count = int(size * pii_ratio)

    result = []

    for i in range(size):
        if i < pii_count:
            base_string = pii_samples[i % len(pii_samples)]
            replacement = i % 10
            # Modify the strings to include the counter
            modified_string = (
                base_string.replace("person", f"person{replacement}")
                .replace("W1 2BC", f"W{replacement} 2BC")
                .replace("7890", f"789{replacement}")
                .replace("1,234.56", f"1,234.5{replacement}")
                .replace("1234567890", f"12345678{replacement}0")
                .replace("AB123", f"AB12{replacement}")
                .replace("some-sort", f"some{replacement}-sort")
                .replace("168.0", f"168.{replacement}")
            )
            result.append(modified_string)
        else:
            result.append(clean_samples[i % len(clean_samples)])

    return result


@pytest.fixture
def cleaner():
    """Fixture providing a Cleaner instance."""
    return Cleaner("all")


@pytest.fixture
def sample_string():
    """Fixture providing a single sample string."""
    return create_sample_strings()[0]


@pytest.fixture
def large_string_list():
    """Fixture providing a large list of strings for batch operations."""
    return generate_large_list(100_000, 0.2)


@pytest.mark.performance
@pytest.mark.parametrize("ignore_case", [False, True])
def test_detect_individual(benchmark, cleaner, sample_string, ignore_case):
    """Benchmark individual string detection."""
    benchmark(cleaner.detect_pii, sample_string, ignore_case)


@pytest.mark.performance
@pytest.mark.parametrize("ignore_case", [False, True])
def test_detect_large_list(benchmark, cleaner, large_string_list, ignore_case):
    """Benchmark detection on large list of strings."""

    def detect_batch():
        for text in large_string_list:
            cleaner.detect_pii(text, ignore_case)

    benchmark(detect_batch)


@pytest.mark.performance
@pytest.mark.parametrize("operation", ["redact", "replace"])
@pytest.mark.parametrize("ignore_case", [False, True])
def test_clean_individual(
    benchmark, cleaner, sample_string, operation, ignore_case
):
    """Benchmark individual string cleaning operations."""
    benchmark(cleaner.clean_pii, sample_string, operation, ignore_case)


@pytest.mark.performance
@pytest.mark.parametrize("operation", ["redact", "replace"])
@pytest.mark.parametrize("ignore_case", [False, True])
def test_clean_large_list(
    benchmark, cleaner, large_string_list, operation, ignore_case
):
    """Benchmark batch cleaning operations on large lists."""
    benchmark(cleaner.clean_list, large_string_list, operation, ignore_case)
