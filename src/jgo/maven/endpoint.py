"""
Maven coordinate and endpoint parsing and representation.

This module provides classes for representing and parsing Maven coordinates and endpoints.
"""

import re
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import Dependency, MavenContext


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
    """

    groupId: str
    artifactId: str
    version: str | None = None
    classifier: str | None = None
    packaging: str | None = None
    scope: str | None = None
    optional: bool = False

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
        )

    def __repr__(self) -> str:
        """Return detailed representation."""
        parts = [f"{self.groupId}:{self.artifactId}"]
        if self.version:
            parts.append(f"v={self.version}")
        if self.classifier:
            parts.append(f"c={self.classifier}")
        if self.packaging:
            parts.append(f"p={self.packaging}")
        if self.scope:
            parts.append(f"s={self.scope}")
        if self.optional:
            parts.append("optional")
        return f"<Coordinate {' '.join(parts)}>"

    @classmethod
    def parse(cls, coordinate: str) -> "Coordinate":
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
        parsed = _parse_coordinate_dict(coordinate)
        return cls(
            groupId=parsed["groupId"],
            artifactId=parsed["artifactId"],
            version=parsed["version"],
            classifier=parsed["classifier"],
            packaging=parsed["packaging"],
            scope=parsed["scope"],
            optional=parsed["optional"],
        )

    def to_dependency(self, context: "MavenContext") -> "Dependency":
        """
        Convert this coordinate to a Dependency object.

        Args:
            context: The MavenContext to use for creating the dependency.

        Returns:
            A Dependency object.
        """
        from .core import DEFAULT_CLASSIFIER, DEFAULT_PACKAGING, Dependency

        classifier = self.classifier or DEFAULT_CLASSIFIER
        packaging = self.packaging or DEFAULT_PACKAGING

        project = context.project(self.groupId, self.artifactId)
        component = (
            project.at_version(self.version) if self.version else project.at_version("")
        )
        artifact = component.artifact(classifier, packaging)
        return Dependency(artifact, self.scope, self.optional, [])


@dataclass
class Endpoint:
    """
    Represents a complete endpoint expression.

    An endpoint consists of:
    - coordinates: List of Coordinate objects
    - main_class: Optional main class to execute
    - managed: List of booleans indicating which coordinates are managed
    - deprecated_format: Whether deprecated syntax was used
    """

    coordinates: list[Coordinate]
    main_class: str | None = None
    managed: list[bool] | None = None
    deprecated_format: bool = False

    def __post_init__(self):
        """Validate and normalize the endpoint."""
        if self.managed is None:
            self.managed = [False] * len(self.coordinates)
        elif len(self.managed) != len(self.coordinates):
            raise ValueError(
                f"managed list length ({len(self.managed)}) must match "
                f"coordinates list length ({len(self.coordinates)})"
            )

    def __str__(self) -> str:
        """Return string representation of the endpoint."""
        coord_strs = []
        for coord, is_managed in zip(self.coordinates, self.managed):
            coord_str = str(coord)
            if is_managed:
                coord_str += "!"
            coord_strs.append(coord_str)

        result = "+".join(coord_strs)
        if self.main_class:
            result += f"@{self.main_class}"
        return result

    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"<Endpoint coords={len(self.coordinates)} "
            f"main={self.main_class or 'None'} "
            f"managed={sum(self.managed)}/{len(self.coordinates)}>"
        )

    @classmethod
    def parse(cls, endpoint: str) -> "Endpoint":
        """
        Parse a complete endpoint expression.

        This handles:
        - Multiple coordinates separated by '+' (e.g., coord1+coord2+coord3)
        - Main class specification with '@' (new format: coord1+coord2@MainClass)
        - Deprecated main class with ':@' or ':MainClass'
        - Managed dependency flag with '!' or '\\!' suffix

        Args:
            endpoint: The endpoint string to parse (e.g., "g:a:v+g2:a2:v2@MainClass")

        Returns:
            An Endpoint object.

        Examples:
            >>> Endpoint.parse("org.scijava:scijava-common:2.90.0")
            <Endpoint coords=1 main=None managed=0/1>

            >>> Endpoint.parse("g:a:v+g2:a2:v2@org.example.Main")
            <Endpoint coords=2 main=org.example.Main managed=0/2>

            >>> Endpoint.parse("g:a:v!+g2:a2:v2")
            <Endpoint coords=2 main=None managed=1/2>
        """
        parsed = _parse_endpoint_dict(endpoint)
        coordinates = [
            Coordinate(
                groupId=c["groupId"],
                artifactId=c["artifactId"],
                version=c["version"],
                classifier=c["classifier"],
                packaging=c["packaging"],
                scope=c["scope"],
                optional=c["optional"],
            )
            for c in parsed["coordinates"]
        ]
        return cls(
            coordinates=coordinates,
            main_class=parsed["main_class"],
            managed=parsed["managed"],
            deprecated_format=parsed["deprecated_format"],
        )

    def to_components(self, context: "MavenContext") -> list:
        """
        Convert this endpoint's coordinates to Component objects.

        Args:
            context: The MavenContext to use for creating components.

        Returns:
            List of Component objects.
        """
        components = []
        for coord in self.coordinates:
            project = context.project(coord.groupId, coord.artifactId)
            version = coord.version or "RELEASE"
            component = project.at_version(version)
            components.append(component)
        return components


def coord2str(
    groupId: str,
    artifactId: str,
    version: str | None = None,
    classifier: str | None = None,
    packaging: str | None = None,
    scope: str | None = None,
    optional: bool = False,
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

    Returns:
        A formatted coordinate string (e.g., "g:a:p:c:v:s")
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

    return ":".join(parts)


def _parse_coordinate_dict(coordinate: str) -> dict[str, str | None]:
    """
    Parse a Maven coordinate string into a dictionary.

    This is the internal implementation that returns a dict.
    External callers should use Coordinate.parse() instead.
    """
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

    def looks_like_version(s: str) -> bool:
        """Check if string looks like a version (contains digits)."""
        return bool(re.search(r"\d", s))

    def looks_like_classifier(s: str) -> bool:
        """Check if string looks like a classifier based on common patterns."""
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
        return any(
            re.search(pattern, s, re.IGNORECASE) for pattern in classifier_patterns
        )

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
    }


def _parse_endpoint_dict(endpoint: str) -> dict:
    """
    Parse a complete endpoint expression into a dictionary.

    This is the internal implementation that returns a dict.
    External callers should use Endpoint.parse() instead.
    """
    main_class = None
    deprecated_format = False
    coordinates_part = endpoint

    # Check for new @ separator format
    if "@" in endpoint:
        plus_parts = endpoint.split("+")

        # Find which part contains @
        at_part_index = -1
        for i, part in enumerate(plus_parts):
            if "@" in part:
                at_part_index = i
                break

        if at_part_index >= 0:
            part_with_at = plus_parts[at_part_index]
            at_index = part_with_at.rfind("@")
            before_at = part_with_at[:at_index]
            after_at = part_with_at[at_index + 1 :]

            if before_at.endswith(":"):
                # Old format: coord:@MainClass
                deprecated_format = True
                warnings.warn(
                    "The ':@mainClass' syntax is deprecated. "
                    "Use 'coord1+coord2@mainClass' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                main_class = "@" + after_at if after_at else None
            else:
                # New format: coord@MainClass
                main_class = after_at if after_at else None
                plus_parts[at_part_index] = before_at
                coordinates_part = "+".join(plus_parts)

    # Split coordinates by +
    coord_parts = coordinates_part.split("+")
    coordinates = []
    managed = []

    for part in coord_parts:
        # Check for managed dependency flag (! or \\! suffix)
        is_managed = False
        if part.endswith("\\!"):
            is_managed = True
            part = part[:-2]
        elif part.endswith("!"):
            is_managed = True
            part = part[:-1]

        if not part:
            continue

        # Check for deprecated :MainClass format in first coordinate
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

        # Parse coordinate
        try:
            parsed_coord = _parse_coordinate_dict(part)
            coordinates.append(parsed_coord)
            managed.append(is_managed)
        except ValueError:
            continue

    return {
        "coordinates": coordinates,
        "main_class": main_class,
        "managed": managed,
        "deprecated_format": deprecated_format,
    }


# Convenience functions that wrap the class methods
def parse_coordinate(coordinate: str) -> Coordinate:
    """Parse a coordinate string into a Coordinate object."""
    return Coordinate.parse(coordinate)


def parse_endpoint(endpoint: str) -> Endpoint:
    """Parse an endpoint string into an Endpoint object."""
    return Endpoint.parse(endpoint)
