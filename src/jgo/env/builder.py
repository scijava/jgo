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
from .bytecode import detect_jar_java_version
from .environment import Environment
from .jar import (
    autocomplete_main_class,
    classify_jar,
    detect_main_class_from_jar,
    detect_module_info,
)
from .linking import LinkStrategy, link_file
from .lockfile import LockedDependency, LockFile, compute_sha256, compute_spec_hash

if TYPE_CHECKING:
    from ..maven import Component, MavenContext
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
    coord_str: str, components: list[Component], jars_dirs: Path | list[Path]
) -> str | None:
    """
    Infer main class from a coordinate string.

    For composite coordinates (with +), tries each in order until one succeeds.

    Args:
        coord_str: Coordinate string (e.g., "org.python:jython-slim" or "org.foo:foo+org.bar:bar")
        components: List of Maven components (parallel to coord parts)
        jars_dirs: Directory or list of directories containing JAR files

    Returns:
        Inferred main class, or None if no Main-Class found
    """
    # Normalize to list
    if isinstance(jars_dirs, Path):
        dirs = [jars_dirs]
    else:
        dirs = list(jars_dirs)

    coord_parts = coord_str.split("+")

    for i, coord_part in enumerate(coord_parts):
        coord_part = coord_part.strip()
        coord = Coordinate.parse(coord_part)

        # Find matching JAR in environment (search all directories)
        for d in dirs:
            if not d.exists():
                continue
            for jar_path in d.glob("*.jar"):
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

    @staticmethod
    def is_project_mode() -> bool:
        """
        Check if we're in project mode (jgo.toml exists in CWD).

        In project mode, the cache structure is flat (.jgo/ directly).
        In ad-hoc mode, the cache uses hierarchical structure (G/A/hash/).
        """
        return Path("jgo.toml").exists()

    def from_endpoint(
        self, endpoint: str, update: bool = False, main_class: str | None = None
    ) -> Environment:
        """
        Build an environment from an endpoint string.

        Endpoint format: G:A[:V][:C][:mainClass][!][+G:A:V...]
        - Components with ! suffix are raw/unmanaged

        Args:
            endpoint: Endpoint string
            update: Force update from remote repos
            main_class: CLI override for main class (not persisted to lockfile)
        """
        # Parse endpoint
        components, coordinates, parsed_main_class = self._parse_endpoint(endpoint)

        # Determine which components should be managed
        boms = filter_managed_components(components, coordinates)

        # Temporarily store managed components for use in from_components
        self._current_boms = boms if boms else None

        # Build environment without specifying a main class
        # This allows auto-detection from the JAR manifest if not cached
        environment = self.from_components(components, update=update, main_class=None)

        # Apply runtime override with priority: CLI main class > endpoint main class > auto-detected
        # This ensures explicitly specified main classes override cached auto-detected classes
        environment._runtime_main_class = (
            main_class or parsed_main_class or environment.main_class
        )

        return environment

    def from_components(
        self,
        components: list[Component],
        update: bool = False,
        main_class: str | None = None,
    ) -> Environment:
        """
        Build an environment from a list of components (ad-hoc mode).
        """
        # Generate cache key
        cache_key = self._cache_key(components)

        # Environment path (always hierarchical for ad-hoc mode)
        primary = components[0]
        workspace_path = self.cache_dir / primary.project.path_prefix / cache_key

        # Check if environment exists and is valid
        environment = Environment(workspace_path)
        if self._is_environment_valid(environment, update):
            return environment

        # Build environment and get locked dependencies
        locked_deps = self._build_environment(environment, components, main_class)

        # Determine main class (auto-complete if needed)
        # Check both jars/ and modules/ directories for the primary artifact
        final_main_class = None
        primary_jar = None
        for dir_path in [environment.jars_dir, environment.modules_dir]:
            candidate = dir_path / primary.artifact().filename
            if candidate.exists():
                primary_jar = candidate
                break

        if main_class:
            # Search both jars/ and modules/ directories for auto-completion
            final_main_class = autocomplete_main_class(
                main_class,
                primary.artifactId,
                [environment.jars_dir, environment.modules_dir],
            )
        elif primary_jar:
            # Auto-detect from primary component JAR
            final_main_class = detect_main_class_from_jar(primary_jar)

        # Create entrypoints dict if we have a main class
        entrypoints = {}
        default_entrypoint = None
        if final_main_class:
            entrypoints["main"] = final_main_class
            default_entrypoint = "main"

        # Generate and save lockfile
        self._clear_lockfile_cache(environment)

        lockfile = LockFile(
            dependencies=locked_deps,
            min_java_version=environment.min_java_version,
            entrypoints=entrypoints,
            default_entrypoint=default_entrypoint,
            link_strategy=self.link_strategy.name,
        )
        lockfile.save(environment.lock_path)

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

        # Determine workspace path based on mode
        # Project mode: flat structure (.jgo/ directly)
        # Ad-hoc mode: hierarchical structure (G/A/hash/)
        if self.is_project_mode():
            # Flat structure for project mode
            workspace_path = cache_dir
        else:
            # Hierarchical structure for ad-hoc mode
            cache_key = self._cache_key(components)
            primary = components[0]
            workspace_path = cache_dir / primary.project.path_prefix / cache_key

        # Check if environment exists and is valid
        environment = Environment(workspace_path)
        if self._is_environment_valid(environment, update, check_staleness=True):
            return environment

        # Build environment and get locked dependencies
        locked_deps = self._build_environment(environment, components, None)

        # Infer concrete entrypoints from spec
        # Search both jars/ and modules/ directories
        concrete_entrypoints = self._infer_concrete_entrypoints(
            spec, components, [environment.jars_dir, environment.modules_dir]
        )

        # Compute spec hash for staleness detection (from root jgo.toml if it exists)
        root_spec_path = Path("jgo.toml")
        if root_spec_path.exists():
            spec_hash = compute_spec_hash(root_spec_path)
        else:
            # Use the spec path (for ad-hoc mode where we save a copy)
            spec_path = environment.path / "jgo.toml"
            spec.save(spec_path)
            spec_hash = compute_spec_hash(spec_path)

        # Generate lock file from locked dependencies
        self._clear_lockfile_cache(environment)

        lockfile = LockFile(
            dependencies=locked_deps,
            environment_name=spec.name,
            java_version=java_version or spec.java_version,
            java_vendor=spec.java_vendor,
            min_java_version=environment.min_java_version,
            entrypoints=concrete_entrypoints,
            default_entrypoint=spec.default_entrypoint,
            spec_hash=spec_hash,
            link_strategy=self.link_strategy.name,
        )
        lockfile.save(environment.lock_path)

        # In project mode, don't copy jgo.toml (root is source of truth)
        # In ad-hoc mode, save a copy for reference (already done above if needed)

        return environment

    def resolve_lockfile(
        self,
        spec: EnvironmentSpec,
        java_version: str | None = None,
    ) -> LockFile:
        """
        Resolve dependencies and create lockfile without materializing environment.

        This is used by 'jgo lock' to update jgo.lock.toml without building
        the environment directory with linked JARs.

        Args:
            spec: Environment specification
            java_version: Resolved Java version from cjdk (for lockfile)

        Returns:
            LockFile with resolved dependencies and entrypoints
        """
        import tempfile

        # Parse coordinates into components
        components = []
        for coord_str in spec.coordinates:
            coord = Coordinate.parse(coord_str)
            version = coord.version or "RELEASE"

            component = self.context.project(
                coord.groupId, coord.artifactId
            ).at_version(version)
            components.append(component)

        # Create a temporary environment directory for dependency resolution
        # This downloads JARs to Maven cache but doesn't link them permanently
        with tempfile.TemporaryDirectory() as tmp:
            temp_env = Environment(Path(tmp))
            temp_env.path.mkdir(parents=True, exist_ok=True)
            temp_env.jars_dir.mkdir(exist_ok=True)
            temp_env.modules_dir.mkdir(exist_ok=True)

            # Resolve dependencies (downloads to Maven cache, links to temp dir)
            locked_deps = self._build_environment(temp_env, components, None)

            # Infer concrete entrypoints from spec
            concrete_entrypoints = self._infer_concrete_entrypoints(
                spec, components, [temp_env.jars_dir, temp_env.modules_dir]
            )

            # Get min Java version from temp environment
            min_java_version = temp_env.min_java_version

        # Compute spec hash for staleness detection
        root_spec_path = Path("jgo.toml")
        if root_spec_path.exists():
            spec_hash = compute_spec_hash(root_spec_path)
        else:
            spec_hash = None

        # Create and return lockfile
        lockfile = LockFile(
            dependencies=locked_deps,
            environment_name=spec.name,
            java_version=java_version or spec.java_version,
            java_vendor=spec.java_vendor,
            min_java_version=min_java_version,
            entrypoints=concrete_entrypoints,
            default_entrypoint=spec.default_entrypoint,
            spec_hash=spec_hash,
            link_strategy=self.link_strategy.name,
        )

        return lockfile

    def _clear_lockfile_cache(self, environment: Environment) -> None:
        """
        Clear cached lockfile to force fresh bytecode detection.

        Called before regenerating lockfile to ensure min_java_version
        is detected from actual JARs, not stale cached values.

        Args:
            environment: Environment whose lockfile should be cleared
        """
        environment._lockfile = None
        lock_path = environment.lock_path
        if lock_path.exists():
            lock_path.unlink()

    def _is_lockfile_stale(self, environment: Environment) -> bool:
        """
        Check if lockfile is stale (spec has changed since lockfile was generated).

        Args:
            environment: Environment to check

        Returns:
            True if lockfile is stale and rebuild needed, False otherwise
        """
        lockfile = environment.lockfile
        if not lockfile or not lockfile.spec_hash:
            # No lockfile or no spec hash - can't validate staleness
            return False

        # Compute current spec hash
        root_spec_path = Path("jgo.toml")
        if root_spec_path.exists():
            current_hash = compute_spec_hash(root_spec_path)
        else:
            # Check for spec in environment directory (ad-hoc mode)
            spec_path = environment.path / "jgo.toml"
            if not spec_path.exists():
                # No spec file - can't validate staleness
                return False
            current_hash = compute_spec_hash(spec_path)

        # Compare hashes
        return current_hash != lockfile.spec_hash

    def _is_environment_valid(
        self, environment: Environment, update: bool, check_staleness: bool = False
    ) -> bool:
        """
        Check if cached environment is valid and can be reused.

        Args:
            environment: Environment to validate
            update: If True, force rebuild (returns False)
            check_staleness: If True, also check if spec-based lockfile is stale

        Returns:
            True if environment can be reused, False if rebuild needed
        """
        if not environment.path.exists() or update:
            return False

        # Validate environment has JARs
        if not environment.classpath:
            return False

        # Check if lockfile is stale (only for spec-based environments)
        if check_staleness and self._is_lockfile_stale(environment):
            return False

        return True

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
        self, spec: EnvironmentSpec, components: list[Component], jars_dirs: list[Path]
    ) -> dict[str, str]:
        """
        Infer concrete main classes from spec entrypoints.

        For each entrypoint in the spec:
        - If value contains ":" → coordinate reference → infer from JARs
        - Otherwise → class name (concrete or simple) → auto-complete if needed

        Args:
            spec: Environment specification
            components: List of Maven components
            jars_dirs: List of directories containing JAR files

        Returns:
            Dictionary of entrypoint names to concrete main class names
        """
        concrete_entrypoints = {}

        for name, value in spec.entrypoints.items():
            if is_coordinate_reference(value):
                # Coordinate reference - infer from JARs
                main_class = infer_main_class_from_coordinates(
                    value, components, jars_dirs
                )
                if main_class:
                    concrete_entrypoints[name] = main_class
                # If inference fails, omit entrypoint (no Main-Class found)
            else:
                # Class name - auto-complete if needed
                primary = components[0]
                main_class = autocomplete_main_class(
                    value, primary.artifactId, jars_dirs
                )
                concrete_entrypoints[name] = main_class

        return concrete_entrypoints

    def _build_environment(
        self,
        environment: Environment,
        components: list[Component],
        main_class: str | None,
    ) -> list[LockedDependency]:
        """
        Build the environment by resolving and linking JARs.

        JARs are separated into two directories based on module detection:
        - jars/: Non-modular JARs (class-path)
        - modules/: Modular JARs (module-path)

        Args:
            environment: Environment to build
            components: Maven components to include
            main_class: Main class (unused, kept for signature compatibility)

        Returns:
            List of locked dependencies with module info (for lock file generation)
        """
        # Create directories
        environment.path.mkdir(parents=True, exist_ok=True)
        jars_dir = environment.path / "jars"
        modules_dir = environment.path / "modules"
        jars_dir.mkdir(exist_ok=True)
        modules_dir.mkdir(exist_ok=True)

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

        # Track locked dependencies with module info
        locked_deps: list[LockedDependency] = []

        # Collect all artifact paths to determine min Java version
        # We need to know the target Java version before classifying JARs
        all_artifact_paths = []
        for component in components:
            artifact = component.artifact()
            all_artifact_paths.append(artifact.resolve())
        for dep in all_deps:
            if dep.scope in ("compile", "runtime"):
                all_artifact_paths.append(dep.artifact.resolve())

        # Determine minimum Java version by scanning all JARs
        min_java_version = None
        for jar_path in all_artifact_paths:
            if jar_path.exists():
                version = detect_jar_java_version(jar_path)
                if version:
                    min_java_version = max(min_java_version or 0, version)

        # Get JDK for module classification (only if Java 9+)
        jar_tool = None
        if min_java_version and min_java_version >= 9:
            try:
                from ..exec.java_source import JavaLocator, JavaSource

                locator = JavaLocator(java_source=JavaSource.AUTO, verbose=False)
                java_path = locator.locate(min_version=min_java_version)
                jar_tool = java_path.parent / "jar"
                if not jar_tool.exists():
                    # No jar tool available - fall back to simple detection
                    jar_tool = None
            except Exception:
                # Failed to get JDK - fall back to simple detection
                jar_tool = None

        # First, link the components themselves
        for component in components:
            artifact = component.artifact()
            source_path = artifact.resolve()

            # Classify JAR for module compatibility
            if jar_tool:
                # Java 9+ with jar tool - use precise classification
                jar_type = classify_jar(source_path, jar_tool)
                # Types 1/2/3 are modularizable, type 4 is not
                target_dir = modules_dir if jar_type in (1, 2, 3) else jars_dir
            else:
                # Java 8 or no jar tool - use simple heuristic
                module_info = detect_module_info(source_path)
                target_dir = modules_dir if module_info.is_modular else jars_dir
                jar_type = None  # Not classified

            dest_path = target_dir / artifact.filename

            if not dest_path.exists():
                link_file(source_path, dest_path, self.link_strategy)

            # For lockfile, we still need module_info for backward compat
            module_info = detect_module_info(source_path)

            # Create locked dependency with module info and classification
            sha256 = compute_sha256(source_path) if source_path.exists() else None
            locked_deps.append(
                LockedDependency(
                    groupId=artifact.groupId,
                    artifactId=artifact.artifactId,
                    version=artifact.version,
                    packaging=artifact.packaging,
                    classifier=artifact.classifier,
                    sha256=sha256,
                    is_modular=module_info.is_modular,
                    module_name=module_info.module_name,
                    jar_type=jar_type,
                )
            )

        # Track which artifacts we've already processed (from components)
        processed = {(c.groupId, c.artifactId, c.version) for c in components}

        # Link/copy dependency JARs
        for dep in all_deps:
            if dep.scope not in ("compile", "runtime"):
                continue  # Skip test deps, etc.

            artifact = dep.artifact
            key = (artifact.groupId, artifact.artifactId, artifact.version)
            if key in processed:
                continue  # Already handled as a component
            processed.add(key)

            source_path = artifact.resolve()

            # Classify JAR for module compatibility
            if jar_tool:
                # Java 9+ with jar tool - use precise classification
                jar_type = classify_jar(source_path, jar_tool)
                # Types 1/2/3 are modularizable, type 4 is not
                target_dir = modules_dir if jar_type in (1, 2, 3) else jars_dir
            else:
                # Java 8 or no jar tool - use simple heuristic
                module_info = detect_module_info(source_path)
                target_dir = modules_dir if module_info.is_modular else jars_dir
                jar_type = None  # Not classified

            dest_path = target_dir / artifact.filename

            if not dest_path.exists():
                link_file(source_path, dest_path, self.link_strategy)

            # For lockfile, we still need module_info for backward compat
            module_info = detect_module_info(source_path)

            # Create locked dependency with module info and classification
            sha256 = compute_sha256(source_path) if source_path.exists() else None
            locked_deps.append(
                LockedDependency(
                    groupId=artifact.groupId,
                    artifactId=artifact.artifactId,
                    version=artifact.version,
                    packaging=artifact.packaging,
                    classifier=artifact.classifier,
                    sha256=sha256,
                    is_modular=module_info.is_modular,
                    module_name=module_info.module_name,
                    jar_type=jar_type,
                )
            )

        # Return locked dependencies for lock file generation
        return locked_deps

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
