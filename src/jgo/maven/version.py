"""
Maven version parsing, comparison, and range utilities.

This module provides four levels of version handling:

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

4. Java Version Handling
   - JavaVersion - NamedTuple for JVM versions
   - parse_java_version() - Handle old-style "1.8" format
   - parse_jdk_activation_range() - JDK profile activation ranges
   - version_matches_jdk_range() - Check JDK activation

Reference: https://maven.apache.org/pom.html#version-order-specification
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


# ============================================================
# SECTION 4: JAVA VERSION HANDLING
#
# Special handling for Java/JVM version strings and JDK profile
# activation ranges. These differ from general Maven versions:
# - Old-style "1.8" format maps to Java 8
# - JDK activation uses PREFIX matching for simple versions
# ============================================================


class JavaVersion(NamedTuple):
    """
    Semantic representation for Java runtime versions.

    This is specifically for JVM version detection, NOT for
    Maven artifact versions.

    Attributes:
        major: Major version (e.g., 8, 11, 17)
        minor: Minor version (default 0)
        patch: Patch version (default 0)
    """

    major: int
    minor: int = 0
    patch: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def parse_java_version(version: str) -> JavaVersion:
    """
    Parse Java runtime version string.

    Handles JVM-specific formats:
    - Old: "1.8.0_292" -> JavaVersion(8, 0, 292)
    - New: "17.0.2" -> JavaVersion(17, 0, 2)

    Args:
        version: Java version string

    Returns:
        JavaVersion with major, minor, patch components

    Raises:
        ValueError: If version string is invalid or cannot be parsed
    """
    version = version.strip()
    if not version:
        raise ValueError("Empty version string")

    try:
        # Check if old format (1.x.y_z)
        if version.startswith("1."):
            parts = version.split(".")
            if len(parts) < 2:
                raise ValueError(f"Invalid old-format version: {version}")

            # Extract major version from second component
            major = int(parts[1].split("_")[0])

            # Extract patch/minor from remaining parts
            minor = 0
            patch = 0

            if len(parts) >= 3:
                # Handle third component (could have underscore for patch)
                third_parts = parts[2].split("_")
                minor = int(third_parts[0]) if third_parts[0] else 0
                patch = int(third_parts[1]) if len(third_parts) > 1 else 0
            elif "_" in parts[1]:
                # Handle 1.8_292 format
                _, patch_str = parts[1].split("_", 1)
                patch = int(patch_str)

            return JavaVersion(major, minor, patch)
        else:
            # New format (x.y.z)
            parts = version.split(".")
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0

            return JavaVersion(major, minor, patch)
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid version string '{version}': {e}")


def parse_jdk_activation_range(
    range_spec: str,
) -> tuple[JavaVersion | None, JavaVersion | None, bool, bool]:
    """
    Parse JDK profile activation range specification.

    This implements Maven's JDK profile activation semantics, which
    differ from general version ranges:

    - Simple versions use PREFIX MATCHING: "11" matches 11.x.x
    - Range syntax follows Maven conventions: "[1.8,11)"

    NOTE: This is NOT the same as dependency version ranges.

    Supports various range formats:
        - Simple version: "8" or "1.8" -> prefix match (e.g., 1.8 matches 1.8.x)
        - Inclusive range: "[1.8,11]" -> both bounds inclusive
        - Exclusive range: "(1.8,11)" -> both bounds exclusive
        - Mixed range: "[1.8,11)" -> lower inclusive, upper exclusive
        - Unbounded lower: "(,8]" -> no lower bound
        - Unbounded upper: "[11,)" -> no upper bound

    Args:
        range_spec: Maven-style version range string

    Returns:
        Tuple of (lower_bound, upper_bound, lower_inclusive, upper_inclusive)
        where bounds are JavaVersion or None for unbounded ranges

    Raises:
        ValueError: If range syntax is invalid or lower > upper
    """
    range_spec = range_spec.strip()
    if not range_spec:
        raise ValueError("Empty range specification")

    # Check if this is a range syntax (starts with bracket)
    if not (range_spec.startswith("[") or range_spec.startswith("(")):
        # Simple version - check if patch version was specified
        # If no patch (e.g., "1.8", "11"), treat as prefix match
        # If patch specified (e.g., "1.8.0_292"), treat as exact match
        orig_spec = range_spec.strip()
        version = parse_java_version(range_spec)

        # Check if original spec had patch component
        # For old format: "1.8.0_292" has patch, "1.8" doesn't
        # For new format: "11.0.1" has patch, "11" doesn't
        has_patch = False
        if orig_spec.startswith("1."):
            # Old format: check for third dot or underscore
            parts = orig_spec.split(".")
            if len(parts) >= 3 or (len(parts) >= 2 and "_" in parts[1]):
                has_patch = True
        else:
            # New format: check for two dots
            if orig_spec.count(".") >= 2:
                has_patch = True

        if has_patch:
            # Exact match
            return (version, version, True, True)
        else:
            # Prefix match: match all versions with same major version
            # e.g., "1.8" matches [8.0.0, 9.0.0) - all Java 8 versions
            # e.g., "11" matches [11.0.0, 12.0.0) - all Java 11 versions
            lower = version
            upper = JavaVersion(version.major + 1, 0, 0)
            return (lower, upper, True, False)

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
    if "," not in bounds_str:
        raise ValueError(f"Range must contain comma: {range_spec}")

    # Split on comma
    parts = bounds_str.split(",", 1)
    lower_str = parts[0].strip()
    upper_str = parts[1].strip()

    # Parse bounds (empty string means unbounded)
    lower_bound = parse_java_version(lower_str) if lower_str else None
    upper_bound = parse_java_version(upper_str) if upper_str else None

    # Validate: if both bounds present, lower must be <= upper
    if lower_bound is not None and upper_bound is not None:
        if lower_bound > upper_bound:
            raise ValueError(
                f"Lower bound {lower_bound} > upper bound {upper_bound} in {range_spec}"
            )

    return (lower_bound, upper_bound, lower_inclusive, upper_inclusive)


def version_matches_jdk_range(
    version: JavaVersion,
    lower: JavaVersion | None,
    upper: JavaVersion | None,
    lower_inclusive: bool,
    upper_inclusive: bool,
) -> bool:
    """
    Check if Java version matches JDK activation range.

    Uses lexicographic tuple comparison for semantic versioning.

    Args:
        version: The Java version to check
        lower: Lower bound or None for unbounded
        upper: Upper bound or None for unbounded
        lower_inclusive: Whether lower bound is inclusive
        upper_inclusive: Whether upper bound is inclusive

    Returns:
        True if version is in range, False otherwise
    """
    # Check lower bound
    if lower is not None:
        if lower_inclusive:
            if version < lower:
                return False
        else:
            if version <= lower:
                return False

    # Check upper bound
    if upper is not None:
        if upper_inclusive:
            if version > upper:
                return False
        else:
            if version >= upper:
                return False

    return True
