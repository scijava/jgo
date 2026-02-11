"""
Maven version parsing, comparison, and range utilities.

This module provides three levels of version handling:

1. SemVer Comparison (via semver library)
   - is_semver_1x() - Check if version string is valid SemVer 1.x
   - compare_semver() - Compare two SemVer strings

2. Maven Version Comparison (non-SemVer)
   - MavenVersion class - Parsed version with comparison operators
   - tokenize() - Split version into tokens per Maven spec
   - trim_nulls() - Remove trailing null values
   - compare_versions() - Compare two version strings

3. Maven Version Ranges
   - VersionRange class - Parsed range with bounds
   - parse_version_range() - Parse "[1.0,2.0)" style ranges
   - version_in_range() - Check if version satisfies range

Reference: https://maven.apache.org/pom.html#version-order-specification

See also the more general Java version handling in jgo.util.java.
"""

from __future__ import annotations

import re
from functools import total_ordering
from typing import NamedTuple

import semver

# ============================================================
# SECTION 1: SEMVER COMPARISON
#
# Maven uses SemVer 1.x rules when both versions match the
# Semantic Versioning grammar with lowercase letters only.
# ============================================================

# Regex for SemVer 1.x: no build metadata (+), lowercase only
_SEMVER_1X_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|[a-z\d-]*[a-z-][a-z\d-]*)"
    r"(?:\.(?:0|[1-9]\d*|[a-z\d-]*[a-z-][a-z\d-]*))*))?$"
)


def is_semver_1x(version: str) -> bool:
    """
    Check if version string is valid Semantic Versioning 1.x.

    SemVer 1.x differences from 2.x:
    - No build metadata (+ suffix)
    - Prerelease identifiers are dot-separated alphanumerics

    Maven uses SemVer 1.x rules when both versions match this grammar
    AND use only lowercase letters.

    Args:
        version: Version string to check

    Returns:
        True if version is valid SemVer 1.x with lowercase letters only
    """
    version = version.strip()
    if not version:
        return False

    # SemVer 2.x allows build metadata with +, but 1.x does not
    if "+" in version:
        return False

    # Maven requires lowercase for SemVer path
    if version != version.lower():
        return False

    # Check if it matches SemVer grammar
    return _SEMVER_1X_PATTERN.match(version) is not None


def compare_semver(v1: str, v2: str) -> int:
    """
    Compare two SemVer strings.

    Args:
        v1: First version string
        v2: Second version string

    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2

    Raises:
        ValueError: If either version is not valid SemVer
    """
    return semver.Version.parse(v1).compare(semver.Version.parse(v2))


# ============================================================
# SECTION 2: MAVEN VERSION COMPARISON (NON-SEMVER)
#
# Implements the Maven version ordering specification from:
# https://maven.apache.org/pom.html#version-order-specification
# ============================================================


class Token(NamedTuple):
    """
    A single version token.

    Attributes:
        value: The token value (int for numeric, str for qualifier)
        separator: The separator preceding this token ('.', '-', '_', or '')
    """

    value: int | str
    separator: str


# Qualifier ordering per Maven spec:
# alpha < beta < milestone < rc = cr < snapshot < "" = final = ga = release < sp
QUALIFIER_ORDER: dict[str, int] = {
    "alpha": -5,
    "a": -5,
    "beta": -4,
    "b": -4,
    "milestone": -3,
    "m": -3,
    "rc": -2,
    "cr": -2,
    "snapshot": -1,
    "": 0,
    "final": 0,
    "ga": 0,
    "release": 0,
    "sp": 1,
}

# Null values that get trimmed from the end
_NULL_VALUES: set[str | int] = {0, "", "final", "ga", "release"}


