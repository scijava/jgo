"""
Utility functions for file I/O.
"""

from pathlib import Path


def text(p: Path) -> str:
    """Read a text file."""
    with open(p, "r") as f:
        return f.read()


def binary(p: Path) -> bytes:
    """Read a binary file."""
    with open(p, "rb") as f:
        return f.read()
