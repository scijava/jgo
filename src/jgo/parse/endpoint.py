"""
Parsing and representation of Maven endpoint expressions.

An endpoint is a complete expression specifying one or more Maven coordinates
with an optional main class to execute. Endpoints support:
- Multiple coordinates joined with '+' (e.g., coord1+coord2+coord3)
- Main class specification with '@' (e.g., g:a:v@MainClass)
- Raw/unmanaged flags with '!' suffix (always disables dependency management for that coordinate)
- Deprecated legacy formats (':MainClass' and ':@MainClass')

This module provides simple data structures for representing parsed endpoints.
It does not handle Maven resolution or dependency management - for that,
see the jgo.maven subpackage.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass

from .coordinate import Coordinate, _parse_coordinate_dict


def _normalize_endpoint_syntax(endpoint: str) -> tuple[str, bool]:
    """
    Normalize deprecated @ syntax to modern format.

    Modern format: coord1+coord2+...@MainClass
    Deprecated formats:
      - coord@Main+coord2  (middle @)
      - coord:@Main        (old :@ syntax)

    Args:
        endpoint: The endpoint string to normalize

    Returns:
        Tuple of (normalized_endpoint, was_deprecated)

    Raises:
        ValueError: If multiple @ declarations are found
    """
    at_count = endpoint.count("@")

    if at_count == 0:
        return endpoint, False

    if at_count > 1:
        raise ValueError(
            "Multiple main class declarations are not supported. "
            "Use: coord1+coord2@MainClass (not coord1@Main1+coord2@Main2)"
        )

    # Single @: normalize position
    # Pattern: ([^@]*?):?(@[^+!]*)(.*) -> \1\3\2
    # Group 1: Everything before @ (non-greedy)
    # :? : Optional colon (for :@ syntax)
    # Group 2: @ and main class (up to + or !)
    # Group 3: Everything after
    # Replacement: Put group 2 (the @MainClass) at the end
    normalized = re.sub(r"([^@]*?):?(@[^+!]*)(.*)", r"\1\3\2", endpoint)
    was_deprecated = normalized != endpoint

    return normalized, was_deprecated


@dataclass
class Endpoint:
    """
    Represents a complete endpoint expression.

    An endpoint consists of:
    - coordinates: List of Coordinate objects (each may have raw=True for ! suffix)
    - main_class: Optional main class to execute
    - deprecated_format: Whether deprecated syntax was used
    """

    coordinates: list[Coordinate]
    main_class: str | None = None
    deprecated_format: bool = False

    def __str__(self) -> str:
        """Return string representation of the endpoint."""
        # Each coordinate handles its own ! suffix via coord.raw
        coord_strs = [str(coord) for coord in self.coordinates]

        result = "+".join(coord_strs)
        if self.main_class:
            result += f"@{self.main_class}"
        return result

    def __repr__(self) -> str:
        """Return detailed representation."""
        raw_count = sum(1 for c in self.coordinates if c.raw)
        return (
            f"<Endpoint coords={len(self.coordinates)} "
            f"main={self.main_class or 'None'} "
            f"raw={raw_count}/{len(self.coordinates)}>"
        )

    @classmethod
    def parse(cls, endpoint: "Endpoint" | str) -> "Endpoint":
        """
        Parse a complete endpoint expression.

        Modern format:
        - coord1+coord2+coord3@MainClass
        - Coordinates separated by '+'
        - Main class at the end with '@'
        - Raw/unmanaged flag per coordinate with '!'

        Deprecated formats (supported with warning):
        - coord@Main+coord2 (middle @)
        - coord:@MainClass (old :@ syntax)
        - coord:MainClass (old : syntax)

        Args:
            endpoint: The endpoint string to parse (e.g., "g:a:v+g2:a2:v2@MainClass")

        Returns:
            An Endpoint object.

        Examples:
            >>> Endpoint.parse("org.scijava:scijava-common:2.90.0")
            <Endpoint coords=1 main=None raw=0/1>

            >>> Endpoint.parse("g:a:v+g2:a2:v2@org.example.Main")
            <Endpoint coords=2 main=org.example.Main raw=0/2>

            >>> Endpoint.parse("g:a:v!+g2:a2:v2")
            <Endpoint coords=2 main=None raw=1/2>
        """
        if isinstance(endpoint, cls):
            return endpoint

        # Normalize deprecated @ syntax
        normalized, was_deprecated_at = _normalize_endpoint_syntax(endpoint)

        if was_deprecated_at:
            warnings.warn(
                f"Deprecated main class syntax: '{endpoint}'. "
                f"Use '{normalized}' instead. "
                f"The '@MainClass' should be at the end of the endpoint.",
                DeprecationWarning,
                stacklevel=2,
            )

        # Parse with clean v2 logic
        parsed = _parse_endpoint_dict(normalized)
        coordinates = [
            Coordinate(
                groupId=c["groupId"],
                artifactId=c["artifactId"],
                version=c["version"],
                classifier=c["classifier"],
                packaging=c["packaging"],
                scope=c["scope"],
                optional=c["optional"],
                raw=c["raw"],
            )
            for c in parsed["coordinates"]
        ]
        return cls(
            coordinates=coordinates,
            main_class=parsed["main_class"],
            deprecated_format=parsed["deprecated_format"] or was_deprecated_at,
        )


def _parse_endpoint_dict(endpoint: str) -> dict:
    """
    Parse a complete endpoint expression into a dictionary.

    This is the internal implementation that returns a dict.
    External callers should use Endpoint.parse() instead.

    Assumes the endpoint has been normalized by _normalize_endpoint_syntax(),
    so '@MainClass' (if present) is always at the end.
    """
    main_class = None
    deprecated_format = False
    coordinates_part = endpoint

    # Simple split on last @ (if present)
    if "@" in endpoint:
        coordinates_part, main_class = endpoint.rsplit("@", 1)

    # Split coordinates by +
    coord_parts = coordinates_part.split("+")
    coordinates = []

    for part in coord_parts:
        if not part:
            continue

        # Check for deprecated :MainClass format in first coordinate
        # (This is the only remaining deprecated format to handle here)
        if len(coordinates) == 0 and main_class is None:
            tokens = part.split(":")
            if len(tokens) >= 3:
                last_token = tokens[-1]
                if "." in last_token or (last_token and last_token[0].isupper()):
                    if not re.search(r"\d", last_token):
                        deprecated_format = True
                        warnings.warn(
                            "The ':mainClass' syntax is deprecated. "
                            "Use 'coord1+coord2@mainClass' instead.",
                            DeprecationWarning,
                            stacklevel=2,
                        )
                        main_class = last_token
                        part = ":".join(tokens[:-1])

        # Parse coordinate (handles the ! suffix internally)
        try:
            parsed_coord = _parse_coordinate_dict(part)
            coordinates.append(parsed_coord)
        except ValueError:
            continue

    return {
        "coordinates": coordinates,
        "main_class": main_class,
        "deprecated_format": deprecated_format,
    }