def tokenize(version: str) -> list[Token]:
    """
    Split version string into tokens per Maven spec.

    Splitting rules:
    1. Split on delimiters: '.', '-', '_'
    2. Split on transitions between digits and characters (treated as '-')
    3. Replace empty tokens with 0

    Args:
        version: Version string to tokenize

    Returns:
        List of Token objects with values and separators
    """
    if not version:
        return []

    tokens: list[Token] = []
    current = ""
    current_sep = ""
    prev_is_digit: bool | None = None

    for char in version:
        if char in ".-_":
            # Delimiter found - emit current token
            if current or tokens:  # Don't emit empty first token
                value = _parse_token_value(current)
                tokens.append(Token(value, current_sep))
            current = ""
            current_sep = char
            prev_is_digit = None
        elif char.isdigit():
            # Check for transition from letter to digit
            if prev_is_digit is False and current:
                value = _parse_token_value(current)
                tokens.append(Token(value, current_sep))
                current = ""
                current_sep = "-"  # Transitions are treated as hyphen
            current += char
            prev_is_digit = True
        else:
            # Check for transition from digit to letter
            if prev_is_digit is True and current:
                value = _parse_token_value(current)
                tokens.append(Token(value, current_sep))
                current = ""
                current_sep = "-"  # Transitions are treated as hyphen
            current += char
            prev_is_digit = False

    # Emit final token
    if current or tokens:
        value = _parse_token_value(current)
        tokens.append(Token(value, current_sep))

    return tokens


def _parse_token_value(s: str) -> int | str:
    """Parse token string to int if numeric, else lowercase string."""
    if not s:
        return 0
    if s.isdigit():
        return int(s)
    return s.lower()


def trim_nulls(tokens: list[Token]) -> list[Token]:
    """
    Remove trailing null values from token list.

    Null values are: 0, "", "final", "ga", "release"

    The trimming process is repeated at each remaining hyphen from end to start.
    For example: "1.0.0-foo.0.0" -> "1-foo"

    Args:
        tokens: List of tokens to trim

    Returns:
        New list with trailing nulls removed
    """
    if not tokens:
        return []

    result = list(tokens)

    # Trim from the end
    # We remove trailing nulls, and if after removal the last token is
    # preceded by a hyphen, we might need to remove it too if it becomes null
    changed = True
    while changed and result:
        changed = False
        # Remove trailing nulls
        while result and result[-1].value in _NULL_VALUES:
            result.pop()
            changed = True

    return result


def _qualifier_priority(value: str) -> tuple[int, str]:
    """
    Get qualifier priority for comparison.

    Returns tuple of (priority, value) where priority is:
    - QUALIFIER_ORDER value for known qualifiers
    - 0 for unknown qualifiers (compared alphabetically)
    """
    lower = value.lower() if isinstance(value, str) else ""
    if lower in QUALIFIER_ORDER:
        return (QUALIFIER_ORDER[lower], "")
    # Unknown qualifiers sort after known ones, alphabetically
    return (0, lower)


def compare_tokens(
    a: Token | None, b: Token | None, pad_sep_a: str = "", pad_sep_b: str = ""
) -> int:
    """
    Compare two tokens with separator context.

    Comparison rules per Maven spec:
    - When separators are the same:
      - Numeric tokens use integer ordering
      - Qualifiers use QUALIFIER_ORDER, then alphabetic
      - Numeric > Qualifier (for non-special qualifiers)
    - When separators differ:
      - .qualifier = -qualifier < -number < .number

    Args:
        a: First token (or None for padding)
        b: Second token (or None for padding)
        pad_sep_a: Separator to use if a is None (for padding)
        pad_sep_b: Separator to use if b is None (for padding)

    Returns:
        -1 if a < b, 0 if a == b, 1 if a > b
    """
    # Handle None (padding) cases
    if a is None and b is None:
        return 0

    # Get effective values and separators
    val_a = a.value if a else (0 if pad_sep_a == "." else "")
    val_b = b.value if b else (0 if pad_sep_b == "." else "")
    sep_a = a.separator if a else pad_sep_a
    sep_b = b.separator if b else pad_sep_b

    # Both numeric
    if isinstance(val_a, int) and isinstance(val_b, int):
        if sep_a == sep_b or (sep_a in ".-_" and sep_b in ".-_"):
            # Same separator type - direct numeric comparison
            # But: -number < .number when separators differ
            if sep_a != sep_b:
                # .number > -number > _number (treating _ as -)
                if sep_a == "." and sep_b in "-_":
                    return 1
                if sep_a in "-_" and sep_b == ".":
                    return -1
            return (val_a > val_b) - (val_a < val_b)
        return (val_a > val_b) - (val_a < val_b)

    # Both qualifiers (strings)
    if isinstance(val_a, str) and isinstance(val_b, str):
        prio_a = _qualifier_priority(val_a)
        prio_b = _qualifier_priority(val_b)
        if prio_a[0] != prio_b[0]:
            return (prio_a[0] > prio_b[0]) - (prio_a[0] < prio_b[0])
        # Same priority - compare alphabetically
        return (prio_a[1] > prio_b[1]) - (prio_a[1] < prio_b[1])

    # Mixed: one numeric, one qualifier
    # Rule: .qualifier = -qualifier < -number < .number
    if isinstance(val_a, int):
        # a is numeric, b is qualifier
        # -number > qualifier, .number > qualifier
        return 1
    else:
        # a is qualifier, b is numeric
        return -1


