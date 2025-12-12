"""
EnvironmentBuilder for jgo 2.0.

Builds Environment instances from Maven components or endpoint strings.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from .environment import Environment
from .jar_util import autocomplete_main_class, detect_main_class_from_jar
from .linking import LinkStrategy, link_file
from .lockfile import LockFile

if TYPE_CHECKING:
    from ..maven import Component, MavenContext
    from ..maven.core import Dependency
    from .spec import EnvironmentSpec


class EnvironmentBuilder:
    """
    Builds environment directories from Maven components.

    Supports hybrid caching:
    - Project mode: Uses .jgo/ in current directory (when jgo.toml exists)
    - Ad-hoc mode: Uses ~/.cache/jgo/ for one-off executions
    - Override: Explicit cache_dir can be provided
    """

    def __init__(
        self,
        context: MavenContext,
        cache_dir: Path | None = None,
        link_strategy: LinkStrategy = LinkStrategy.AUTO,
        managed: bool = False,
    ):
        self.context = context
        self.link_strategy = link_strategy
        self.managed = managed

        # Auto-detect cache directory if not specified
        if cache_dir is None:
            cache_dir = self._auto_detect_cache_dir()

        self.cache_dir = Path(cache_dir).expanduser()

    @staticmethod
    def _auto_detect_cache_dir() -> Path:
        """
        Auto-detect cache directory based on context.

        Returns:
            Path(".jgo") if jgo.toml exists in current directory (project mode)
            Otherwise Path.home() / ".cache" / "jgo" (ad-hoc mode)
        """
        # Check if jgo.toml exists in current directory
        if Path("jgo.toml").exists():
            return Path(".jgo")

        # Default to centralized cache
        return Path.home() / ".cache" / "jgo"

    def from_endpoint(
        self, endpoint: str, update: bool = False, main_class: str | None = None
    ) -> Environment:
        """
        Build an environment from an endpoint string.

        Endpoint format: G:A[:V][:C][:mainClass][!][+G:A:V...]
        Components with ! suffix are used as managed BOMs.
        """
        # Parse endpoint
        components, managed_flags, parsed_main_class = self._parse_endpoint(endpoint)

        # Apply -m flag: if self.managed is True, mark all components as managed
        # Otherwise, use the per-component managed flags from ! markers
        if self.managed:
            # -m flag forces all components to be managed (backward compatibility)
            boms = components
        else:
            # Use explicit ! markers to determine which components are managed
            boms = [
                comp
                for comp, is_managed in zip(components, managed_flags)
                if is_managed
            ]

        # Temporarily store managed components for use in from_components
        self._current_boms = boms if boms else None

        # Use parsed main class if caller didn't provide one
        if main_class is None:
            main_class = parsed_main_class

        # Build environment
        return self.from_components(components, update=update, main_class=main_class)

    def from_components(
        self,
        components: list[Component],
        update: bool = False,
        main_class: str | None = None,
    ) -> Environment:
        """
        Build an environment from a list of components.
        """
        # Generate cache key
        cache_key = self._cache_key(components)

        # Environment path
        primary = components[0]
        workspace_path = self.cache_dir / primary.project.path_prefix / cache_key

        # Check if environment exists and is valid
        environment = Environment(workspace_path)
        if workspace_path.exists() and not update:
            # Validate environment has JARs
            if environment.classpath:
                # Environment is valid, use cached build
                # But we still need to set/update main class if provided
                if main_class:
                    # Auto-complete main class if needed
                    jars_dir = workspace_path / "jars"
                    main_class = autocomplete_main_class(
                        main_class, primary.artifactId, jars_dir
                    )
                    environment.set_main_class(main_class)
                return environment
            # Otherwise fall through to rebuild

        # Build/rebuild environment
        # Note: We don't need the returned deps here since from_components
        # is primarily for endpoint-based builds, not spec-based builds
        self._build_environment(environment, components, main_class)

        return environment

    def from_spec(
        self,
        spec: EnvironmentSpec,
        update: bool = False,
        entrypoint: str | None = None,
    ) -> Environment:
        """
        Build an environment from an EnvironmentSpec (jgo.toml).

        Args:
            spec: Environment specification
            update: If True, force rebuild even if environment exists
            entrypoint: Optional entrypoint name to use (overrides spec default)

        Returns:
            Environment instance
        """
        # Parse coordinates into components
        components = []
        for coord in spec.coordinates:
            parts = coord.split(":")
            groupId = parts[0]
            artifactId = parts[1]
            version = parts[2] if len(parts) >= 3 else "RELEASE"
            # TODO: Handle classifier (parts[3]) when Component supports it

            component = self.context.project(groupId, artifactId).at_version(version)
            components.append(component)

        # Get main class from entrypoint
        main_class = spec.get_main_class(entrypoint)

        # Use spec's cache_dir if specified, otherwise use builder's default
        cache_dir = (
            Path(spec.cache_dir).expanduser() if spec.cache_dir else self.cache_dir
        )

        # Generate cache key for this spec
        cache_key = self._cache_key(components)

        # Environment path
        primary = components[0]
        workspace_path = cache_dir / primary.project.path_prefix / cache_key

        # Check if environment exists and is valid
        environment = Environment(workspace_path)
        if workspace_path.exists() and not update:
            # Validate environment has JARs
            if environment.classpath:
                # Environment is valid, use it
                return environment
            # Otherwise fall through to rebuild

        # Build environment and get resolved dependencies
        resolved_deps = self._build_environment(environment, components, main_class)

        # Save spec and lock file to environment directory
        spec_path = environment.path / "jgo.toml"
        lock_path = environment.path / "jgo.lock.toml"

        spec.save(spec_path)

        # Generate lock file from resolved dependencies
        lockfile = LockFile.from_resolved_dependencies(
            dependencies=resolved_deps,
            environment_name=spec.name,
            min_java_version=environment.min_java_version,
            entrypoints=spec.entrypoints,
            default_entrypoint=spec.default_entrypoint,
        )
        lockfile.save(lock_path)

        return environment

    def _cache_key(self, components: list[Component]) -> str:
        """Generate a stable hash for a set of components."""
        # Sort to ensure stable ordering
        # Use resolved_version to ensure RELEASE/LATEST resolve to consistent cache keys
        coord_strings = sorted(
            [f"{c.groupId}:{c.artifactId}:{c.resolved_version}" for c in components]
        )
        combined = "+".join(coord_strings)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _build_environment(
        self,
        environment: Environment,
        components: list[Component],
        main_class: str | None,
    ) -> list[Dependency]:
        """
        Actually build the environment by resolving and linking JARs.

        Returns:
            List of resolved dependencies (for lock file generation)
        """
        # Create directories
        environment.path.mkdir(parents=True, exist_ok=True)
        jars_dir = environment.path / "jars"
        jars_dir.mkdir(exist_ok=True)

        # First, link the components themselves
        for component in components:
            artifact = component.artifact()
            source_path = artifact.resolve()
            dest_path = jars_dir / artifact.filename

            if not dest_path.exists():
                link_file(source_path, dest_path, self.link_strategy)

        # Resolve all dependencies in one shot using wrapper POM
        # Use managed components from endpoint parsing (stored in _current_boms)
        # or fall back to old behavior for backward compatibility
        boms = getattr(self, "_current_boms", None)
        if boms is None and self.managed:
            # Backward compatibility: if -m flag is set but no explicit markers, manage all
            boms = components

        # Resolve all components together (not separately!)
        # This ensures Maven handles version conflicts across all components
        all_deps = components[0].context.resolver.dependencies(
            components,
            managed=bool(boms),
            boms=boms,
        )

        # Link/copy dependency JARs
        for dep in all_deps:
            if dep.scope not in ("compile", "runtime"):
                continue  # Skip test deps, etc.

            artifact = dep.artifact
            source_path = artifact.resolve()
            dest_path = jars_dir / artifact.filename

            if not dest_path.exists():
                link_file(source_path, dest_path, self.link_strategy)

        # Save manifest
        environment.manifest["components"] = [
            f"{c.groupId}:{c.artifactId}:{c.resolved_version}" for c in components
        ]
        environment.manifest["link_strategy"] = self.link_strategy.name
        environment.save_manifest()

        # Detect/set main class
        if main_class:
            # Auto-complete main class if needed
            primary_component = components[0]
            main_class = autocomplete_main_class(
                main_class, primary_component.artifactId, jars_dir
            )
            environment.set_main_class(main_class)
        else:
            # Auto-detect from primary component JAR
            primary_component = components[0]
            primary_jar = jars_dir / primary_component.artifact().filename
            if primary_jar.exists():
                detected_main = detect_main_class_from_jar(primary_jar)
                if detected_main:
                    environment.set_main_class(detected_main)

        # Return dependencies for lock file generation
        return all_deps

    def _parse_endpoint(
        self, endpoint: str
    ) -> tuple[list[Component], list[bool], str | None]:
        """
        Parse endpoint string into components and main class.

        New format: coord1+coord2+...+coordN@mainClass
        Old format: coord1:coord2:@mainClass or coord1:coord2:mainClass (deprecated)

        Returns:
            Tuple of (components_list, managed_flags, main_class)
            - components_list: List of Component objects
            - managed_flags: List of booleans indicating if each component should be managed (has ! suffix)
            - main_class: Main class to run (only from first endpoint part)
        """
        import re
        import warnings

        main_class = None
        coordinates_part = endpoint
        old_format_detected = False

        # Check for new @ separator format
        if "@" in endpoint:
            # Find the @ that separates coordinates from main class
            # New format: coord1+coord2@MainClass (@ after all coordinates)
            # Old format: coord:@MainClass (@ comes right after :)

            # Check if @ appears after a + (which means it's in the middle of coords)
            # Split by + first to see if @ is in any part
            plus_parts = endpoint.split("+")

            # Find which part contains @
            at_part_index = -1
            for i, part in enumerate(plus_parts):
                if "@" in part:
                    at_part_index = i
                    break

            if at_part_index == 0 and len(plus_parts) > 1:
                # @ is in the first part, before other coordinates
                # This could be new format: coord@Main+coord2
                # Split on @ in the first part only
                first_part = plus_parts[0]
                at_index = first_part.rfind("@")
                before_at = first_part[:at_index]
                after_at = first_part[at_index + 1 :]

                if before_at.endswith(":"):
                    # Old format: coord:@MainClass
                    old_format_detected = True
                    warnings.warn(
                        "The ':@mainClass' syntax is deprecated. "
                        "Use 'coord1+coord2@mainClass' instead.",
                        DeprecationWarning,
                        stacklevel=3,
                    )
                    main_class = "@" + after_at if after_at else None
                    # Don't modify coordinates_part for old format
                else:
                    # New format: coord@MainClass+coord2
                    main_class = after_at if after_at else None
                    # Reconstruct coordinates_part without the @MainClass
                    plus_parts[0] = before_at
                    coordinates_part = "+".join(plus_parts)
            elif at_part_index == len(plus_parts) - 1:
                # @ is in the last part, after all coordinates (typical new format)
                last_part = plus_parts[-1]
                at_index = last_part.rfind("@")
                before_at = last_part[:at_index]
                after_at = last_part[at_index + 1 :]

                if before_at.endswith(":"):
                    # Old format: coord:@MainClass
                    old_format_detected = True
                    warnings.warn(
                        "The ':@mainClass' syntax is deprecated. "
                        "Use 'coord1+coord2@mainClass' instead.",
                        DeprecationWarning,
                        stacklevel=3,
                    )
                    main_class = "@" + after_at if after_at else None
                else:
                    # New format: coord1+coord2@MainClass
                    main_class = after_at if after_at else None
                    # Reconstruct coordinates_part without the @MainClass
                    plus_parts[-1] = before_at
                    coordinates_part = "+".join(plus_parts)
            elif at_part_index >= 0:
                # @ is in a middle part (unusual, but handle it)
                part_with_at = plus_parts[at_part_index]
                at_index = part_with_at.rfind("@")
                before_at = part_with_at[:at_index]
                after_at = part_with_at[at_index + 1 :]

                if before_at.endswith(":"):
                    # Old format
                    old_format_detected = True
                    warnings.warn(
                        "The ':@mainClass' syntax is deprecated. "
                        "Use 'coord1+coord2@mainClass' instead.",
                        DeprecationWarning,
                        stacklevel=3,
                    )
                    main_class = "@" + after_at if after_at else None
                else:
                    # New format in middle (weird but valid)
                    main_class = after_at if after_at else None
                    plus_parts[at_part_index] = before_at
                    coordinates_part = "+".join(plus_parts)

        # Split on + for multiple components
        parts = coordinates_part.split("+")
        components = []
        managed_flags = []

        for i, part in enumerate(parts):
            # Check for ! suffix indicating managed dependency
            # Handle both ! and \! (shell escaped)
            is_managed = part.endswith("!") or part.endswith("\\!")
            if part.endswith("\\!"):
                part = part[:-2]  # Strip the \! suffix
            elif part.endswith("!"):
                part = part[:-1]  # Strip the ! suffix

            # Parse G:A[:V][:C][:mainClass]
            tokens = part.split(":")

            if len(tokens) < 2:
                raise ValueError(
                    f"Invalid endpoint format '{part}': need at least groupId:artifactId"
                )

            if len(tokens) > 5:
                raise ValueError(
                    f"Invalid endpoint format '{part}': too many elements (max 5)"
                )

            groupId = tokens[0]
            artifactId = tokens[1]
            version = "RELEASE"
            classifier = None
            part_main_class = None

            # Parse remaining tokens based on count
            if len(tokens) == 3:
                # Could be G:A:V or G:A:mainClass
                # Check if it looks like a version
                if re.match(r"([0-9].*|RELEASE|LATEST|MANAGED)", tokens[2]):
                    version = tokens[2]
                else:
                    # Old format: main class in colon-separated tokens
                    if i == 0:  # Only first component can have main class
                        # Only warn if we didn't already detect old format with @
                        if not old_format_detected:
                            warnings.warn(
                                "The ':mainClass' syntax is deprecated. "
                                "Use 'coord1+coord2@mainClass' instead.",
                                DeprecationWarning,
                                stacklevel=3,
                            )
                        part_main_class = tokens[2]

            elif len(tokens) == 4:
                # G:A:V:C or G:A:V:mainClass
                # If tokens[3] contains a dot, it's likely a main class
                version = tokens[2]
                if "." in tokens[3] or tokens[3][0].isupper():
                    # Old format: main class in colon-separated tokens
                    if i == 0:  # Only first component can have main class
                        # Only warn if we didn't already detect old format with @
                        if not old_format_detected:
                            warnings.warn(
                                "The ':mainClass' syntax is deprecated. "
                                "Use 'coord1+coord2@mainClass' instead.",
                                DeprecationWarning,
                                stacklevel=3,
                            )
                        part_main_class = tokens[3]
                else:
                    classifier = tokens[3]  # noqa: F841 - TODO: Use when Component supports classifiers

            elif len(tokens) == 5:
                # G:A:V:C:mainClass
                version = tokens[2]
                classifier = tokens[3]  # noqa: F841 - TODO: Use when Component supports classifiers
                # Old format: main class in colon-separated tokens
                if i == 0:  # Only first component can have main class
                    # Only warn if we didn't already detect old format with @
                    if not old_format_detected:
                        warnings.warn(
                            "The ':mainClass' syntax is deprecated. "
                            "Use 'coord1+coord2@mainClass' instead.",
                            DeprecationWarning,
                            stacklevel=3,
                        )
                    part_main_class = tokens[4]

            # Only the first component can specify main class via old format
            # If main_class was already set from @ separator, don't override
            if i == 0 and part_main_class and main_class is None:
                main_class = part_main_class

            # Create component
            component = self.context.project(groupId, artifactId).at_version(version)
            # TODO: Handle classifier when Component supports it
            components.append(component)
            managed_flags.append(is_managed)

        return components, managed_flags, main_class
