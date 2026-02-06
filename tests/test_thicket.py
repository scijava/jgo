"""
Test dependency resolution using the thicket - a complex POM hierarchy.

The thicket is a generated collection of POMs with:
- Multi-level parent POM inheritance (up to 4 levels)
- BOM imports (up to 3 per POM, recursively)
- Property-based versioning
- Complex dependency management

This provides a robust test of jgo's Maven model building, property
interpolation, BOM import, and dependency management injection.
"""

import shutil

import pytest

from jgo.maven import MavenContext
from jgo.maven.model import Model
from jgo.maven.pom import POM


@pytest.fixture
def thicket_dir(thicket_poms):
    """Get the directory containing thicket POMs."""
    return thicket_poms


@pytest.fixture
def thicket_pom(thicket_poms):
    """Get the path to the main thicket.pom file."""
    return thicket_poms / "thicket.pom"


@pytest.fixture
def thicket_context(thicket_poms, tmp_path):
    """
    Create a MavenContext with a temporary local repository containing thicket POMs.

    This sets up a proper Maven repository structure:
    - repo_cache/org/scijava/jgo/thicket/{artifactId}/{version}/{artifactId}-{version}.pom

    This allows testing without requiring Maven installation or modifying ~/.m2/repository.
    """
    # Create temporary repository directory
    repo_cache = tmp_path / "m2-repo"
    repo_cache.mkdir(parents=True, exist_ok=True)

    # Process all thicket POMs
    for pom_file in thicket_poms.glob("thicket*.pom"):
        # Skip the effective POM if it exists
        if pom_file.name.startswith("thicket-effective"):
            continue

        # Parse POM to get coordinates
        pom = POM(pom_file)
        group_id = pom.groupId or "org.scijava.jgo.thicket"
        artifact_id = pom.artifactId
        version = pom.version

        if not artifact_id or not version:
            continue

        # Create Maven directory structure: groupId/artifactId/version/
        group_path = "/".join(group_id.split("."))
        pom_dir = repo_cache / group_path / artifact_id / version
        pom_dir.mkdir(parents=True, exist_ok=True)

        # Copy POM to proper location: artifactId-version.pom
        dest_pom = pom_dir / f"{artifact_id}-{version}.pom"
        shutil.copy(pom_file, dest_pom)

    # Create MavenContext pointing to temp repository
    return MavenContext(repo_cache=repo_cache)


class TestThicketBasic:
    """Basic tests that the thicket POM can be loaded and parsed."""

    def test_thicket_pom_exists(self, thicket_pom):
        """Verify thicket.pom exists and is valid XML."""
        assert thicket_pom.exists(), f"Thicket POM not found at {thicket_pom}"

        # Try to parse it
        pom = POM(thicket_pom)

        assert pom.groupId == "org.scijava.jgo.thicket"
        assert pom.artifactId == "thicket"
        assert pom.version is not None

    def test_thicket_has_parent(self, thicket_pom):
        """Verify thicket has a parent POM."""
        pom = POM(thicket_pom)

        parent_artifact = pom.value("parent/artifactId")
        assert parent_artifact is not None
        assert parent_artifact.startswith("thicket-parent")

    def test_thicket_has_boms(self, thicket_pom):
        """Verify thicket imports BOMs."""
        pom = POM(thicket_pom)

        # Check for import-scoped dependencies
        imports = [
            el
            for el in pom.elements("dependencyManagement/dependencies/dependency")
            if el.findtext("scope") == "import"
        ]
        assert len(imports) > 0, "Thicket should have at least one BOM import"

    def test_thicket_has_managed_deps(self, thicket_pom):
        """Verify thicket has managed dependencies."""
        pom = POM(thicket_pom)

        managed_deps = pom.elements("dependencyManagement/dependencies/dependency")
        assert len(managed_deps) > 0, "Thicket should have managed dependencies"