@total_ordering
class MavenVersion:
    """
    A Maven version parsed into tokens for comparison.

    Implements the full Maven version ordering specification from:
    https://maven.apache.org/pom.html#version-order-specification

    Examples:
        >>> MavenVersion("1.0") < MavenVersion("1.1")
        True
        >>> MavenVersion("1.0-alpha") < MavenVersion("1.0")
        True
        >>> MavenVersion("1.0") == MavenVersion("1.0.0")
        True
    """

    def __init__(self, version_string: str):
        """
        Parse version string into comparable form.

        Args:
            version_string: Maven version string
        """
        self._original = version_string
        self._tokens = trim_nulls(tokenize(version_string))

    @property
    def tokens(self) -> list[Token]:
        """Get the parsed and trimmed tokens."""
        return self._tokens

    def __str__(self) -> str:
        return self._original

    def __repr__(self) -> str:
        return f"MavenVersion({self._original!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MavenVersion):
            return NotImplemented
        return self._compare(other) == 0

    def __lt__(self, other: MavenVersion) -> bool:
        if not isinstance(other, MavenVersion):
            return NotImplemented
        return self._compare(other) < 0

    def __hash__(self) -> int:
        # Hash based on trimmed tokens for consistency with __eq__
        return hash(tuple(self._tokens))

    def _compare(self, other: MavenVersion) -> int:
        """Compare with another MavenVersion. Returns -1, 0, or 1."""
        tokens_a = self._tokens
        tokens_b = other._tokens
        max_len = max(len(tokens_a), len(tokens_b))

        for i in range(max_len):
            tok_a = tokens_a[i] if i < len(tokens_a) else None
            tok_b = tokens_b[i] if i < len(tokens_b) else None

            # Padding separator comes from the corresponding position in the
            # longer version (per Maven spec)
            pad_sep_a = tokens_b[i].separator if i < len(tokens_b) else "."
            pad_sep_b = tokens_a[i].separator if i < len(tokens_a) else "."

            result = compare_tokens(tok_a, tok_b, pad_sep_a, pad_sep_b)
            if result != 0:
                return result

        return 0


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two Maven version strings.

    Uses SemVer comparison if both versions are valid SemVer 1.x,
    otherwise falls back to Maven's complex algorithm.

    Args:
        v1: First version string
        v2: Second version string

    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2
    """
    v1 = v1.strip()
    v2 = v2.strip()

    # Try SemVer fast path
    if is_semver_1x(v1) and is_semver_1x(v2):
        return compare_semver(v1, v2)

    # Fall back to Maven comparison
    mv1 = MavenVersion(v1)
    mv2 = MavenVersion(v2)

    if mv1 < mv2:
        return -1
    elif mv1 > mv2:
        return 1
    return 0


# ============================================================
# SECTION 3: MAVEN VERSION RANGES
#
# Parse and evaluate Maven dependency version range expressions.
# ============================================================


class VersionRange(NamedTuple):
    """
    A Maven version range specification.

    Attributes:
        lower: Lower bound version string, or None for unbounded
        upper: Upper bound version string, or None for unbounded
        lower_inclusive: True for '[', False for '('
        upper_inclusive: True for ']', False for ')'
    """

    lower: str | None
    upper: str | None
    lower_inclusive: bool
    upper_inclusive: bool


def parse_version_range(range_spec: str) -> VersionRange:
    """
    Parse Maven version range specification.

    Supports:
        - Inclusive range: "[1.0,2.0]"
        - Exclusive range: "(1.0,2.0)"
        - Mixed: "[1.0,2.0)"
        - Unbounded lower: "(,2.0]"
        - Unbounded upper: "[1.0,)"
        - Exact version: "[1.0]" (equivalent to "[1.0,1.0]")
        - Soft requirement: "1.0" (returns unbounded range, caller handles)

    Args:
        range_spec: Maven-style version range string

    Returns:
        VersionRange with parsed bounds and inclusivity

    Raises:
        ValueError: If range syntax is invalid
    """
    range_spec = range_spec.strip()
    if not range_spec:
        raise ValueError("Empty range specification")

    # Check if this is a range syntax (starts with bracket)
    if not (range_spec.startswith("[") or range_spec.startswith("(")):
        # Check for invalid bracket characters
        if range_spec[0] in "{<":
            raise ValueError(f"Invalid opening bracket: {range_spec[0]}")
        # Soft requirement - any version acceptable, prefer this one
        # Return unbounded range; caller should handle preference logic
        return VersionRange(None, None, False, False)

    # Parse range syntax
    if len(range_spec) < 3:
        raise ValueError(f"Invalid range syntax: {range_spec}")

    # Extract opening bracket
    if range_spec[0] == "[":
        lower_inclusive = True
    elif range_spec[0] == "(":
        lower_inclusive = False
    else:
        raise ValueError(f"Invalid opening bracket: {range_spec[0]}")

    # Extract closing bracket
    if range_spec[-1] == "]":
        upper_inclusive = True
    elif range_spec[-1] == ")":
        upper_inclusive = False
    else:
        raise ValueError(f"Invalid closing bracket: {range_spec[-1]}")

    # Extract bounds (strip brackets)
    bounds_str = range_spec[1:-1]

    # Handle exact version: "[1.0]" -> "[1.0,1.0]"
    if "," not in bounds_str:
        version = bounds_str.strip()
        if not version:
            raise ValueError(f"Empty version in range: {range_spec}")
        return VersionRange(version, version, lower_inclusive, upper_inclusive)

    # Split on comma
    parts = bounds_str.split(",", 1)
    lower_str = parts[0].strip()
    upper_str = parts[1].strip()

    # Parse bounds (empty string means unbounded)
    lower_bound = lower_str if lower_str else None
    upper_bound = upper_str if upper_str else None

    return VersionRange(lower_bound, upper_bound, lower_inclusive, upper_inclusive)


def version_in_range(version: str, range_spec: str | VersionRange) -> bool:
    """
    Check if version satisfies the given range.

    Args:
        version: Version string to check
        range_spec: Range specification string or VersionRange object

    Returns:
        True if version is within range, False otherwise
    """
    if isinstance(range_spec, str):
        vr = parse_version_range(range_spec)
    else:
        vr = range_spec

    # Unbounded range (soft requirement) matches everything
    if vr.lower is None and vr.upper is None:
        return True

    # Check lower bound
    if vr.lower is not None:
        cmp = compare_versions(version, vr.lower)
        if vr.lower_inclusive:
            if cmp < 0:
                return False
        else:
            if cmp <= 0:
                return False

    # Check upper bound
    if vr.upper is not None:
        cmp = compare_versions(version, vr.upper)
        if vr.upper_inclusive:
            if cmp > 0:
                return False
        else:
            if cmp >= 0:
                return False

    return True
