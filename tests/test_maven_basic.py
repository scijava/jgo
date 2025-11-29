#!/usr/bin/env python3
"""
Basic tests for the Maven layer to verify the port was successful.
"""

from jgo.maven import MavenContext, SimpleResolver


def test_maven_context_creation():
    """Test that MavenContext can be created."""
    maven = MavenContext()
    assert maven is not None
    assert maven.repo_cache is not None
    assert maven.resolver is not None
    assert isinstance(maven.resolver, SimpleResolver)
    print("✓ MavenContext creation works")


def test_project_creation():
    """Test that projects can be created."""
    maven = MavenContext()
    project = maven.project("org.scijava", "scijava-common")
    assert project is not None
    assert project.groupId == "org.scijava"
    assert project.artifactId == "scijava-common"
    print("✓ Project creation works")


def test_component_creation():
    """Test that components can be created."""
    maven = MavenContext()
    project = maven.project("org.scijava", "scijava-common")
    component = project.at_version("2.97.0")
    assert component is not None
    assert component.version == "2.97.0"
    assert component.groupId == "org.scijava"
    assert component.artifactId == "scijava-common"
    print("✓ Component creation works")


def test_artifact_creation():
    """Test that artifacts can be created."""
    maven = MavenContext()
    component = maven.project("org.scijava", "scijava-common").at_version("2.97.0")
    artifact = component.artifact()
    assert artifact is not None
    assert artifact.groupId == "org.scijava"
    assert artifact.artifactId == "scijava-common"
    assert artifact.version == "2.97.0"
    assert artifact.packaging == "jar"
    assert artifact.filename == "scijava-common-2.97.0.jar"
    print("✓ Artifact creation works")


def test_string_representation():
    """Test string representations."""
    maven = MavenContext()
    project = maven.project("org.scijava", "scijava-common")
    assert str(project) == "org.scijava:scijava-common"

    component = project.at_version("2.97.0")
    assert str(component) == "org.scijava:scijava-common:2.97.0"

    artifact = component.artifact()
    assert str(artifact) == "org.scijava:scijava-common:jar:2.97.0"
    print("✓ String representations work")


def main():
    """Run all tests."""
    print("Testing Maven layer...")
    print()

    try:
        test_maven_context_creation()
        test_project_creation()
        test_component_creation()
        test_artifact_creation()
        test_string_representation()

        print()
        print("All basic tests passed! ✓")
        return 0
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
