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


class EnvironmentBuilder:
    """
    Builds environment directories from Maven components.
    """

    def __init__(
        self,
        maven_context: MavenContext,
        cache_dir: Path,
        link_strategy: LinkStrategy = LinkStrategy.AUTO,
    ):
        self.maven_context = maven_context
        self.cache_dir = Path(cache_dir).expanduser()
        self.link_strategy = link_strategy

    def from_endpoint(
        self, endpoint: str, update: bool = False, main_class: Optional[str] = None
    ) -> Environment:
        """
        Build an environment from an endpoint string.

        Endpoint format: G:A[:V][:C][:mainClass][+G:A:V...]
        """
        # Parse endpoint
        components, parsed_main_class = self._parse_endpoint(endpoint)

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
            # TODO: Validate environment is up to date
            return environment

        # Build/rebuild environment
        self._build_environment(environment, components, main_class)

        return environment

    def _cache_key(self, components: List[Component]) -> str:
        """Generate a stable hash for a set of components."""
        # Sort to ensure stable ordering
        coord_strings = sorted(
            [f"{c.groupId}:{c.artifactId}:{c.version}" for c in components]
        )
        combined = "+".join(coord_strings)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _build_environment(
        self,
        environment: Environment,
        components: List[Component],
        main_class: Optional[str],
    ):
        """Actually build the environment by resolving and linking JARs."""
        # Create directories
        environment.path.mkdir(parents=True, exist_ok=True)
        jars_dir = environment.path / "jars"
        jars_dir.mkdir(exist_ok=True)

        # Resolve dependencies
        from jgo.maven import Model

        all_deps = []
        for component in components:
            model = Model(component.pom())
            deps = model.dependencies()
            all_deps.extend(deps)

        # Link/copy JARs
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
            f"{c.groupId}:{c.artifactId}:{c.version}" for c in components
        ]
        environment.manifest["link_strategy"] = self.link_strategy.name
        environment.save_manifest()

        # Detect/set main class
        if main_class:
            environment.set_main_class(main_class)
        else:
            # TODO: Auto-detect from primary component
            pass

    def _parse_endpoint(self, endpoint: str) -> Tuple[List[Component], Optional[str]]:
        """
        Parse endpoint string into components and main class.

        Returns:
            Tuple of (components_list, main_class)
            Only the first endpoint part can specify a main class.
        """
        import re

        # Split on + for multiple components
        parts = endpoint.split("+")
        components = []
        main_class = None

        for i, part in enumerate(parts):
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

        return components, main_class