class TestThicketModel:
    """Test that the Model can be built from the thicket POM."""

    def test_model_building(self, thicket_pom, thicket_context):
        """
        Test that a Model can be built from the thicket POM.

        Uses a temporary local repository with thicket POMs.
        """
        # Read the thicket version from the POM
        thicket_pom_obj = POM(thicket_pom)
        version = thicket_pom_obj.version

        component = thicket_context.project(
            "org.scijava.jgo.thicket", "thicket"
        ).at_version(version)

        pom = component.pom()
        model = Model(pom, thicket_context)

        # Model should have been built successfully
        assert model is not None
        assert model.gav.startswith("org.scijava.jgo.thicket:thicket:")

    def test_property_interpolation(self, thicket_pom, thicket_context):
        """
        Test that properties are correctly interpolated in the thicket.

        The thicket uses property-based versioning, so this tests that:
        - Properties from parent POMs are inherited
        - Properties are used in dependency management
        - Property references like ${artifact.version} are resolved
        """
        # Read the thicket version from the POM
        thicket_pom_obj = POM(thicket_pom)
        version = thicket_pom_obj.version

        component = thicket_context.project(
            "org.scijava.jgo.thicket", "thicket"
        ).at_version(version)

        pom = component.pom()
        model = Model(pom, thicket_context)

        # Check that all managed dependencies have interpolated versions
        for dep in model.dep_mgmt.values():
            if dep.version:
                assert "${" not in dep.version, (
                    f"Uninterpolated property in {dep.groupId}:{dep.artifactId}: {dep.version}"
                )

    def test_bom_imports(self, thicket_pom, thicket_context):
        """
        Test that BOM imports work correctly.

        The thicket has multiple levels of BOM imports, which tests:
        - BOMs are imported in the correct order
        - Dependency management from BOMs is merged correctly
        - Transitive BOM imports work (BOMs importing other BOMs)
        """
        # Read the thicket version from the POM
        thicket_pom_obj = POM(thicket_pom)
        version = thicket_pom_obj.version

        component = thicket_context.project(
            "org.scijava.jgo.thicket", "thicket"
        ).at_version(version)

        pom = component.pom()

        # Count direct BOM imports
        raw_pom = POM(pom.source if isinstance(pom, POM) else pom)
        direct_imports = len(
            [
                el
                for el in raw_pom.elements(
                    "dependencyManagement/dependencies/dependency"
                )
                if el.findtext("scope") == "import"
            ]
        )

        # Build the model
        model = Model(pom, thicket_context)

        # The model should have more managed dependencies than just the direct imports,
        # because BOMs import other BOMs transitively
        assert len(model.dep_mgmt) > direct_imports, (
            "Expected transitive BOM imports to increase managed dependencies. "
            f"Direct imports: {direct_imports}, total managed: {len(model.dep_mgmt)}"
        )

    def test_parent_inheritance(self, thicket_pom, thicket_context):
        """
        Test that parent POM properties and dependency management are inherited.

        The thicket has up to 4 levels of parent POMs, which tests:
        - Properties flow down the inheritance chain
        - Dependency management is inherited
        - Child POMs can override parent values
        """
        # Read the thicket version from the POM
        thicket_pom_obj = POM(thicket_pom)
        version = thicket_pom_obj.version

        component = thicket_context.project(
            "org.scijava.jgo.thicket", "thicket"
        ).at_version(version)

        pom = component.pom()
        model = Model(pom, thicket_context)

        # The model should have properties from all parent POMs
        # We can't check specific properties since they're randomly generated,
        # but we can verify that we have some properties
        assert len(model.props) > 0, "Model should have properties from parents"


class TestThicketGeneration:
    """Test the thicket generation script itself."""

    def test_thicket_poms_count(self, thicket_dir):
        """Verify that multiple thicket POMs were generated."""
        pom_files = list(thicket_dir.glob("*.pom"))
        # Filter out the effective POM if it exists
        pom_files = [f for f in pom_files if not f.name.startswith("thicket-effective")]

        # Should have at least the main thicket.pom plus parents and BOMs
        assert len(pom_files) >= 5, (
            f"Expected at least 5 thicket POMs, found {len(pom_files)}."
        )

    def test_thicket_naming_convention(self, thicket_dir):
        """Verify thicket POMs follow the expected naming convention."""
        pom_files = list(thicket_dir.glob("thicket*.pom"))
        pom_files = [f for f in pom_files if not f.name.startswith("thicket-effective")]

        # All POMs should start with "thicket"
        for pom_file in pom_files:
            assert pom_file.name.startswith("thicket"), (
                f"Unexpected POM name: {pom_file.name}"
            )


