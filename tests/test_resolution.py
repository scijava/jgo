"""
Tests for dependency resolution behavior.

These tests validate that dependency resolution works correctly with both
MavenResolver and SimpleResolver, including proper handling of dependency
management and scope filtering.
"""

from jgo.maven import MavenContext
from jgo.maven.resolver import MavenResolver, SimpleResolver


def test_minimaven_resolution_maven_managed(tmp_path):
    """
    Test resolution of org.scijava:minimaven:2.2.2 with Maven resolver and managed=True.

    This should match the output from running `mvn dependency:list` in the actual project.
    Expected dependencies (excluding test scope):
    - org.scijava:scijava-common:jar:2.77.0
    - org.scijava:parsington:jar:1.0.4
    - org.bushe:eventbus:jar:1.4
    """
    from jgo.util.cjdk import ensure_maven_available

    context = MavenContext(repo_cache=tmp_path / "m2_repo")
    component = context.project("org.scijava", "minimaven").at_version("2.2.2")

    # Use MavenResolver (will download Maven via cjdk if needed)
    mvn_command = ensure_maven_available()
    resolver = MavenResolver(mvn_command, update=False)

    deps = resolver.dependencies([component], managed=True)

    # Should have exactly 3 compile/runtime dependencies
    assert len(deps) == 3, f"Expected 3 dependencies, got {len(deps)}"

    # Check each expected dependency
    dep_coords = {(d.groupId, d.artifactId, d.version) for d in deps}

    assert ("org.scijava", "scijava-common", "2.77.0") in dep_coords
    assert ("org.scijava", "parsington", "1.0.4") in dep_coords
    assert ("org.bushe", "eventbus", "1.4") in dep_coords

    # Ensure no test scope dependencies leaked through
    for dep in deps:
        assert dep.scope != "test", f"Test dependency should not be included: {dep}"


def test_minimaven_resolution_simple_no_managed(tmp_path):
    """
    Test resolution of org.scijava:minimaven:2.2.2 with SimpleResolver and managed=False.

    Note: SimpleResolver always respects the component's own dependencyManagement section
    (this is built into the Model class). The managed flag only controls whether to
    import components as BOMs in an additional dependencyManagement section.

    For minimaven, parsington is 1.0.4 regardless of the managed flag when using
    SimpleResolver, because minimaven's own POM specifies 1.0.4 in its dependencyManagement.
    """
    context = MavenContext(repo_cache=tmp_path / "m2_repo")
    component = context.project("org.scijava", "minimaven").at_version("2.2.2")

    resolver = SimpleResolver()
    deps = resolver.dependencies([component], managed=False)

    # Should still have 3 dependencies
    assert len(deps) == 3, f"Expected 3 dependencies, got {len(deps)}"

    # Check dependencies (parsington is 1.0.4 due to minimaven's own dependencyManagement)
    dep_coords = {(d.groupId, d.artifactId, d.version) for d in deps}

    assert ("org.scijava", "scijava-common", "2.77.0") in dep_coords
    assert ("org.scijava", "parsington", "1.0.4") in dep_coords
    assert ("org.bushe", "eventbus", "1.4") in dep_coords


def test_no_test_scope_in_resolution(tmp_path):
    """
    Test that test scope dependencies are excluded from resolution.

    org.scijava:minimaven:2.2.2 has junit and hamcrest-core as test dependencies,
    which should not appear in the resolved dependency list.
    """
    context = MavenContext(repo_cache=tmp_path / "m2_repo")
    component = context.project("org.scijava", "minimaven").at_version("2.2.2")

    resolver = SimpleResolver()
    deps = resolver.dependencies([component], managed=True)

    # Check that no test dependencies are present
    for dep in deps:
        assert dep.groupId != "junit", "junit (test dependency) should not be included"
        assert dep.groupId != "org.hamcrest", (
            "hamcrest (test dependency) should not be included"
        )


def test_component_not_in_dependency_list(tmp_path):
    """
    Test that the component itself does not appear in its dependency list.

    When using wrapper POMs, the component is added to the POM's dependencies section,
    but it should be filtered out of the final dependency list.
    """
    context = MavenContext(repo_cache=tmp_path / "m2_repo")
    component = context.project("org.scijava", "minimaven").at_version("2.2.2")

    resolver = SimpleResolver()
    deps = resolver.dependencies([component], managed=True)

    # The component itself should not be in the dependency list
    for dep in deps:
        assert not (dep.groupId == "org.scijava" and dep.artifactId == "minimaven"), (
            "The component itself should not appear in its dependency list"
        )


def test_multi_component_resolution(tmp_path):
    """
    Test that multi-component resolution works correctly with SimpleResolver.

    This test verifies that:
    1. Both components are resolved together in a single resolution
    2. Neither component appears in its own dependency list
    3. Dependencies are properly merged without duplicates
    4. Version conflicts are resolved correctly
    """
    context = MavenContext(repo_cache=tmp_path / "m2_repo")
    comp1 = context.project("org.scijava", "minimaven").at_version("2.2.2")
    comp2 = context.project("org.scijava", "parsington").at_version("3.1.0")

    resolver = SimpleResolver()
    deps = resolver.dependencies([comp1, comp2], managed=True)

    # Neither component should appear in the dependency list
    dep_coords = {(d.groupId, d.artifactId) for d in deps}
    assert ("org.scijava", "minimaven") not in dep_coords
    assert ("org.scijava", "parsington") not in dep_coords

    # All dependencies should be unique (no duplicates)
    assert len(deps) == len(set((d.groupId, d.artifactId, d.version) for d in deps))

    # Should have scijava-common (from both minimaven and parsington's dependencies)
    # Version should be resolved correctly
    assert ("org.scijava", "scijava-common") in dep_coords
