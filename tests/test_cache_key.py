"""Test that cache key includes classifier and packaging."""

from jgo.env._builder import EnvironmentBuilder
from jgo.maven import MavenContext
from jgo.parse._coordinate import Coordinate


def test_cache_key_includes_classifier():
    """Test that different classifiers produce different cache keys."""
    context = MavenContext()
    builder = EnvironmentBuilder(context)

    # Create coordinates with different classifiers
    coord1 = Coordinate(
        groupId="org.lwjgl",
        artifactId="lwjgl",
        version="3.3.1",
        classifier="natives-linux",
        packaging="jar",
    )

    coord2 = Coordinate(
        groupId="org.lwjgl",
        artifactId="lwjgl",
        version="3.3.1",
        classifier="natives-windows",
        packaging="jar",
    )

    # Convert to dependencies
    deps1 = builder._coordinates_to_dependencies([coord1])
    deps2 = builder._coordinates_to_dependencies([coord2])

    # Generate cache keys
    key1 = builder._cache_key(deps1)
    key2 = builder._cache_key(deps2)

    # Different classifiers should produce different keys
    assert key1 != key2, f"Expected different cache keys but got: {key1} == {key2}"


def test_cache_key_includes_packaging():
    """Test that different packaging types produce different cache keys."""
    context = MavenContext()
    builder = EnvironmentBuilder(context)

    # Create coordinates with different packaging
    coord1 = Coordinate(
        groupId="org.example",
        artifactId="myapp",
        version="1.0.0",
        classifier="",
        packaging="jar",
    )

    coord2 = Coordinate(
        groupId="org.example",
        artifactId="myapp",
        version="1.0.0",
        classifier="",
        packaging="war",
    )

    # Convert to dependencies
    deps1 = builder._coordinates_to_dependencies([coord1])
    deps2 = builder._coordinates_to_dependencies([coord2])

    # Generate cache keys
    key1 = builder._cache_key(deps1)
    key2 = builder._cache_key(deps2)

    # Different packaging should produce different keys
    assert key1 != key2, f"Expected different cache keys but got: {key1} == {key2}"


def test_cache_key_same_coordinates():
    """Test that identical coordinates produce the same cache key."""
    context = MavenContext()
    builder = EnvironmentBuilder(context)

    coord1 = Coordinate(
        groupId="org.example",
        artifactId="myapp",
        version="1.0.0",
        classifier="linux",
        packaging="jar",
    )

    coord2 = Coordinate(
        groupId="org.example",
        artifactId="myapp",
        version="1.0.0",
        classifier="linux",
        packaging="jar",
    )

    deps1 = builder._coordinates_to_dependencies([coord1])
    deps2 = builder._coordinates_to_dependencies([coord2])

    key1 = builder._cache_key(deps1)
    key2 = builder._cache_key(deps2)

    # Same coordinates should produce same key
    assert key1 == key2, f"Expected same cache keys but got: {key1} != {key2}"
