"""SHA-256 hashing helpers — the basis of all file provenance."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 hex digest of a file, streaming in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest of a bytes object."""
    return hashlib.sha256(data).hexdigest()
