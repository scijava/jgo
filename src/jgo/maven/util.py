"""
Utility functions for Maven operations.

NOTE: Coordinate and endpoint parsing functionality has been moved to endpoint.py.
The functions in this module now wrap the new classes for backward compatibility.
For new code, consider using Coordinate and Endpoint classes directly.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

# Import new coordinate/endpoint classes and functions
from .endpoint import (
    _parse_coordinate_dict,
    _parse_endpoint_dict,
    coord2str,  # Re-export for backward compatibility
)

# Public API
__all__ = [
    "ts2dt",
    "str2coord",
    "parse_endpoint",
    "coord2str",
    "text",
    "binary",
]


def ts2dt(ts: str) -> datetime:
    """
    Convert a Maven-style timestamp string into a Python datetime object.

    Valid forms:
    * 20210702144918 (seen in <lastUpdated> in maven-metadata.xml)
    * 20210702.144917 (seen in deployed SNAPSHOT filenames and <snapshotVersion><value>)
    """
    m = re.match(r"(\d{4})(\d\d)(\d\d)\.?(\d\d)(\d\d)(\d\d)", ts)
    if not m:
        raise ValueError(f"Invalid timestamp: {ts}")
    return datetime(*map(int, m.groups()))  # noqa


def str2coord(coordinate: str) -> dict[str, str | None]:
    """
    Parses a Maven coordinate string into its components.

    This function handles multiple Maven coordinate formats using heuristics:
    - G:A (minimal - groupId and artifactId only)
    - G:A:V (basic user input)
    - G:A:P (with packaging type)
    - G:A:C (with classifier only, for latest version with classifier)
    - G:A:V:C (user input with classifier)
    - G:A:P:V (mvn dependency:get format)
    - G:A:P:V:S (mvn dependency:list format without classifier)
    - G:A:P:C:V (user input with packaging and classifier)
    - G:A:P:C:V:S (mvn dependency:list format with classifier)

    Classifiers are detected based on common patterns (natives-*, sources, javadoc, etc.).
    Versions are detected by presence of digits or known version keywords (RELEASE, LATEST).

    Args:
        coordinate: The Maven coordinate string to parse.

    Returns:
        A dictionary containing the parsed components: 'groupId', 'artifactId',
        'packaging', 'classifier', 'version', 'scope', and 'optional'.

    Note:
        This function is kept for backward compatibility. New code should use
        Coordinate.parse() which returns a Coordinate object instead of a dict.
    """
    return _parse_coordinate_dict(coordinate)


def parse_endpoint(endpoint: str) -> dict[str, any]:
    """
    Parse a complete endpoint expression into coordinates and main class.

    This function handles:
    - Multiple coordinates separated by '+' (e.g., coord1+coord2+coord3)
    - Main class specification with '@' (new format: coord1+coord2@MainClass)
    - Deprecated main class with ':@' or ':MainClass'
    - Managed dependency flag with '!' or '\\!' suffix

    Args:
        endpoint: The endpoint string to parse (e.g., "g:a:v+g2:a2:v2@MainClass")

    Returns:
        A dictionary containing:
        - 'coordinates': List of parsed coordinate dicts (from str2coord)
        - 'main_class': Main class string (None if not specified)
        - 'managed': List of booleans indicating managed status for each coordinate
        - 'deprecated_format': Boolean indicating if deprecated syntax was used

    Examples:
        >>> parse_endpoint("org.scijava:scijava-common:2.90.0")
        {'coordinates': [{'groupId': 'org.scijava', ...}], 'main_class': None, 'managed': [False], ...}

        >>> parse_endpoint("g:a:v+g2:a2:v2@org.example.Main")
        {'coordinates': [{...}, {...}], 'main_class': 'org.example.Main', 'managed': [False, False], ...}

        >>> parse_endpoint("g:a:v!+g2:a2:v2")
        {'coordinates': [{...}, {...}], 'main_class': None, 'managed': [True, False], ...}

    Note:
        This function is kept for backward compatibility. New code should use
        Endpoint.parse() which returns an Endpoint object instead of a dict.
    """
    return _parse_endpoint_dict(endpoint)


def text(p: Path) -> str:
    """Read a text file."""
    with open(p, "r") as f:
        return f.read()


def binary(p: Path) -> bytes:
    """Read a binary file."""
    with open(p, "rb") as f:
        return f.read()
