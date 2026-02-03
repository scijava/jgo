"""
Tests for dependency resolution behavior.

These tests validate that dependency resolution works correctly with both
MvnResolver and PythonResolver, including proper handling of dependency
management and scope filtering.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from jgo.env import EnvironmentBuilder
from jgo.maven import MavenContext
from jgo.maven.core import Component, Dependency
from jgo.maven.resolver import MvnResolver, PythonResolver
from jgo.parse.endpoint import Endpoint
from jgo.util.maven import ensure_maven_available


@dataclass(frozen=True)
class DiffExpectation:
    added: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()

    def added_set(self) -> set[str]:
        return set(self.added)

    def removed_set(self) -> set[str]:
        return set(self.removed)


@dataclass(frozen=True)
class ResolutionScenario:
    endpoint: str
    truth: tuple[str, ...]
    unmanaged: DiffExpectation = DiffExpectation()

    def truth_set(self) -> set[str]:
        return set(self.truth)


RESOLUTION_SCENARIOS: tuple[ResolutionScenario, ...] = (
    ResolutionScenario(
        endpoint="org.scijava:minimaven:2.2.2",
        truth=(
            "org.bushe:eventbus:jar:1.4",
            "org.scijava:parsington:jar:1.0.4",
            "org.scijava:scijava-common:jar:2.77.0",
        ),
        unmanaged=DiffExpectation(
            added=("org.scijava:parsington:jar:1.0.3",),
            removed=("org.scijava:parsington:jar:1.0.4",),
        ),
    ),
    ResolutionScenario(
        endpoint="org.scijava:scijava-maven-plugin:3.0.1",
        truth=(
            "com.google.code.findbugs:jsr305:jar:3.0.2",
            "com.google.errorprone:error_prone_annotations:jar:2.32.0",
            "com.google.guava:failureaccess:jar:1.0.2",
            "com.google.guava:guava:jar:33.3.1-jre",
            "com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava",
            "com.google.j2objc:j2objc-annotations:jar:3.0.0",
            "commons-codec:commons-codec:jar:1.17.1",
            "commons-io:commons-io:jar:2.17.0",
            "guru.nidi:jdepend:jar:2.9.5",
            "javax.el:javax.el-api:jar:3.0.0",
            "javax.enterprise:cdi-api:jar:2.0.SP1",
            "javax.inject:javax.inject:jar:1",
            "javax.interceptor:javax.interceptor-api:jar:1.2",
            "net.sf.jgrapht:jgrapht:jar:0.8.3",
            "org.apache.maven:maven-aether-provider:jar:3.0",
            "org.apache.maven:maven-artifact:jar:3.0",
            "org.apache.maven:maven-core:jar:3.0",
            "org.apache.maven:maven-model:jar:3.0",
            "org.apache.maven:maven-model-builder:jar:3.0",
            "org.apache.maven:maven-plugin-api:jar:3.0",
            "org.apache.maven:maven-repository-metadata:jar:3.0",
            "org.apache.maven:maven-settings:jar:3.0",
            "org.apache.maven:maven-settings-builder:jar:3.0",
            "org.apache.maven.enforcer:enforcer-api:jar:3.5.0",
            "org.apache.maven.plugin-tools:maven-plugin-annotations:jar:3.5",
            "org.apache.maven.resolver:maven-resolver-api:jar:1.9.18",
            "org.apache.maven.shared:maven-artifact-transfer:jar:0.9.1",
            "org.apache.maven.shared:maven-common-artifact-filters:jar:3.0.1",
            "org.apache.maven.shared:maven-shared-utils:jar:3.1.0",
            "org.checkerframework:checker-qual:jar:3.48.0",
            "org.codehaus.plexus:plexus-classworlds:jar:2.5.2",
            "org.codehaus.plexus:plexus-component-annotations:jar:2.2.0",
            "org.codehaus.plexus:plexus-interpolation:jar:1.24",
            "org.codehaus.plexus:plexus-utils:jar:3.1.0",
            "org.eclipse.sisu:org.eclipse.sisu.inject:jar:0.3.0",
            "org.eclipse.sisu:org.eclipse.sisu.plexus:jar:0.3.0",
            "org.scijava:parsington:jar:3.1.0",
            "org.scijava:scijava-common:jar:2.99.0",
            "org.slf4j:slf4j-api:jar:1.7.36",
            "org.sonatype.aether:aether-api:jar:1.7",
            "org.sonatype.aether:aether-impl:jar:1.7",
            "org.sonatype.aether:aether-spi:jar:1.7",
            "org.sonatype.aether:aether-util:jar:1.7",
            "org.sonatype.plexus:plexus-cipher:jar:1.4",
            "org.sonatype.plexus:plexus-sec-dispatcher:jar:1.3",
            "org.sonatype.sisu:sisu-guice:jar:no_aop:3.2.5",
            "org.sonatype.sisu:sisu-inject-bean:jar:2.6.0",
            "org.sonatype.sisu:sisu-inject-plexus:jar:2.6.0",
        ),
        # NB: With managed=False, the root's dependencyManagement is not applied
        # to transitive dependencies, resulting in different (usually older) versions.
        unmanaged=DiffExpectation(
            added=(
                "commons-codec:commons-codec:jar:1.6",
                "commons-io:commons-io:jar:2.5",
                "javax.annotation:jsr250-api:jar:1.0",
                "javax.enterprise:cdi-api:jar:1.0",
                "org.codehaus.plexus:plexus-component-annotations:jar:1.7.1",
                "org.slf4j:slf4j-api:jar:1.7.5",
                "org.sonatype.sisu:sisu-guice:jar:noaop:2.1.7",
                "org.sonatype.sisu:sisu-inject-bean:jar:1.4.2",
                "org.sonatype.sisu:sisu-inject-plexus:jar:1.4.2",
            ),
            removed=(
                "com.google.code.findbugs:jsr305:jar:3.0.2",
                "com.google.errorprone:error_prone_annotations:jar:2.32.0",
                "com.google.guava:failureaccess:jar:1.0.2",
                "com.google.guava:guava:jar:33.3.1-jre",
                "com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava",
                "com.google.j2objc:j2objc-annotations:jar:3.0.0",
                "commons-codec:commons-codec:jar:1.17.1",
                "commons-io:commons-io:jar:2.17.0",
                "javax.el:javax.el-api:jar:3.0.0",
                "javax.enterprise:cdi-api:jar:2.0.SP1",
                "javax.interceptor:javax.interceptor-api:jar:1.2",
                "org.checkerframework:checker-qual:jar:3.48.0",
                "org.codehaus.plexus:plexus-component-annotations:jar:2.2.0",
                "org.slf4j:slf4j-api:jar:1.7.36",
                "org.sonatype.sisu:sisu-guice:jar:no_aop:3.2.5",
                "org.sonatype.sisu:sisu-inject-bean:jar:2.6.0",
                "org.sonatype.sisu:sisu-inject-plexus:jar:2.6.0",
            ),
        ),
    ),
)


def dependency_fingerprint(dep: Dependency) -> str:
    parts = [dep.groupId, dep.artifactId, dep.type]
    if dep.classifier:
        parts.append(dep.classifier)
    parts.append(dep.version)
    return ":".join(parts)


def dependencies_from_endpoint(
    context: MavenContext, endpoint: str
) -> list[Dependency]:
    builder = EnvironmentBuilder(context)
    parsed = Endpoint.parse(endpoint)
    return builder._coordinates_to_dependencies(parsed.coordinates)


def resolve_dependency_set(resolver, dependencies: list[Dependency]) -> set[str]:
    _, resolved_deps = resolver.resolve(dependencies)
    return {dependency_fingerprint(dep) for dep in resolved_deps}


def components_from_endpoint(context: MavenContext, endpoint: str) -> list[Component]:
    deps = dependencies_from_endpoint(context, endpoint)
    return [dep.artifact.component for dep in deps]


def assert_expected_diff(
    endpoint: str,
    truth: set[str],
    candidate: set[str],
    expected: DiffExpectation,
) -> None:
    removed = truth - candidate
    added = candidate - truth
    expected_removed = expected.removed_set()
    expected_added = expected.added_set()
    assert removed == expected_removed, (
        f"Unexpected dependencies missing from unmanaged resolution of {endpoint}: "
        f"expected {sorted(expected_removed)}, got {sorted(removed)}"
    )
    assert added == expected_added, (
        f"Unexpected dependencies added in unmanaged resolution of {endpoint}: "
        f"expected {sorted(expected_added)}, got {sorted(added)}"
    )


@pytest.fixture(scope="module")
def maven_command():
    return ensure_maven_available()


@pytest.fixture(scope="module")
def mvn_resolver(maven_command):
    return MvnResolver(maven_command, update=False)


@pytest.mark.parametrize(
    "scenario",
    RESOLUTION_SCENARIOS,
    ids=lambda case: case.endpoint,
)
def test_resolution_modes(m2_repo, scenario, mvn_resolver):
    python_resolver = PythonResolver()
    context = MavenContext(repo_cache=m2_repo, resolver=python_resolver)

    # Managed mode: dependencies with raw=False (default)
    managed_deps = dependencies_from_endpoint(context, scenario.endpoint)

    # Unmanaged mode: same dependencies but with raw=True
    unmanaged_deps = [
        Dependency(dep.artifact, dep.scope, dep.optional, dep.exclusions, raw=True)
        for dep in managed_deps
    ]

    truth = resolve_dependency_set(mvn_resolver, managed_deps)
    assert truth == scenario.truth_set(), (
        f"Maven resolver managed output for {scenario.endpoint} "
        "diverged from expected truth"
    )

    mvn_unmanaged = resolve_dependency_set(mvn_resolver, unmanaged_deps)
    assert_expected_diff(scenario.endpoint, truth, mvn_unmanaged, scenario.unmanaged)

    python_managed = resolve_dependency_set(python_resolver, managed_deps)
    assert python_managed == truth, (
        f"PythonResolver managed output differed from Maven for {scenario.endpoint}"
    )

    python_unmanaged = resolve_dependency_set(python_resolver, unmanaged_deps)
    assert python_unmanaged == mvn_unmanaged, (
        "PythonResolver --no-managed output differed from Maven for "
        f"{scenario.endpoint}"
    )


def test_no_test_scope_in_resolution(m2_repo):
    """
    Test that test scope dependencies are excluded from resolution.

    org.scijava:minimaven:2.2.2 has junit and hamcrest-core as test dependencies,
    which should not appear in the resolved dependency list.
    """
    context = MavenContext(repo_cache=m2_repo)
    deps = dependencies_from_endpoint(context, "org.scijava:minimaven:2.2.2")

    resolver = PythonResolver()
    _, resolved_deps = resolver.resolve(deps)

    # Check that no test dependencies are present
    for dep in resolved_deps:
        assert dep.groupId != "junit", "junit (test dependency) should not be included"
        assert dep.groupId != "org.hamcrest", (
            "hamcrest (test dependency) should not be included"
        )


def test_component_not_in_dependency_list(m2_repo):
    """
    Test that the component itself does not appear in its dependency list.

    When using wrapper POMs, the component is added to the POM's dependencies section,
    but it should be filtered out of the final dependency list.
    """
    context = MavenContext(repo_cache=m2_repo)
    deps = dependencies_from_endpoint(context, "org.scijava:minimaven:2.2.2")

    resolver = PythonResolver()
    _, resolved_deps = resolver.resolve(deps)

    # The component itself should not be in the dependency list
    for dep in resolved_deps:
        assert not (dep.groupId == "org.scijava" and dep.artifactId == "minimaven"), (
            "The component itself should not appear in its dependency list"
        )


def test_multi_component_resolution(m2_repo):
    """
    Test that multi-component resolution works correctly with PythonResolver.

    This test verifies that:
    1. Both components are resolved together in a single resolution
    2. Neither component appears in its own dependency list
    3. Dependencies are properly merged without duplicates
    4. Version conflicts are resolved correctly
    """
    context = MavenContext(repo_cache=m2_repo)
    deps = dependencies_from_endpoint(
        context, "org.scijava:minimaven:2.2.2+org.scijava:parsington:3.1.0"
    )

    resolver = PythonResolver()
    _, resolved_deps = resolver.resolve(deps)

    # Neither component should appear in the dependency list
    dep_coords = {(d.groupId, d.artifactId) for d in resolved_deps}
    assert ("org.scijava", "minimaven") not in dep_coords
    assert ("org.scijava", "parsington") not in dep_coords

    # All dependencies should be unique (no duplicates)
    assert len(resolved_deps) == len(
        set((d.groupId, d.artifactId, d.version) for d in resolved_deps)
    )

    # Should have scijava-common (from both minimaven and parsington's dependencies)
    # Version should be resolved correctly
    assert ("org.scijava", "scijava-common") in dep_coords


def test_managed_version_resolution(m2_repo):
    """
    Test that MANAGED version string is resolved from dependency management.

    When a dependency has version "MANAGED", it should be resolved from the
    dependencyManagement section of the primary component. This test verifies
    that the PythonResolver correctly handles this case.

    Uses org.scijava:scijava-common:2.66.0 which has minimaven in its
    dependencyManagement at version 2.2.1.
    """
    context = MavenContext(repo_cache=m2_repo)

    # Create dependencies: primary with concrete version, secondary with MANAGED
    deps = dependencies_from_endpoint(
        context, "org.scijava:scijava-common:2.66.0+org.scijava:minimaven:MANAGED"
    )

    resolver = PythonResolver()
    # Use get_dependency_list which returns root node with dependencies as children
    root, dep_nodes = resolver.get_dependency_list(deps)

    # The root's children should include the resolved components
    # Find minimaven in root's children
    optional_nodes = [
        child for child in root.children if child.dep.artifactId == "minimaven"
    ]
    assert len(optional_nodes) == 1, "Expected minimaven as root child"
    # The version should be resolved from dependency management (2.2.1)
    assert optional_nodes[0].dep.version == "2.2.1", (
        "Expected minimaven version 2.2.1 from dependency management, "
        f"got {optional_nodes[0].dep.version}"
    )
