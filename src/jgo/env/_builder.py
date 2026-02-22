"""
EnvironmentBuilder for jgo.

Builds Environment instances from Maven coordinates.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ..constants import default_jgo_cache
from ..maven import Dependency
from ..parse import Coordinate, Endpoint
from ..util.java import JavaLocator, JavaSource
from ._bytecode import detect_jar_java_version
from ._cache import is_cache_valid, read_metadata_cache, write_metadata_cache
from ._environment import Environment
from ._jar import (
    JarType,
    ModuleInfo,
    autocomplete_main_class,
    classify_jar,
    detect_main_class_from_jar,
    detect_module_info,
    has_toplevel_classes,
)
from ._linking import LinkStrategy, link_file
from ._lockfile import LockedDependency, LockFile, compute_sha256, compute_spec_hash

if TYPE_CHECKING:
    from ..maven import Artifact, MavenContext
    from ._spec import EnvironmentSpec

_log = logging.getLogger(__name__)

# Cached baseline JDK path for JAR classification
_baseline_jar_tool: Path | None = None


def get_baseline_jar_tool() -> Path | None:
    """
    Get a consistent baseline `jar` tool for JAR classification using JavaLocator.

    This ensures that JAR module classification is deterministic across all systems,
    regardless of which Java version happens to be on the system PATH.

    Uses a cached OpenJDK 11 installation obtained via JavaLocator/cjdk. This guarantees:
    - Consistent environment structure across all systems
    - Reproducible builds (same endpoint → same jars/ vs modules/ placement)
    - Reliable CI/local parity

    Returns:
        Path to the `jar` executable, or None if unavailable
    """
    global _baseline_jar_tool

    # Return cached value if already resolved
    if _baseline_jar_tool is not None:
        return _baseline_jar_tool

    try:
        # Use JavaLocator to get a baseline Java 11 (LTS version with module support)
        # This is independent of the target environment's Java version
        # Use AUTO mode to always fetch via cjdk (not system Java)
        _log.debug("Locating baseline Java 11 for JAR classification...")
        locator = JavaLocator(
            java_source=JavaSource.AUTO,
            java_version=11,
            verbose=False,
        )
        java_path = locator.locate()

        # Derive jar tool path from java executable
        # java is at $JAVA_HOME/bin/java, jar is at $JAVA_HOME/bin/jar
        import sys

        jar_exe = "jar.exe" if sys.platform == "win32" else "jar"
        jar_tool = java_path.parent / jar_exe

        if jar_tool.exists():
            _log.debug(f"Using baseline jar tool: {jar_tool}")
            _baseline_jar_tool = jar_tool
            return jar_tool
        else:
            _log.warning(f"jar tool not found at {jar_tool}")
            _baseline_jar_tool = None  # Cache the failure to avoid repeated attempts
            return None

    except Exception as e:
        _log.warning(
            f"Failed to obtain baseline JDK for JAR classification: {e}. "
            "Falling back to simple module detection."
        )
        _baseline_jar_tool = None  # Cache the failure
        return None


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
    coord_str: str, artifacts: list[Artifact], jars_dirs: Path | list[Path]
) -> str | None:
    """
    Infer main class from a coordinate string.

    For composite coordinates (with +), tries each in order until one succeeds.

    Args:
        coord_str: Coordinate string (e.g., "org.python:jython-slim" or "org.foo:foo+org.bar:bar")
        artifacts: List of Maven artifacts (parallel to coord parts)
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
    Builds environment directories from Maven coordinates.

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
        optional_depth: int = 0,
    ):
        self.context = context
        self.link_strategy = link_strategy
        self.optional_depth = optional_depth

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
        return default_jgo_cache()

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
        parsed = Endpoint.parse(endpoint)
        parsed_main_class = parsed.main_class

        # Convert coordinates to Dependencies (preserves classifier, packaging, scope, raw)
        dependencies = self._coordinates_to_dependencies(parsed.coordinates)

        # Generate cache key from Dependencies (full classifier/packaging/scope info)
        cache_key = self._cache_key(dependencies)

        # Environment path (hierarchical for ad-hoc mode)
        primary_artifact = dependencies[0].artifact
        workspace_path = (
            self.cache_dir
            / "envs"
            / primary_artifact.component.project.path_prefix
            / cache_key
        )

        # Check cache
        environment = Environment(workspace_path)
        if self._is_environment_valid(environment, update):
            # Apply main class overrides for cached environments
            primary = dependencies[0].artifact
            autocompleted_cli_main = None
            autocompleted_parsed_main = None

            if main_class:
                autocompleted_cli_main = autocomplete_main_class(
                    main_class,
                    primary.artifactId,
                    [environment.jars_dir, environment.modules_dir],
                )

            if parsed_main_class:
                autocompleted_parsed_main = autocomplete_main_class(
                    parsed_main_class,
                    primary.artifactId,
                    [environment.jars_dir, environment.modules_dir],
                )

            environment._runtime_main_class = (
                autocompleted_cli_main
                or autocompleted_parsed_main
                or environment.main_class
            )
            return environment

        # Build environment
        locked_deps = self._build_environment(environment, dependencies, None)

        # Determine main class (auto-complete if needed)
        primary = dependencies[0].artifact
        final_main_class = None
        primary_jar = None
        for dir_path in [environment.jars_dir, environment.modules_dir]:
            candidate = dir_path / primary.filename
            if candidate.exists():
                primary_jar = candidate
                break

        if primary_jar:
            # Auto-detect from primary artifact JAR
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

        # Auto-complete main class overrides (both CLI and endpoint)
        autocompleted_cli_main = None
        autocompleted_parsed_main = None

        if main_class:
            autocompleted_cli_main = autocomplete_main_class(
                main_class,
                primary.artifactId,
                [environment.jars_dir, environment.modules_dir],
            )

        if parsed_main_class:
            autocompleted_parsed_main = autocomplete_main_class(
                parsed_main_class,
                primary.artifactId,
                [environment.jars_dir, environment.modules_dir],
            )

        # Apply runtime override with priority: CLI main class > endpoint main class > auto-detected
        environment._runtime_main_class = (
            autocompleted_cli_main
            or autocompleted_parsed_main
            or environment.main_class
        )

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
        if not spec.coordinates:
            raise ValueError("No coordinates specified in environment spec.")

        # Parse coordinates into dependencies
        coordinates = [Coordinate.parse(coord_str) for coord_str in spec.coordinates]
        dependencies = self._coordinates_to_dependencies(coordinates)
        artifacts = [dep.artifact for dep in dependencies]

        # Use spec's cache_dir if specified, otherwise use builder's default
        cache_dir = (
            Path(spec.cache_dir).expanduser() if spec.cache_dir else self.cache_dir
        )

        # Determine workspace path based on mode
        # Project mode: flat structure (.jgo/ directly)
        # Ad-hoc mode: hierarchical structure (envs/G/A/hash/)
        if self.is_project_mode():
            # Flat structure for project mode
            workspace_path = cache_dir
        else:
            # Hierarchical structure for ad-hoc mode
            cache_key = self._cache_key(dependencies)
            primary = artifacts[0]
            workspace_path = (
                cache_dir / "envs" / primary.component.project.path_prefix / cache_key
            )

        # Check if environment exists and is valid
        environment = Environment(workspace_path)
        if self._is_environment_valid(environment, update, check_staleness=True):
            return environment

        # Build environment and get locked dependencies
        locked_deps = self._build_environment(environment, dependencies, None)

        # Infer concrete entrypoints from spec
        # Search both jars/ and modules/ directories
        concrete_entrypoints = self._infer_concrete_entrypoints(
            spec, artifacts, [environment.jars_dir, environment.modules_dir]
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

        # Parse coordinates into dependencies
        coordinates = [Coordinate.parse(coord_str) for coord_str in spec.coordinates]
        dependencies = self._coordinates_to_dependencies(coordinates)
        artifacts = [dep.artifact for dep in dependencies]

        # Create a temporary environment directory for dependency resolution
        # This downloads JARs to Maven cache but doesn't link them permanently
        with tempfile.TemporaryDirectory() as tmp:
            temp_env = Environment(Path(tmp))
            temp_env.path.mkdir(parents=True, exist_ok=True)
            temp_env.jars_dir.mkdir(exist_ok=True)
            temp_env.modules_dir.mkdir(exist_ok=True)

            # Resolve dependencies (downloads to Maven cache, links to temp dir)
            locked_deps = self._build_environment(temp_env, dependencies, None)

            # Infer concrete entrypoints from spec
            concrete_entrypoints = self._infer_concrete_entrypoints(
                spec, artifacts, [temp_env.jars_dir, temp_env.modules_dir]
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

    def _coordinates_to_dependencies(
        self, coordinates: list["Coordinate"]
    ) -> list["Dependency"]:
        """
        Convert Coordinate objects to Dependency objects.

        Defaults missing versions to RELEASE and missing scopes to "compile"
        (builder-specific behavior for top-level coordinates).

        Args:
            coordinates: List of parsed Coordinate objects with full coordinate info

        Returns:
            List of Dependency objects
        """
        dependencies = []
        for coord in coordinates:
            # Default version to RELEASE and scope to "compile" if not specified
            # (builder-specific behavior for top-level user coordinates)
            if not coord.version or not coord.scope:
                coord = Coordinate(
                    groupId=coord.groupId,
                    artifactId=coord.artifactId,
                    version=coord.version or "RELEASE",
                    classifier=coord.classifier,
                    packaging=coord.packaging,
                    scope=coord.scope or "compile",
                    optional=coord.optional,
                    raw=coord.raw,
                    placement=coord.placement,
                )

            # Use MavenContext.create_dependency to avoid code duplication
            # TODO: Pass exclusions when exclusion parsing is implemented
            dependency = self.context.create_dependency(coord, exclusions=None)
            dependencies.append(dependency)

        return dependencies

    def _cache_key(self, dependencies: list["Dependency"]) -> str:
        """
        Generate a stable hash for a set of dependencies.

        Uses full artifact coordinates (G:A:V:C:P) plus exclusions to ensure:
        - Different classifiers get different caches (e.g., natives-linux vs natives-windows)
        - Different packaging types get different caches
        - Different exclusions get different caches (different dependency trees)

        Args:
            dependencies: List of Dependency objects with full coordinate info and exclusions

        Returns:
            16-character hex hash string
        """
        # Sort to ensure stable ordering
        # Use resolved version to ensure RELEASE/LATEST resolve to consistent cache keys
        coord_strings = []
        for dep in sorted(
            dependencies,
            key=lambda d: (
                d.artifact.groupId,
                d.artifact.artifactId,
                d.artifact.version,  # This resolves RELEASE/LATEST
                d.artifact.classifier,
                d.artifact.packaging,
            ),
        ):
            # Include full artifact coordinates: G:A:V:C:P
            coord_str = (
                f"{dep.artifact.groupId}:"
                f"{dep.artifact.artifactId}:"
                f"{dep.artifact.version}:"  # Resolved version
                f"{dep.artifact.classifier}:"
                f"{dep.artifact.packaging}"
            )

            # Include exclusions for this dependency
            if dep.exclusions:
                excl_strs = sorted(
                    [f"{e.groupId}:{e.artifactId}" for e in dep.exclusions]
                )
                coord_str += f":excl={','.join(excl_strs)}"

            coord_strings.append(coord_str)

        combined = "+".join(coord_strings)

        # Include optional_depth in cache key
        # This ensures different optional_depth values get separate cache directories
        combined += f":optional_depth={self.optional_depth}"

        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _infer_concrete_entrypoints(
        self, spec: EnvironmentSpec, artifacts: list[Artifact], jars_dirs: list[Path]
    ) -> dict[str, str]:
        """
        Infer concrete main classes from spec entrypoints.

        For each entrypoint in the spec:
        - If value contains ":" → coordinate reference → infer from JARs
        - Otherwise → class name (concrete or simple) → auto-complete if needed

        Args:
            spec: Environment specification
            artifacts: List of Maven artifacts
            jars_dirs: List of directories containing JAR files

        Returns:
            Dictionary of entrypoint names to concrete main class names
        """
        concrete_entrypoints = {}

        for name, value in spec.entrypoints.items():
            if is_coordinate_reference(value):
                # Coordinate reference - infer from JARs
                main_class = infer_main_class_from_coordinates(
                    value, artifacts, jars_dirs
                )
                if main_class:
                    concrete_entrypoints[name] = main_class
                # If inference fails, omit entrypoint (no Main-Class found)
            else:
                # Class name - auto-complete if needed
                primary = artifacts[0]
                main_class = autocomplete_main_class(
                    value, primary.artifactId, jars_dirs
                )
                concrete_entrypoints[name] = main_class

        return concrete_entrypoints

    def _build_environment(
        self,
        environment: Environment,
        dependencies: list[Dependency],
        main_class: str | None,
    ) -> list[LockedDependency]:
        """
        Build the environment by resolving and linking JARs.

        JARs are separated into two directories based on module detection:
        - jars/: Non-modular JARs (class-path)
        - modules/: Modular JARs (module-path)

        Args:
            environment: Environment to build
            dependencies: Input dependencies to resolve
            main_class: Main class (unused, kept for signature compatibility)

        Returns:
            List of locked dependencies with module info (for lock file generation)
        """
        # Create directories
        environment.path.mkdir(parents=True, exist_ok=True)
        jars_dir = environment.path / "jars"
        modules_dir = environment.path / "modules"

        # Clean existing JARs to prevent duplicates across jars/ and modules/
        # This ensures JARs are only in one directory based on current classification
        for dir_path in [jars_dir, modules_dir]:
            if dir_path.exists():
                for jar_file in dir_path.glob("*.jar"):
                    jar_file.unlink()

        jars_dir.mkdir(exist_ok=True)
        modules_dir.mkdir(exist_ok=True)

        # Resolve all dependencies together (not separately!)
        # This ensures Maven handles version conflicts across all dependencies
        # Returns (resolved_inputs, resolved_transitive) where:
        # - resolved_inputs: Input deps with MANAGED versions resolved
        # - resolved_transitive: Transitive dependencies (excludes inputs)
        resolved_inputs, resolved_transitive = dependencies[0].context.resolver.resolve(
            dependencies,
            optional_depth=self.optional_depth,
        )

        # Track locked dependencies with module info
        locked_deps: list[LockedDependency] = []

        # Collect all artifact paths to determine min Java version
        # We need to know the target Java version before classifying JARs
        all_artifact_paths = []
        # Process resolved artifacts first
        for dep in resolved_inputs:
            all_artifact_paths.append(dep.artifact.resolve())
        # Then transitive dependencies
        for dep in resolved_transitive:
            if dep.scope in ("compile", "runtime"):
                all_artifact_paths.append(dep.artifact.resolve())

        # Determine minimum Java version by scanning all JARs
        min_java_version = None
        for jar_path in all_artifact_paths:
            if jar_path.exists():
                version = detect_jar_java_version(jar_path)
                if version:
                    min_java_version = max(min_java_version or 0, version)

        # Lazy-initialize baseline jar tool only when needed
        # Sentinel value to detect if we've tried to get it yet
        jar_tool_state = {"tool": None, "initialized": False}

        def get_jar_tool_lazy():
            """Get baseline jar tool lazily (only when actually needed)."""
            if not jar_tool_state["initialized"]:
                # Get baseline JDK for module classification
                # This uses a consistent Java 11 via cjdk, ensuring deterministic builds
                # regardless of what Java version is on the system PATH
                jar_tool_state["tool"] = get_baseline_jar_tool()
                jar_tool_state["initialized"] = True
            return jar_tool_state["tool"]

        # Helper function to classify and link a JAR artifact
        def process_artifact(artifact, source_path):
            """Classify JAR, link it to the appropriate directory, and create locked dependency."""
            # Compute SHA256 first (needed for cache and lockfile)
            sha256 = compute_sha256(source_path) if source_path.exists() else None

            # Try to read from metadata cache first
            cached_metadata = None
            if sha256:
                cached_metadata = read_metadata_cache(
                    artifact.groupId,
                    artifact.artifactId,
                    artifact.version,
                    artifact.filename,
                    self.cache_dir,
                )
                # Validate cache by SHA256
                if cached_metadata and is_cache_valid(cached_metadata, sha256):
                    # Cache hit! Use cached values
                    min_java_ver = cached_metadata.min_java_version
                    jar_type = cached_metadata.jar_type
                    module_info = ModuleInfo(**cached_metadata.module_info)
                    _log.debug(f"Using cached metadata for {artifact.filename}")
                else:
                    # Cache miss or invalid - will compute below
                    cached_metadata = None

            # If we didn't get valid cached data, compute it now
            if cached_metadata is None:
                # Detect minimum Java version from bytecode
                min_java_ver = detect_jar_java_version(source_path)

                # Use fast module detection (no subprocess)
                module_info = detect_module_info(source_path)

                # Get jar tool lazily only when we need it
                jar_tool = get_jar_tool_lazy()

                if jar_tool:
                    # Baseline jar tool available - use precise classification
                    if module_info.is_modular:
                        # Fast path: JAR has module-info.class or Automatic-Module-Name
                        jar_type = (
                            JarType.AUTOMATIC
                            if module_info.is_automatic
                            else JarType.EXPLICIT
                        )
                        # AUTOMATIC JARs with classes in the unnamed package cannot be
                        # used on the module path - Java raises
                        # InvalidModuleDescriptorException at runtime.
                        if jar_type == JarType.AUTOMATIC and has_toplevel_classes(
                            source_path
                        ):
                            jar_type = JarType.PLAIN
                    else:
                        # Slow path: Need subprocess to distinguish DERIVABLE vs PLAIN
                        _log.debug(
                            f"Analyzing JAR for modularizability: {artifact.filename}"
                        )
                        jar_type = classify_jar(source_path, jar_tool)
                else:
                    # No jar tool available - use simple module detection
                    jar_type = None  # Not classified

                # Write to cache for next time
                if sha256:
                    write_metadata_cache(
                        artifact.groupId,
                        artifact.artifactId,
                        artifact.version,
                        artifact.filename,
                        self.cache_dir,
                        sha256,
                        jar_type,
                        min_java_ver,
                        module_info,
                    )

            # Determine target directory based on jar_type
            if jar_type is not None:
                target_dir = modules_dir if jar_type != JarType.PLAIN else jars_dir
            else:
                # No classification - use module_info
                target_dir = modules_dir if module_info.is_modular else jars_dir

            dest_path = target_dir / artifact.filename

            if not dest_path.exists():
                link_file(source_path, dest_path, self.link_strategy)

            # Create locked dependency with module info and classification
            return LockedDependency(
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

        # Process artifacts and their transitive dependencies
        # Track processed artifacts to avoid duplicates
        # Use artifact.key which includes classifier and packaging to handle
        # multiple artifacts with same G:A:V (e.g., natives for different platforms)
        processed = set()

        # First, process the resolved artifacts (with MANAGED versions resolved)
        for dep in resolved_inputs:
            artifact = dep.artifact
            if artifact.key in processed:
                continue  # Skip duplicates
            processed.add(artifact.key)

            source_path = artifact.resolve()
            locked_deps.append(process_artifact(artifact, source_path))

        # Then, process transitive dependencies
        for dep in resolved_transitive:
            if dep.scope not in ("compile", "runtime"):
                continue  # Skip test deps, etc.

            artifact = dep.artifact
            if artifact.key in processed:
                continue  # Skip duplicates
            processed.add(artifact.key)

            source_path = artifact.resolve()
            locked_deps.append(process_artifact(artifact, source_path))

        # Return locked dependencies for lock file generation
        return locked_deps
