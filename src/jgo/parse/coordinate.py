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

The Coordinate class is a simple data structure for holding parsed coordinate
components. It does not perform Maven resolution, version interpolation, or
dependency management - for that, see the jgo.maven subpackage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


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
        """Return string representation using coord2str."""
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
        parsed = _parse_coordinate_dict(coordinate)
        return cls(
            groupId=parsed["groupId"],
            artifactId=parsed["artifactId"],
            version=parsed["version"],
            classifier=parsed["classifier"],
            packaging=parsed["packaging"],
            scope=parsed["scope"],
            optional=parsed["optional"] or False,
            raw=parsed["raw"],
            placement=parsed.get("placement"),
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
        r"^natives-",
        r"^sources$",
        r"^javadoc$",
        r"^tests$",
        r"-(x86_64|amd64|arm64|aarch64|i386|i686|armv7|armhf)",
        r"-(linux|windows|macos|osx|darwin|freebsd|solaris)",
        r"^shaded$",
        r"^uber$",
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

    Returns:
        A formatted coordinate string (e.g., "g:a:p:c:v:s" or "g:a:v!" for raw)
    """
    parts = [groupId, artifactId]

    # Add packaging if present (comes before version in Maven format)
    if packaging:
        parts.append(packaging)

    # Add classifier if present
    if classifier:
        parts.append(classifier)

    # Add version if present
    if version:
        parts.append(version)

    # Add scope if present
    if scope:
        parts.append(scope)
        if optional:
            parts[-1] += " (optional)"

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


def _parse_coordinate_dict(coordinate: str) -> dict[str, str | None]:
    """
    Parse a Maven coordinate string into a dictionary.

    This is the internal implementation that returns a dict.
    External callers should use Coordinate.parse() instead.
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
