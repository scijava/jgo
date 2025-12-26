"""Maven version parsing and comparison utilities for profile activation."""

from typing import NamedTuple


class JavaVersion(NamedTuple):
    """Semantic version representation for Java versions."""

    major: int
    minor: int
    patch: int

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


def parse_java_version(version: str) -> JavaVersion:
    """
    Parse Java version string to semantic version.

    Handles both old format (1.x.y) and new format (x.y.z).

    Examples:
        "1.8" → JavaVersion(8, 0, 0)
        "1.8.0_292" → JavaVersion(8, 0, 292)
        "8" → JavaVersion(8, 0, 0)
        "11" → JavaVersion(11, 0, 0)
        "11.0.1" → JavaVersion(11, 0, 1)
        "17.0.2" → JavaVersion(17, 0, 2)

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


def parse_version_range(
    range_spec: str,
) -> tuple[JavaVersion | None, JavaVersion | None, bool, bool]:
    """
    Parse Maven version range specification.

    Supports various range formats:
        - Simple version: "8" or "1.8" → prefix match (e.g., 1.8 matches 1.8.x)
        - Inclusive range: "[1.8,11]" → both bounds inclusive
        - Exclusive range: "(1.8,11)" → both bounds exclusive
        - Mixed range: "[1.8,11)" → lower inclusive, upper exclusive
        - Unbounded lower: "(,8]" → no lower bound
        - Unbounded upper: "[11,)" → no upper bound

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


def version_matches_range(
    version: JavaVersion,
    lower: JavaVersion | None,
    upper: JavaVersion | None,
    lower_inclusive: bool,
    upper_inclusive: bool,
) -> bool:
    """
    Check if version falls within specified range.

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
