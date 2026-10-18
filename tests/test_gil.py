"""Tests that the batch functions release the GIL while they work."""

import itertools
import threading
import time

import pytest
from piicleaner import _internal

# Long texts with little PII, so the regex work (done without the GIL)
# outweighs converting the inputs and results (done with it)
TEXTS = [
    "Nothing sensitive here, just some ordinary words. " * 200
    + "Contact john@example.com or call 07700 900123"
] * 4_000
CLEANERS = _internal.get_available_cleaners()


def longest_stall(call):
    """Run `call` while another thread ticks, and return the longest time
    the ticking thread went without running, and how long `call` took."""
    ticks = []
    started = threading.Event()
    stop = threading.Event()

    def tick():
        started.set()
        while not stop.is_set():
            ticks.append(time.perf_counter())
            time.sleep(0.001)

    ticker = threading.Thread(target=tick)
    ticker.start()
    started.wait()
    t0 = time.perf_counter()
    call()
    t1 = time.perf_counter()
    stop.set()
    ticker.join()
    gaps = [b - a for a, b in itertools.pairwise(ticks) if b > t0 and a < t1]
    return max(gaps), t1 - t0


@pytest.mark.parametrize(
    "call",
    [
        lambda: _internal.detect_pii_batch(TEXTS, True),
        lambda: _internal.detect_pii_with_cleaners_batch(TEXTS, CLEANERS, True),
        lambda: _internal.clean_pii_batch(TEXTS, "redact", True, None),
        lambda: _internal.clean_pii_with_cleaners_batch(
            TEXTS, CLEANERS, "redact", True, None
        ),
    ],
    ids=[
        "detect_pii_batch",
        "detect_pii_with_cleaners_batch",
        "clean_pii_batch",
        "clean_pii_with_cleaners_batch",
    ],
)
def test_batch_releases_gil(call):
    """Other Python threads keep running during a batch call. Converting
    the list to and from Python needs the GIL, so they're paused for part
    of the call, but not all of it."""
    stall, duration = longest_stall(call)
    assert stall < duration / 2
