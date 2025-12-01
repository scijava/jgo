"""
EnvironmentBuilder for jgo 2.0.

Builds Environment instances from Maven components or endpoint strings.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import hashlib
from jgo.maven import MavenContext, Component
from .environment import Environment
from .linking import LinkStrategy, link_file
from .spec import EnvironmentSpec
from .lockfile import LockFile


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
        maven_context: MavenContext,
        cache_dir: Optional[Path] = None,
        link_strategy: LinkStrategy = LinkStrategy.AUTO,
        managed: bool = False,
    ):
        self.maven_context = maven_context
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
        self, endpoint: str, update: bool = False, main_class: Optional[str] = None
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
            managed_components = components
        else:
            # Use explicit ! markers to determine which components are managed
            managed_components = [
                comp
                for comp, is_managed in zip(components, managed_flags)
                if is_managed
            ]

        # Temporarily store managed_components for use in from_components
        self._current_managed_components = (
            managed_components if managed_components else None
        )

        # Use parsed main class if caller didn't provide one
        if main_class is None:
            main_class = parsed_main_class

        # Build environment
        return self.from_components(components, update=update, main_class=main_class)

    def from_components(
        self,
        components: List[Component],
        update: bool = False,
        main_class: Optional[str] = None,
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
                # Environment is valid, use it
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
        entrypoint: Optional[str] = None,
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

            component = self.maven_context.project(groupId, artifactId).at_version(
                version
            )
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

    def _cache_key(self, components: List[Component]) -> str:
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
        components: List[Component],
        main_class: Optional[str],
    ) -> List:
        """
        Actually build the environment by resolving and linking JARs.

        Returns:
            List of resolved dependencies (for lock file generation)
        """
        # Create directories
        environment.path.mkdir(parents=True, exist_ok=True)
        jars_dir = environment.path / "jars"
        jars_dir.mkdir(exist_ok=True)

        # Resolve dependencies
        all_deps = []

        # First, link the components themselves
        for component in components:
            artifact = component.artifact()
            source_path = artifact.resolve()
            dest_path = jars_dir / artifact.filename

            if not dest_path.exists():
                link_file(source_path, dest_path, self.link_strategy)

        # Then resolve and link their dependencies
        # Use the resolver from maven_context to respect --resolver flag
        # Use managed components from endpoint parsing (stored in _current_managed_components)
        # or fall back to old behavior for backward compatibility
        managed_components = getattr(self, "_current_managed_components", None)
        if managed_components is None and self.managed:
            # Backward compatibility: if -m flag is set but no explicit markers, manage all
            managed_components = components

        for component in components:
            deps = component.maven_context.resolver.dependencies(
                component,
                managed=bool(managed_components),
                managed_components=managed_components,
            )
            all_deps.extend(deps)

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
            environment.set_main_class(main_class)
        else:
            # Auto-detect from primary component JAR
            from .jar_util import detect_main_class_from_jar

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
    ) -> Tuple[List[Component], List[bool], Optional[str]]:
        """
        Parse endpoint string into components and main class.

        Returns:
            Tuple of (components_list, managed_flags, main_class)
            - components_list: List of Component objects
            - managed_flags: List of booleans indicating if each component should be managed (has ! suffix)
            - main_class: Main class to run (only from first endpoint part)
        """
        import re

        # Split on + for multiple components
        parts = endpoint.split("+")
        components = []
        managed_flags = []
        main_class = None

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
                    part_main_class = tokens[2]

            elif len(tokens) == 4:
                # G:A:V:C or G:A:V:mainClass
                # If tokens[3] contains a dot, it's likely a main class
                version = tokens[2]
                if "." in tokens[3] or tokens[3][0].isupper():
                    part_main_class = tokens[3]
                else:
                    classifier = tokens[3]  # noqa: F841 - TODO: Use when Component supports classifiers

            elif len(tokens) == 5:
                # G:A:V:C:mainClass
                version = tokens[2]
                classifier = tokens[3]  # noqa: F841 - TODO: Use when Component supports classifiers
                part_main_class = tokens[4]

            # Only the first endpoint can specify main class
            if i == 0 and part_main_class:
                main_class = part_main_class

            # Create component
            component = self.maven_context.project(groupId, artifactId).at_version(
                version
            )
            # TODO: Handle classifier when Component supports it
            components.append(component)
            managed_flags.append(is_managed)

        return components, managed_flags, main_class
