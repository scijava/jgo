# Quick Start Guide: Implementing jgo 2.0

This guide helps you get started implementing jgo 2.0 based on the detailed plans.

## Prerequisites

1. Read the full implementation plan: `JGO_2.0_PLAN.md`
2. Understand the migration examples: `MIGRATION_EXAMPLE.md`
3. Review the roadmap: `IMPLEMENTATION_ROADMAP.md`

## Day 1: Setup and Foundation

### Morning: Project Setup

```bash
# 1. Create feature branch
git checkout -b feat/jgo-2.0

# 2. Create new module structure
mkdir -p src/jgo/{maven,env,exec,cli,config,compat,util}

# 3. Create __init__.py files
touch src/jgo/maven/__init__.py
touch src/jgo/env/__init__.py
touch src/jgo/exec/__init__.py
touch src/jgo/cli/__init__.py
touch src/jgo/config/__init__.py
touch src/jgo/compat/__init__.py
touch src/jgo/util/__init__.py

# 4. Copy maven.py from db-xml-maven
cp ../../ctrueden/db-xml-maven/maven.py src/jgo/maven/core.py
```

### Afternoon: Split maven.py into Modules

The current `maven.py` is monolithic. Split it into:

```python
# src/jgo/maven/__init__.py
"""
Maven dependency resolution for Python.

This module provides pure-Python Maven functionality including:
- Dependency resolution (transitive dependencies, scopes, exclusions)
- POM parsing and property interpolation
- Metadata querying (available versions, release/snapshot)
- Artifact downloading from Maven repositories
"""

from .core import Environment, Project, Component, Artifact, Dependency
from .resolver import Resolver, SimpleResolver, MavenResolver
from .pom import POM
from .metadata import Metadata, MetadataXML
from .model import Model

__all__ = [
    "Environment",
    "Project",
    "Component",
    "Artifact",
    "Dependency",
    "Resolver",
    "SimpleResolver",
    "MavenResolver",
    "POM",
    "Metadata",
    "MetadataXML",
    "Model",
]
```

Split the code:
- `core.py` - Environment, Project, Component, Artifact, Dependency, XML
- `resolver.py` - Resolver, SimpleResolver, MavenResolver (renamed from SysCallResolver)
- `pom.py` - POM class
- `metadata.py` - Metadata, MetadataXML, Metadatas
- `model.py` - Model class (dependency resolution logic)
- `util.py` - Helper functions (ts2dt, coord2str, etc.)

## Day 2-3: Fix Critical Maven Issues

### Priority 1: Fix Property Interpolation in G/A/C

**Location:** `src/jgo/maven/model.py` around line 1022

**Current issue:**
```python
# model.py line 1020-1032
for dep in list(self.deps.values()) + list(self.dep_mgmt.values()):
    # CTR START HERE --
    # We need to interpolate into dep fields other than version.
    v = dep.version
    if v is not None: dep.set_version(Model._evaluate(v, self.props))
```

**Fix approach:**

Move interpolation earlier, to `Environment.dependency()`:

```python
# src/jgo/maven/core.py, in Environment.dependency() method around line 299

def dependency(self, el: ElementTree.Element) -> "Dependency":
    """
    Create a Dependency object from the given XML element.
    :param el: The XML element from which to create the dependency.
    :return: The Dependency object.
    """
    # Extract raw values
    groupId = el.findtext("groupId")
    artifactId = el.findtext("artifactId")
    version = el.findtext("version")
    classifier = el.findtext("classifier") or DEFAULT_CLASSIFIER
    packaging = el.findtext("type") or DEFAULT_PACKAGING

    # NEW: Interpolate G/A/C/V early, BEFORE creating GACT key
    # This requires access to properties - pass them in or make dependency
    # creation happen later in the Model building process
    # For now, only version needs interpolation typically

    # ... rest of method
```

**Better approach:** Defer interpolation to Model building:

1. Keep `Environment.dependency()` as-is (creates raw dependencies)
2. In `Model._merge()`, after merging from POM, interpolate all dependency fields
3. This requires modifying the GACT dict keys after interpolation
4. Solution: Create a new dict with interpolated keys

```python
# src/jgo/maven/model.py

def _interpolate_dependency_coords(self):
    """
    Interpolate ${...} expressions in dependency coordinates.
    This must happen after properties are fully merged but before
    using dependencies, because it changes GACT keys.
    """
    # Interpolate deps
    new_deps = {}
    for gact, dep in self.deps.items():
        # Interpolate each field
        g = Model._evaluate(dep.groupId, self.props) if dep.groupId else None
        a = Model._evaluate(dep.artifactId, self.props) if dep.artifactId else None
        c = Model._evaluate(dep.classifier, self.props) if dep.classifier else None
        t = Model._evaluate(dep.type, self.props) if dep.type else None
        v = Model._evaluate(dep.version, self.props) if dep.version else None

        # Update dependency fields (need to add setters)
        # This is the tricky part - need to update the artifact's component
        # Better: create new dependency with interpolated values

        new_gact = (g, a, c, t)
        if new_gact != gact:
            # Key changed! Check for collisions
            if new_gact in new_deps:
                _log.warning(f"Interpolation caused key collision: {gact} -> {new_gact}")
                # Keep the one that was in the original dict (nearest wins)
                continue
        new_deps[new_gact] = dep

    self.deps = new_deps

    # Same for dep_mgmt
    # ... similar logic
```

Call this in `Model.__init__()` after model interpolation step.

### Priority 2: Add Tests

Create `tests/test_maven.py`:

