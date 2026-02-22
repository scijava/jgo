"""
Parsing and representation of Maven coordinates.

A Maven coordinate identifies an artifact in a Maven repository,
or a dependency declaration in a Maven component dependency graph.

This module handles parsing various Maven coordinate formats using heuristics:
- G:A (minimal - groupId and artifactId only)
- G:A:V (basic user input)
- G:A:P:V (with packaging type)
- G:A:P:C:V (with classifier)
- G:A:P:C:V:S (full format with scope)
- Other orderings of these - see the Coordinate.parse function for details

Explicit Positioning (Strict Mode):
To avoid heuristic ambiguity, use empty strings (consecutive colons) to specify
exact positions. When empty strings are detected, the parser uses strict positional
format: G:A:V:C:P:S

Examples:
- "org.example:my-lib:1.0.0:"      → version=1.0.0, classifier=None (explicit)
- "org.example:my-lib::sources"    → version=None, classifier=sources (explicit)
- "org.example:my-lib:1.0::pom"    → version=1.0, packaging=pom (skip classifier)
- "junit:junit:4.13:::test"        → version=4.13, scope=test (skip C and P)

The Coordinate class is a simple data structure for holding parsed coordinate
components. It does not perform Maven resolution, version interpolation, or
dependency management - for that, see the jgo.maven subpackage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ..styles import STYLES, format_tokens, styled

# Default coordinate component values that are suppressed
# in CLI display unless --full-coordinates is used.
DEFAULT_PACKAGING = "jar"
DEFAULT_SCOPE = "compile"

FULL_COORDINATES: bool = False


def set_full_coordinates(value: bool) -> None:
    global FULL_COORDINATES
    FULL_COORDINATES = value


@dataclass
class Coordinate:
    """
    Represents a single Maven coordinate.

    A coordinate consists of:
    - groupId: The Maven group ID (e.g., 'org.scijava')
    - artifactId: The Maven artifact ID (e.g., 'scijava-common')
    - version: The version (e.g., '2.90.0', 'RELEASE', or None)
    - classifier: Optional classifier (e.g., 'natives-linux', 'sources')
    - packaging: The packaging type (e.g., 'jar', 'pom', 'war')
    - scope: The dependency scope (e.g., 'compile', 'runtime', 'test')
    - optional: Whether this is an optional dependency
    - raw: Maven-specific resolution mode (None=auto, True=raw, False=managed)
    - placement: Module path placement (None=auto, "class-path", "module-path")
    """

    groupId: str
    artifactId: str
    version: str | None = None
    classifier: str | None = None
    packaging: str | None = None
    scope: str | None = None
    optional: bool = False
    raw: bool | None = None
    placement: Literal["class-path", "module-path"] | None = None

    def __str__(self) -> str:
        """Return plain string representation using coord2str."""
        return coord2str(
            self.groupId,
            self.artifactId,
            self.version,
            self.classifier,
            self.packaging,
            self.scope,
            self.optional,
            self.raw,
            self.placement,
        )

    @classmethod
    def parse(cls, coordinate: "Coordinate" | str) -> "Coordinate":
        """
        Parse a Maven coordinate string into a Coordinate object.

        This handles multiple Maven coordinate formats using heuristics:
        - G:A (minimal - groupId and artifactId only)
        - G:A:V (basic user input)
        - G:A:P (with packaging type)
        - G:A:C (with classifier only, for latest version with classifier)
        - G:A:V:C (user input with classifier)
        - G:A:P:V (mvn dependency:get format)
        - G:A:P:V:S (mvn dependency:list format without classifier)
        - G:A:P:C:V (user input with packaging and classifier)
        - G:A:P:C:V:S (mvn dependency:list format with classifier)

        Args:
            coordinate: The Maven coordinate string to parse.

        Returns:
            A Coordinate object with the parsed components.

        Raises:
            ValueError: If the coordinate string is invalid.
        """
        if isinstance(coordinate, cls):
            return coordinate
        # At this point, coordinate must be a str
        assert isinstance(coordinate, str), (
            "coordinate must be str after isinstance check"
        )
        parsed = _parse_coordinate_dict(coordinate)
        group_id = parsed["groupId"]
        artifact_id = parsed["artifactId"]
        if not isinstance(group_id, str) or not isinstance(artifact_id, str):
            raise ValueError("groupId and artifactId must be strings")
        optional_val = parsed["optional"]
        raw_val = parsed["raw"]
        placement_val = parsed.get("placement")

        # Type-narrow placement_val
        placement_final: Literal["class-path", "module-path"] | None = None
        if isinstance(placement_val, str) and placement_val in (
            "class-path",
            "module-path",
        ):
            placement_final = placement_val  # type: ignore[assignment]

        return cls(
            groupId=group_id,
            artifactId=artifact_id,
            version=parsed["version"] if isinstance(parsed["version"], str) else None,
            classifier=parsed["classifier"]
            if isinstance(parsed["classifier"], str)
            else None,
            packaging=parsed["packaging"]
            if isinstance(parsed["packaging"], str)
            else None,
            scope=parsed["scope"] if isinstance(parsed["scope"], str) else None,
            optional=bool(optional_val) if optional_val else False,
            raw=raw_val if isinstance(raw_val, bool) else None,
            placement=placement_final,
        )


def looks_like_version(s: str) -> bool:
    """
    Check if string looks like a version (starts with digit or is a special keyword).

    This is a heuristic, which cannot guarantee certainty either way.

    Args:
        s: The string to examine

    Returns:
        True if the string starts with a digit, or is one of LATEST, RELEASE, or MANAGED
        False if the string does not start with a digit and is not a special keyword
    """
    # Special version keywords
    if s.upper() in ("LATEST", "RELEASE", "MANAGED"):
        return True
    # Standard versions start with a digit
    return bool(s and s[0].isdigit())


def looks_like_classifier(s: str) -> bool:
    """
    Check if string looks like a classifier based on common patterns.

    This is a heuristic, which cannot guarantee certainty either way.

    Args:
        s: The string to examine

    Returns:
        True if the string matches a known pattern in the wild for classifiers
        False if the string does not match any such pattern
    """
    classifier_patterns = [
        # Native library prefix (e.g., natives-linux)
        r"^natives-",
        # Standard Maven classifiers that are always classifiers
        r"^(sources|javadoc|tests)$",
        # Less common but legitimate standalone classifiers
        r"^(shaded|uber|universal)$",
        # Common OS/platform names as standalone classifiers
        # Based on empirical evidence from Maven Central (JavaFX, etc.)
        r"^(linux|windows|win|macos|mac)$",
        # Common architecture names as standalone classifiers
        r"^(x86_64|amd64|i386|i486|i586|i686|ia64)$",  # x86 family
        r"^(arm|arm64|aarch64|aarch_64|armv6|armv6hf|armv7|armhf)$",  # ARM family
        r"^(ppc|ppc64|ppc64le|powerpc)$",  # PowerPC family
        # Architecture patterns with hyphen or underscore prefix (e.g., linux-x86_64)
        r"[-_](x86_64|amd64|i386|i486|i586|i686|ia64)",  # x86 family
        r"[-_](arm|arm64|aarch64|aarch_64|armv6|armv6hf|armv7|armhf)",  # ARM family
        r"[-_](ppc|ppc64|ppc64le|powerpc)",  # PowerPC family
        # OS patterns with hyphen or underscore prefix (e.g., natives-linux)
        r"[-_](linux|windows|win|macos|mac|osx|darwin|freebsd|solaris|android)",
        # Underscore variants for platform combos (e.g., linux_64)
        r"_(32|64)$",
    ]
    return any(re.search(pattern, s, re.IGNORECASE) for pattern in classifier_patterns)


def looks_like_main_class(s: str) -> bool:
    """
    Check if string could be a valid Java main class name.

    A valid Java class name follows identifier rules for each dot-separated token:
    - Must start with a letter, $, or _
    - Can contain letters, digits, $, or _
    - Cannot start with a digit

    Args:
        s: The string to examine

    Returns:
        True if the string follows Java identifier grammar (might be a class)
        False if it violates Java identifier rules (definitely NOT a class)
    """
    if not s:
        return False

    # Split by dots for package-qualified names
    tokens = s.split(".")

    for token in tokens:
        if not token:  # Empty token (e.g., "com..Main")
            return False

        # First character: must be letter, $, or _
        if not (token[0].isalpha() or token[0] in ("$", "_")):
            return False

        # Remaining characters: letters, digits, $, or _
        for ch in token[1:]:
            if not (ch.isalnum() or ch in ("$", "_")):
                return False

    return True


def coord2str(
    groupId: str,
    artifactId: str,
    version: str | None = None,
    classifier: str | None = None,
    packaging: str | None = None,
    scope: str | None = None,
    optional: bool = False,
    raw: bool | None = None,
    placement: str | None = None,
    display: bool = False,
) -> str:
    """
    Convert Maven coordinate components to a string.

    Args:
        groupId: The Maven group ID
        artifactId: The Maven artifact ID
        version: The version (optional)
        classifier: The classifier (optional)
        packaging: The packaging type (optional)
        scope: The dependency scope (optional)
        optional: Whether this is an optional dependency
        raw: Whether to use raw/strict resolution (appends ! if True)
        placement: Module path placement ("class-path" or "module-path")
        display: If True, format with Rich markup for CLI display

    Returns:
        A formatted coordinate string (e.g., "g:a:p:c:v:s" or "g:a:v!" for raw)
        If display=True, includes Rich markup tags for coloring
    """
    if display:
        # Suppress components with default values unless --full-coordinates
        if not FULL_COORDINATES:
            if packaging == DEFAULT_PACKAGING:
                packaging = None
            if scope == DEFAULT_SCOPE:
                scope = None

        # Build coordinate from non-empty components
        result = format_tokens(
            [
                (groupId, "g"),
                (artifactId, "a"),
                (packaging, "p"),
                (classifier, "c"),
                (version, "v"),
                (scope, "s"),
            ]
        )

        # Add (optional) marker if optional flag is set
        if optional:
            result += f" [{STYLES['optional']}](optional)[/]"

        # Append placement suffix (before raw flag)
        if placement == "class-path":
            result += f"[{STYLES['placement']}](c)[/]"
        elif placement == "module-path":
            result += f"[{STYLES['placement']}](m)[/]"

        # Append ! for raw/strict resolution (comes last)
        if raw:
            result += styled("!")

        return result
    else:
        # Plain text mode - no Rich markup
        parts = [groupId, artifactId]
        if packaging:
            parts.append(packaging)
        if classifier:
            parts.append(classifier)
        if version:
            parts.append(version)
        if scope:
            scope_text = scope
            if optional:
                scope_text += " (optional)"
            parts.append(scope_text)

        result = ":".join(parts)

        # Append placement suffix (before raw flag)
        if placement == "class-path":
            result += "(c)"
        elif placement == "module-path":
            result += "(m)"

        # Append ! for raw/strict resolution (comes last)
        if raw:
            result += "!"

        return result


def _parse_coordinate_dict(coordinate: str) -> dict[str, str | None | bool]:
    """
    Parse a Maven coordinate string into a dictionary.

    This is the internal implementation that returns a dict.
    External callers should use Coordinate.parse() instead.

    Supports two modes:
    1. Heuristic mode (default): Uses pattern matching to infer component types
    2. Strict mode: When empty strings are present (e.g., "g:a::c"), uses
       fixed positions G:A:V:C:P:S to avoid ambiguity
    """
    # Check for raw/unmanaged flag (! or \! suffix) on the entire coordinate
    # Handle both ! and \! (shell escaped) before splitting
    raw = None
    if coordinate.endswith("\\!"):
        coordinate = coordinate[:-2]  # Strip the \! suffix
        raw = True
    elif coordinate.endswith("!"):
        coordinate = coordinate[:-1]  # Strip the ! suffix
        raw = True

    # Check for module placement suffix: (c), (cp), (m), (mp), (p)
    # Must come after ! handling but before splitting on :
    placement = None
    placement_suffixes = [
        ("(cp)", "class-path"),
        ("(c)", "class-path"),
        ("(mp)", "module-path"),
        ("(m)", "module-path"),
        ("(p)", "module-path"),
    ]
    for suffix, value in placement_suffixes:
        if coordinate.endswith(suffix):
            coordinate = coordinate[: -len(suffix)]
            placement = value
            break

    parts = coordinate.split(":")
    if len(parts) < 2:
        raise ValueError(
            "Invalid coordinate string: must have at least groupId and artifactId"
        )

    # Check if we're in strict mode (empty strings present, indicating explicit positions)
    has_empty_strings = any(part == "" for part in parts[2:])  # Skip G and A positions

    # Handle " (optional)" suffix early - it's typically attached to the last part
    optional = False
    if parts[-1].endswith(" (optional)"):
        parts[-1] = parts[-1][:-11]  # Remove " (optional)"
        optional = True

    # Known sets for identification
    packaging_values = {
        "jar",
        "war",
        "ear",
        "pom",
        "rar",
        "maven-plugin",
        "ejb",
        "par",
        "test-jar",
        "aar",
        "apk",
        "bundle",
    }
    scope_values = {"compile", "provided", "runtime", "test", "system", "import"}

    # Always first two parts
    groupId = parts[0]
    artifactId = parts[1]

    packaging = None
    classifier = None
    version = None
    scope = None

    num_parts = len(parts)

    # STRICT MODE: When empty strings are present, use fixed positions G:A:V:C:P:S
    # This allows explicit disambiguation without relying on heuristics
    if has_empty_strings:
        if num_parts >= 3:
            version = parts[2] if parts[2] else None
        if num_parts >= 4:
            classifier = parts[3] if parts[3] else None
        if num_parts >= 5:
            packaging = parts[4] if parts[4] else None
        if num_parts >= 6:
            scope = parts[5] if parts[5] else None
        if num_parts >= 7:
            # More than 6 positions (G:A:V:C:P:S) is an error
            raise ValueError(
                f"Too many parts in strict mode coordinate: {coordinate}. "
                "Expected at most G:A:V:C:P:S (6 positions total)."
            )

        # In strict mode, validate that scope is actually a scope if provided
        if scope and scope not in scope_values:
            raise ValueError(
                f"Invalid scope '{scope}' in strict mode. "
                f"Must be one of: {', '.join(sorted(scope_values))}"
            )

        return {
            "groupId": groupId,
            "artifactId": artifactId,
            "packaging": packaging,
            "classifier": classifier,
            "version": version,
            "scope": scope,
            "optional": optional,
            "raw": raw,
            "placement": placement,
        }

    if num_parts == 2:
        # G:A - minimal coordinate
        pass
    elif num_parts == 3:
        # G:A:V or G:A:P or G:A:C
        if parts[2] in packaging_values:
            packaging = parts[2]
        elif looks_like_classifier(parts[2]):
            classifier = parts[2]
        elif looks_like_version(parts[2]):
            version = parts[2]
        else:
            # Ambiguous - default to version for backward compatibility
            version = parts[2]
    elif num_parts == 4:
        # Could be: G:A:V:C, G:A:P:V
        if parts[2] in packaging_values:
            packaging = parts[2]
            version = parts[3]
        elif looks_like_version(parts[2]) and not looks_like_version(parts[3]):
            version = parts[2]
            classifier = parts[3]
        elif looks_like_version(parts[3]):
            if parts[2] in packaging_values:
                packaging = parts[2]
            else:
                classifier = parts[2]
            version = parts[3]
        else:
            version = parts[2]
            classifier = parts[3]
    elif num_parts == 5:
        # Could be: G:A:P:V:S, G:A:P:C:V, G:A:V:C:S
        if parts[4] in scope_values:
            scope = parts[4]
            if parts[2] in packaging_values:
                packaging = parts[2]
                version = parts[3]
            else:
                version = parts[2]
                classifier = parts[3]
        elif parts[2] in packaging_values:
            packaging = parts[2]
            if looks_like_version(parts[4]):
                classifier = parts[3]
                version = parts[4]
            else:
                version = parts[3]
                classifier = parts[4]
        else:
            version = parts[2]
            classifier = parts[3]
            if parts[4] in scope_values:
                scope = parts[4]
    elif num_parts == 6:
        # G:A:P:C:V:S
        packaging = parts[2]
        classifier = parts[3]
        version = parts[4]
        scope = parts[5]
    else:
        # 7+ parts - unusual, try to be flexible
        remaining = list(parts[2:])

        if remaining and remaining[-1] in scope_values:
            scope = remaining[-1]
            remaining = remaining[:-1]

        for i, part in enumerate(remaining):
            if part in packaging_values:
                packaging = part
                remaining = remaining[:i] + remaining[i + 1 :]
                break

        for i in range(len(remaining) - 1, -1, -1):
            if looks_like_version(remaining[i]):
                version = remaining[i]
                remaining = remaining[:i] + remaining[i + 1 :]
                break

        if remaining:
            classifier = ":".join(remaining)

    return {
        "groupId": groupId,
        "artifactId": artifactId,
        "packaging": packaging,
        "classifier": classifier,
        "version": version,
        "scope": scope,
        "optional": optional,
        "raw": raw,
        "placement": placement,
    }
