#!/usr/bin/env python3
"""
Unit tests for endpoint parsing with @ separator.
"""

import tempfile
import warnings
from pathlib import Path

import pytest

from jgo.env import EnvironmentBuilder
from jgo.maven import MavenContext


def test_parse_endpoint_new_format_simple():
    """Test new @ separator format with simple artifact."""
    maven = MavenContext()
    builder = EnvironmentBuilder(maven_context=maven)

    # New format: G:A@MainClass
    components, managed_flags, main_class = builder._parse_endpoint(
        "org.example:artifact@Main"
    )

    assert len(components) == 1
    assert components[0].groupId == "org.example"
    assert components[0].artifactId == "artifact"
    assert main_class == "Main"
    assert not managed_flags[0]


def test_parse_endpoint_new_format_with_version():
    """Test new @ separator format with version."""
    maven = MavenContext()
    builder = EnvironmentBuilder(maven_context=maven)

    # New format: G:A:V@MainClass
    components, managed_flags, main_class = builder._parse_endpoint(
        "org.example:artifact:1.0.0@com.example.Main"
    )

    assert len(components) == 1
    assert components[0].groupId == "org.example"
    assert components[0].artifactId == "artifact"
    assert components[0].resolved_version == "1.0.0"
    assert main_class == "com.example.Main"


def test_parse_endpoint_new_format_multiple_artifacts():
    """Test new @ separator format with multiple artifacts."""
    maven = MavenContext()
    builder = EnvironmentBuilder(maven_context=maven)

    # New format: G:A+G:A@MainClass
    components, managed_flags, main_class = builder._parse_endpoint(
        "org.example:artifact1+org.example:artifact2@Main"
    )

    assert len(components) == 2
    assert components[0].groupId == "org.example"
    assert components[0].artifactId == "artifact1"
    assert components[1].groupId == "org.example"
    assert components[1].artifactId == "artifact2"
    assert main_class == "Main"


def test_parse_endpoint_new_format_with_managed():
    """Test new @ separator format with managed dependency."""
    maven = MavenContext()
    builder = EnvironmentBuilder(maven_context=maven)

    # New format with managed flag: G:A!@MainClass
    components, managed_flags, main_class = builder._parse_endpoint(
        "org.example:artifact!@Main"
    )

    assert len(components) == 1
    assert managed_flags[0] is True
    assert main_class == "Main"


def test_parse_endpoint_old_format_deprecated():
    """Test old :@MainClass format triggers deprecation warning."""
    maven = MavenContext()
    builder = EnvironmentBuilder(maven_context=maven)

    # Old format: G:A:@MainClass (should trigger warning)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        components, managed_flags, main_class = builder._parse_endpoint(
            "org.example:artifact:@Main"
        )

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert ":@mainClass" in str(w[0].message)

    assert main_class == "@Main"  # Old format keeps the @ prefix


def test_parse_endpoint_old_format_colon_mainclass():
    """Test old :mainClass format triggers deprecation warning."""
    maven = MavenContext()
    builder = EnvironmentBuilder(maven_context=maven)

    # Old format: G:A:mainClass (should trigger warning)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        components, managed_flags, main_class = builder._parse_endpoint(
            "org.example:artifact:com.example.Main"
        )

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert ":mainClass" in str(w[0].message)

    assert main_class == "com.example.Main"


def test_parse_endpoint_no_main_class():
    """Test parsing without main class."""
    maven = MavenContext()
    builder = EnvironmentBuilder(maven_context=maven)

    # No main class specified
    components, managed_flags, main_class = builder._parse_endpoint(
        "org.example:artifact:1.0.0"
    )

    assert len(components) == 1
    assert main_class is None


def test_parse_endpoint_only_second_component_ignored():
    """Test that main class on second component is ignored."""
    maven = MavenContext()
    builder = EnvironmentBuilder(maven_context=maven)

    # Main class only on first component should be used
    components, managed_flags, main_class = builder._parse_endpoint(
        "org.example:artifact1@Main+org.example:artifact2"
    )

    assert len(components) == 2
    assert main_class == "Main"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