class TestThicketDocumentation:
    """Verify thicket has proper documentation for developers."""

    def test_thicket_script_has_docstring(self):
        """Verify generator.py has documentation."""
        from tests.fixtures.thicket import generator

        # Check for module docstring
        assert generator.__doc__ is not None, (
            "generator.py should have a module docstring"
        )

    def test_generate_function_exists(self):
        """Verify the generate_thicket function exists and is callable."""
        from tests.fixtures.thicket import generate_thicket

        assert callable(generate_thicket), "generate_thicket should be callable"


class TestThicketPythonResolver:
    """Test PythonResolver on the complex thicket POM hierarchy.

    Note: We only test PythonResolver here because the thicket is a synthetic
    test fixture with only POM files and no actual JAR artifacts. MvnResolver
    requires real artifacts to function. For resolver parity tests against real
    Maven artifacts, see test_resolution.py.
    """

    def test_python_resolver_managed(self, thicket_pom, thicket_context):
        """
        Test that PythonResolver can handle the thicket's complex POM hierarchy (managed mode).

        This validates the Python resolver's ability to handle:
        - Multi-level parent POM inheritance (up to 4 levels)
        - BOM imports with transitive imports (up to 3 per POM)
        - Property-based versioning and interpolation
        - Complex dependency management merging

        The thicket is randomly generated but with a fixed seed, so it provides
        a reproducible stress test for the resolver.
        """
        from jgo.maven.resolver import PythonResolver

        # Read the thicket version from the POM
        thicket_pom_obj = POM(thicket_pom)
        version = thicket_pom_obj.version

        # Create component and wrap in Dependency
        from jgo.maven import Dependency

        component = thicket_context.project(
            "org.scijava.jgo.thicket", "thicket"
        ).at_version(version)
        deps_input = [Dependency(component.artifact())]

        # Resolve with Python resolver - should not raise any errors
        python_resolver = PythonResolver()
        _, python_deps = python_resolver.resolve(deps_input)

        # We can't compare against a hardcoded truth since the thicket is randomly generated,
        # but we can verify basic properties:
        # 1. Dependencies were resolved (not empty unless thicket has no deps)
        # 2. All dependencies have proper coordinates
        for dep in python_deps:
            assert dep.groupId, "Dependency should have groupId"
            assert dep.artifactId, "Dependency should have artifactId"
            assert dep.version, "Dependency should have version"
            # Versions should be resolved (no property placeholders)
            assert "${" not in dep.version, (
                f"Uninterpolated property in {dep.groupId}:{dep.artifactId}: {dep.version}"
            )

    def test_python_resolver_unmanaged(self, thicket_pom, thicket_context):
        """
        Test that PythonResolver can handle the thicket without dependency management.

        This is a simpler case but still validates the resolver's ability to:
        - Build a complete model from a complex POM hierarchy
        - Resolve dependencies without managed versions
        - Handle property interpolation correctly
        """
        from jgo.maven.resolver import PythonResolver

        # Read the thicket version from the POM
        thicket_pom_obj = POM(thicket_pom)
        version = thicket_pom_obj.version

        # Create component and wrap in Dependency (raw=True for unmanaged)
        from jgo.maven import Dependency

        component = thicket_context.project(
            "org.scijava.jgo.thicket", "thicket"
        ).at_version(version)
        deps_input = [Dependency(component.artifact(), raw=True)]

        # Resolve with Python resolver
        python_resolver = PythonResolver()
        _, python_deps = python_resolver.resolve(deps_input)

        # Verify all dependencies are properly resolved
        for dep in python_deps:
            assert dep.groupId, "Dependency should have groupId"
            assert dep.artifactId, "Dependency should have artifactId"
            assert dep.version, "Dependency should have version"
            assert "${" not in dep.version, (
                f"Uninterpolated property in {dep.groupId}:{dep.artifactId}: {dep.version}"
            )
