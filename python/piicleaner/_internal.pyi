"""Type stubs for the Rust _internal module"""

def detect_pii(text: str) -> list[tuple[int, int, str]]:
    """Detect PII in a string and return match information"""
    ...

def clean_pii(text: str, cleaning: str) -> str:
    """Clean PII from a string using the specified method"""
    ...

def detect_pii_with_cleaners(
    text: str, cleaners: list[str]
) -> list[tuple[int, int, str]]:
    """Detect PII with specific cleaners"""
    ...

def get_available_cleaners() -> list[str]:
    """Get list of available cleaner names"""
    ...

def detect_pii_batch(texts: list[str]) -> list[list[tuple[int, int, str]]]:
    """Vectorized detect PII for multiple texts"""
    ...

def clean_pii_batch(texts: list[str], cleaning: str) -> list[str]:
    """Vectorized clean PII for multiple texts"""
    ...

def detect_pii_with_cleaners_batch(
    texts: list[str], cleaners: list[str]
) -> list[list[tuple[int, int, str]]]:
    """Vectorized detect PII with specific cleaners for multiple texts"""
    ...

def clean_pii_with_cleaners_batch(
    texts: list[str], cleaners: list[str], cleaning: str
) -> list[str]:
    """Vectorized clean PII with specific cleaners for multiple texts"""
    ...
