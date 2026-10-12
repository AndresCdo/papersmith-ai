"""Deterministic fixtures. Fixed seed, no data, no network.

The seed is chosen per run so that levels 2 and 3 vary between runs while
staying reproducible within one.

Backend-neutral on purpose: this file imports no array library, so it never
decides which backend the implementation computes with (`src/<Package>/
__init__.py`'s `__backend__` does). Build the backend's own generator from
`SEED` where a test needs one, e.g. `numpy.random.default_rng(SEED)` or
`torch.Generator().manual_seed(SEED)`.
"""

from __future__ import annotations

import random

import pytest

SEED = {{SEED}}
TOL = 1e-10


@pytest.fixture
def seed() -> int:
    return SEED


@pytest.fixture
def rng() -> random.Random:
    """A seeded standard-library generator; see the module docstring for a
    backend's own."""
    return random.Random(SEED)
