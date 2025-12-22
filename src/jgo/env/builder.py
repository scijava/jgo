"""
EnvironmentBuilder for jgo.

Builds Environment instances from Maven components or endpoint strings.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from ..constants import DEFAULT_JGO_CACHE
from ..parse.coordinate import Coordinate
from .environment import Environment
from .jar_util import autocomplete_main_class, detect_main_class_from_jar
from .linking import LinkStrategy, link_file
from .lockfile import LockFile, compute_spec_hash

if TYPE_CHECKING:
    from ..maven import Component, MavenContext
    from ..maven.core import Dependency
    from .spec import EnvironmentSpec


def filter_managed_components(
    components: list[Component], coordinates: list[Coordinate]
) -> list[Component]:
    """
    Filter components to those that should be managed (i.e., not marked as raw).

    Args:
        components: List of Maven components
        coordinates: List of parsed coordinates (parallel to components)

    Returns:
        List of components that should be managed (coordinates without raw flag)
    """
    return [comp for comp, coord in zip(components, coordinates) if not coord.raw]


def is_coordinate_reference(entrypoint_value: str) -> bool:
    """
    Check if entrypoint value is a Maven coordinate reference vs. a class name.

    Maven coordinates contain colons (e.g., "org.python:jython-slim" or "org.foo:foo+org.bar:bar")
    Class names do not contain colons (e.g., "org.python.util.jython" or "MyMain")

    Args:
        entrypoint_value: Entrypoint value from jgo.toml

    Returns:
        True if value is a coordinate reference, False if it's a class name
    """
    return ":" in entrypoint_value


def infer_main_class_from_coordinates(
    coord_str: str, components: list[Component], jars_dir: Path
) -> str | None:
    """
    Infer main class from a coordinate string.

    For composite coordinates (with +), tries each in order until one succeeds.

    Args:
        coord_str: Coordinate string (e.g., "org.python:jython-slim" or "org.foo:foo+org.bar:bar")
        components: List of Maven components (parallel to coord parts)
        jars_dir: Directory containing JAR files

    Returns:
        Inferred main class, or None if no Main-Class found
    """
    coord_parts = coord_str.split("+")

    for i, coord_part in enumerate(coord_parts):
        coord_part = coord_part.strip()
        coord = Coordinate.parse(coord_part)

        # Find matching JAR in environment
        for jar_path in jars_dir.glob("*.jar"):
            if coord.artifactId in jar_path.name:
                main_class = detect_main_class_from_jar(jar_path)
                if main_class:
                    return main_class

    return None


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
    ):
        self.context = context
        self.link_strategy = link_strategy

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
        return DEFAULT_JGO_CACHE

    def from_endpoint(
        self, endpoint: str, update: bool = False, main_class: str | None = None
    ) -> Environment:
        """
        Build an environment from an endpoint string.

        Endpoint format: G:A[:V][:C][:mainClass][!][+G:A:V...]
        - Components with ! suffix are raw/unmanaged
        """
        # Parse endpoint
        components, coordinates, parsed_main_class = self._parse_endpoint(endpoint)

        # Determine which components should be managed
        boms = filter_managed_components(components, coordinates)

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
        java_version: str | None = None,
    ) -> Environment:
        """
        Build an environment from an EnvironmentSpec (jgo.toml).

        Args:
            spec: Environment specification
            update: If True, force rebuild even if environment exists
            entrypoint: Optional entrypoint name to use (overrides spec default)
            java_version: Resolved Java version from cjdk (for lockfile)

        Returns:
            Environment instance
        """
        # Parse coordinates into components
        components = []
        for coord_str in spec.coordinates:
            coord = Coordinate.parse(coord_str)
            version = coord.version or "RELEASE"

            component = self.context.project(
                coord.groupId, coord.artifactId
            ).at_version(version)
            components.append(component)

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
                # TODO: Validate lockfile is not stale
                return environment
            # Otherwise fall through to rebuild

        # Build environment and get resolved dependencies
        resolved_deps = self._build_environment(environment, components, None)

        # Infer concrete entrypoints from spec
        jars_dir = environment.path / "jars"
        concrete_entrypoints = self._infer_concrete_entrypoints(
            spec, components, jars_dir
        )

        # Get concrete default entrypoint and set as main class
        concrete_default_class = None
        if spec.default_entrypoint and spec.default_entrypoint in concrete_entrypoints:
            concrete_default_class = concrete_entrypoints[spec.default_entrypoint]
        elif concrete_entrypoints:
            # Use first entrypoint as default if none specified
            concrete_default_class = next(iter(concrete_entrypoints.values()))

        # Set main class in environment (for backwards compat with manifest.json)
        if concrete_default_class:
            environment.set_main_class(concrete_default_class)

        # Save spec and lock file to environment directory
        spec_path = environment.path / "jgo.toml"
        lock_path = environment.path / "jgo.lock.toml"

        spec.save(spec_path)

        # Compute spec hash for staleness detection (from root jgo.toml if it exists)
        root_spec_path = Path("jgo.toml")
        if root_spec_path.exists():
            spec_hash = compute_spec_hash(root_spec_path)
        else:
            # Use the spec we just saved in the environment
            spec_hash = compute_spec_hash(spec_path)

        # Generate lock file from resolved dependencies
        lockfile = LockFile.from_resolved_dependencies(
            dependencies=resolved_deps,
            environment_name=spec.name,
            java_version=java_version or spec.java_version,
            java_vendor=spec.java_vendor,
            min_java_version=environment.min_java_version,
            entrypoints=concrete_entrypoints,
            default_entrypoint=spec.default_entrypoint,
            spec_hash=spec_hash,
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

    def _infer_concrete_entrypoints(
        self, spec: EnvironmentSpec, components: list[Component], jars_dir: Path
    ) -> dict[str, str]:
        """
        Infer concrete main classes from spec entrypoints.

        For each entrypoint in the spec:
        - If value contains ":" → coordinate reference → infer from JARs
        - Otherwise → class name (concrete or simple) → auto-complete if needed

        Args:
            spec: Environment specification
            components: List of Maven components
            jars_dir: Directory containing JAR files

        Returns:
            Dictionary of entrypoint names to concrete main class names
        """
        concrete_entrypoints = {}

        for name, value in spec.entrypoints.items():
            if is_coordinate_reference(value):
                # Coordinate reference - infer from JARs
                main_class = infer_main_class_from_coordinates(
                    value, components, jars_dir
                )
                if main_class:
                    concrete_entrypoints[name] = main_class
                # If inference fails, omit entrypoint (no Main-Class found)
            else:
                # Class name - auto-complete if needed
                primary = components[0]
                main_class = autocomplete_main_class(
                    value, primary.artifactId, jars_dir
                )
                concrete_entrypoints[name] = main_class

        return concrete_entrypoints

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
        # or fall back to default behavior: manage all components
        boms = getattr(self, "_current_boms", None)
        if boms is None:
            # Default: manage all components
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
    ) -> tuple[list[Component], list[Coordinate], str | None]:
        """
        Parse endpoint string into components and main class.

        Now uses Endpoint.parse() from jgo.parse.endpoint for consistency.

        Returns:
            Tuple of (components_list, coordinates_list, main_class)
            - components_list: List of Component objects for Maven resolution
            - coordinates_list: List of Coordinate objects (containing raw flags)
            - main_class: Main class to run
        """
        from ..parse.endpoint import Endpoint

        # Use the unified parsing logic from jgo.parse.endpoint
        parsed = Endpoint.parse(endpoint)

        # Convert coordinates to Maven Component objects
        components = []
        for coord in parsed.coordinates:
            # Use version if specified, otherwise default to RELEASE
            version = coord.version or "RELEASE"
            component = self.context.project(
                coord.groupId, coord.artifactId
            ).at_version(version)
            # TODO: Handle classifier and packaging by using Artifact instead?
            components.append(component)

        return components, parsed.coordinates, parsed.main_class
