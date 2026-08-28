"""Shared fixtures and paths for the overheatlens-core test suite."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

CORE_ROOT = Path(__file__).resolve().parent.parent      # overheatlens-core
REPO_ROOT = CORE_ROOT.parent.parent                     # repository root
FIXTURES = REPO_ROOT / "fixtures" / "epw" / "synthetic"

if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    if not FIXTURES.exists():
        pytest.skip(f"synthetic fixtures not found at {FIXTURES}")
    return FIXTURES


@pytest.fixture()
def hours_8760() -> np.ndarray:
    """Hour-ending labels 1..24 repeating for a non-leap year."""
    return (np.arange(8760) % 24) + 1


def series_at(const_c: float, n: int = 8760, value: float | None = None,
              idx: int | None = None) -> np.ndarray:
    """Constant series, optionally with one hour overridden — for boundary tests."""
    a = np.full(n, float(const_c))
    if value is not None and idx is not None:
        a[idx] = value
    return a