```python
import pytest
from jgo.maven import MavenContext, Model

class TestPropertyInterpolation:
    def test_version_interpolation(self):
        """Test that ${project.version} in version field works."""
        # Use a real POM that does this
        maven = MavenContext()
        component = maven.project("org.scijava", "scijava-common").at_version("2.96.0")
        model = Model(component.pom())

        # All versions should be interpolated (no ${...})
        for dep in model.dependencies():
            assert "$" not in dep.version, f"Uninterpolated version: {dep}"

    def test_groupid_interpolation(self):
        """Test that ${project.groupId} in groupId field works."""
        # Find or create a POM that uses this
        # e.g., miglayout-swing depending on miglayout-core
        maven = MavenContext()
        component = maven.project("com.miglayout", "miglayout-swing").at_version("5.3")
        model = Model(component.pom())

        for dep in model.dependencies():
            assert "$" not in dep.groupId, f"Uninterpolated groupId: {dep}"
```

## Day 4-5: Environment Layer

### Create Environment Class

```python
# src/jgo/env/environment.py

from pathlib import Path
from typing import List, Optional
import json

class Environment:
    """
    A materialized Maven environment - a directory containing JARs.
    """

    def __init__(self, path: Path):
        self.path = path
        self._manifest = None

    @property
    def manifest_path(self) -> Path:
        return self.path / "manifest.json"

    @property
    def manifest(self) -> dict:
        """Load manifest.json with metadata about this environment."""
        if self._manifest is None:
            if self.manifest_path.exists():
                with open(self.manifest_path) as f:
                    self._manifest = json.load(f)
            else:
                self._manifest = {}
        return self._manifest

    def save_manifest(self):
        """Save manifest.json."""
        with open(self.manifest_path, 'w') as f:
            json.dump(self._manifest, f, indent=2)

    @property
    def classpath(self) -> List[Path]:
        """List of JAR files in this environment."""
        jars_dir = self.path / "jars"
        if not jars_dir.exists():
            return []
        return sorted(jars_dir.glob("*.jar"))

    @property
    def main_class(self) -> Optional[str]:
        """Main class for this environment (if detected/specified)."""
        main_class_file = self.path / "main-class.txt"
        if main_class_file.exists():
            return main_class_file.read_text().strip()
        return self.manifest.get("main_class")

    def set_main_class(self, main_class: str):
        """Set the main class for this environment."""
        main_class_file = self.path / "main-class.txt"
        main_class_file.write_text(main_class)
        self.manifest["main_class"] = main_class
        self.save_manifest()
```

### Create EnvironmentBuilder

```python
# src/jgo/env/builder.py

from pathlib import Path
from typing import List, Optional
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
        maven_context: Environment,
        cache_dir: Path,
        link_strategy: LinkStrategy = LinkStrategy.AUTO
    ):
        self.maven_env = maven_env
        self.cache_dir = Path(cache_dir).expanduser()
        self.link_strategy = link_strategy

    def from_endpoint(
        self,
        endpoint: str,
        update: bool = False,
        main_class: Optional[str] = None
    ) -> Environment:
        """
        Build an environment from an endpoint string.

        Endpoint format: G:A[:V][:C][:mainClass][+G:A:V...]
        """
        # Parse endpoint
        components = self._parse_endpoint(endpoint)

        # Build environment
        return self.from_components(components, update=update, main_class=main_class)

    def from_components(
        self,
        components: List[Component],
        update: bool = False,
        main_class: Optional[str] = None
    ) -> Environment:
        """
        Build an environment from a list of components.
        """
        # Generate cache key
        cache_key = self._cache_key(components)

        # Environment path
        primary = components[0]
        workspace_path = (
            self.cache_dir /
            primary.project.path_prefix /
            cache_key
        )

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
        coord_strings = sorted([
            f"{c.groupId}:{c.artifactId}:{c.version}"
            for c in components
        ])
        combined = "+".join(coord_strings)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _build_environment(
        self,
        environment: Environment,
        components: List[Component],
        main_class: Optional[str]
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
            f"{c.groupId}:{c.artifactId}:{c.version}"
            for c in components
        ]
        environment.manifest["link_strategy"] = self.link_strategy.name
        environment.save_manifest()

        # Detect/set main class
        if main_class:
            environment.set_main_class(main_class)
        else:
            # TODO: Auto-detect from primary component
            pass

    def _parse_endpoint(self, endpoint: str) -> List[Component]:
        """Parse endpoint string into components."""
        # Split on +
        parts = endpoint.split("+")
        components = []

        for part in parts:
            # Parse G:A:V:C:mainClass
            tokens = part.split(":")
            # ... parsing logic
            pass

        return components
```

## Testing Your Progress

After each day, run:

```bash
# Run tests
pytest tests/

# Try the CLI (once implemented)
python -m jgo org.python:jython-standalone --print-classpath

# Try the Python API
python -c "
from jgo.maven import MavenContext
maven = MavenContext()
project = maven.project('org.scijava', 'scijava-common')
print(f'Latest version: {project.release}')
"
```

## Getting Help

If stuck:
1. Review the original `maven.py` in `db-xml-maven`
2. Check Maven documentation
3. Look at how jgo 1.x does it
4. Ask specific questions about architecture decisions

## Key Principles

1. **Keep layers separate** - Maven layer should not know about Environment
2. **Test as you go** - Write tests for each component
3. **Use type hints** - Makes the code more maintainable
4. **Document thoroughly** - Docstrings for all public APIs
5. **Maintain compatibility** - Don't break existing users

## Next Steps

Once you have:
- Maven layer working with interpolation fix
- Environment layer building workspaces
- Basic tests passing

Then move on to:
- Execution layer (JavaRunner)
- CLI redesign
- Backward compatibility
- Documentation

Good luck! 🚀
