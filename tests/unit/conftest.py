"""
Global pytest configuration for mcp-knowledge-service test suite.

Forces the SlowAPI limiter to use a fresh in-memory storage backend for every
test function so that:
  1. No live Redis connection is needed (tests run offline).
  2. Rate-limit counters are completely isolated between tests (no bleed).

The SlowAPI ``Limiter`` object has *two* storage pointers that must both be
swapped:
  - ``limiter._storage``        — used by SlowAPI itself for introspection
  - ``limiter.limiter.storage`` — used by the ``limits`` strategy (FixedWindow)
                                  when ``hit()`` / ``test()`` are called

Swapping only one of these is insufficient; both must point to the same fresh
``MemoryStorage`` instance before each test.
"""

import pytest
from limits.storage import MemoryStorage


@pytest.fixture(autouse=True, scope="function")
def reset_rate_limiter():
    """
    Replace the limiter's storage with a fresh MemoryStorage before each test.
    Restores the original storage after the test so module state stays clean.
    """
    try:
        from apps.api.main import limiter

        fresh = MemoryStorage()

        # Save originals so we can restore after the test
        orig_storage = limiter._storage
        orig_strategy_storage = limiter.limiter.storage

        # Swap both pointers — both must be the same object
        limiter._storage = fresh
        limiter.limiter.storage = fresh

        yield

        # Restore originals (keeps module state clean between test sessions)
        limiter._storage = orig_storage
        limiter.limiter.storage = orig_strategy_storage
    except Exception:
        # App not importable or limiter not wired — safe to skip
        yield
