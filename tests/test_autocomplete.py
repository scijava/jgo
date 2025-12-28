#!/usr/bin/env python3
"""
Unit tests for main class auto-completion.
"""

import tempfile
import warnings
import zipfile
from pathlib import Path

import pytest

from jgo.env.jar import autocomplete_main_class


def create_jar_with_class(jar_path: Path, class_name: str):
    """Helper to create a JAR with a fake class entry."""
    with zipfile.ZipFile(jar_path, "w") as jar:
        # Convert class name to path (e.g., org.example.Main -> org/example/Main.class)
        class_path = class_name.replace(".", "/") + ".class"
        jar.writestr(class_path, b"fake class bytes")


def test_autocomplete_fully_qualified():
    """Test that fully qualified class names are used as-is."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jars_dir = Path(tmp_dir)

        # Test with fully qualified name (contains dots)
        result = autocomplete_main_class("org.example.Main", "artifact", jars_dir)
        assert result == "org.example.Main"


def test_autocomplete_simple_name():
    """Test auto-completion of simple class name."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jars_dir = Path(tmp_dir)

        # Create a JAR with a matching class
        jar_path = jars_dir / "artifact-1.0.0.jar"
        create_jar_with_class(jar_path, "org.example.Main")

        # Test auto-completion with simple name (no dots)
        result = autocomplete_main_class("Main", "artifact", jars_dir)
        assert result == "org.example.Main"


def test_autocomplete_with_at_prefix():
    """Test old @ prefix format for partial matching."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jars_dir = Path(tmp_dir)

        # Create a JAR with a matching class
        jar_path = jars_dir / "artifact-1.0.0.jar"
        create_jar_with_class(jar_path, "org.scijava.script.ScriptREPL")

        # Test old @ prefix format
        result = autocomplete_main_class("@ScriptREPL", "artifact", jars_dir)
        assert result == "org.scijava.script.ScriptREPL"


def test_autocomplete_at_prefix_not_found():
    """Test that @ prefix raises error when not found."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jars_dir = Path(tmp_dir)

        # No matching JAR
        with pytest.raises(ValueError, match="Unable to auto-complete"):
            autocomplete_main_class("@NonExistent", "artifact", jars_dir)


def test_autocomplete_simple_name_not_found():
    """Test that simple name returns as-is with warning when not found."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jars_dir = Path(tmp_dir)

        # No matching JAR
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = autocomplete_main_class("NonExistent", "artifact", jars_dir)

            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "Could not auto-complete" in str(w[0].message)

        # Should return original name
        assert result == "NonExistent"


def test_autocomplete_nested_class():
    """Test auto-completion with nested class."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jars_dir = Path(tmp_dir)

        # Create a JAR with nested class
        jar_path = jars_dir / "artifact-1.0.0.jar"
        create_jar_with_class(jar_path, "org.example.Outer$Inner")

        # Test auto-completion with simple name
        result = autocomplete_main_class("Inner", "artifact", jars_dir)
        assert result == "org.example.Outer$Inner"


def test_autocomplete_filters_by_artifact_id():
    """Test that auto-completion only searches relevant JARs for simple names."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jars_dir = Path(tmp_dir)

        # Create JAR without artifact ID in name
        wrong_jar = jars_dir / "other-1.0.0.jar"
        create_jar_with_class(wrong_jar, "org.other.Main")

        # Create JAR with artifact ID in name
        right_jar = jars_dir / "myartifact-1.0.0.jar"
        create_jar_with_class(right_jar, "org.example.Main")

        # Should find class in right JAR only
        result = autocomplete_main_class("Main", "myartifact", jars_dir)
        assert result == "org.example.Main"


def test_autocomplete_fully_qualified_uses_as_is():
    """Test that fully qualified class names are used as-is without searching."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jars_dir = Path(tmp_dir)

        # Create JAR without artifact ID in name (doesn't contain the class)
        other_jar = jars_dir / "scijava-common-1.0.0.jar"
        create_jar_with_class(other_jar, "org.imagej.Main")

        # Create JAR with artifact ID in name (doesn't contain the class either)
        artifact_jar = jars_dir / "imagej-1.0.0.jar"
        create_jar_with_class(artifact_jar, "org.imagej.ImageJ")

        # Should use fully qualified name as-is without searching
        result = autocomplete_main_class(
            "org.scijava.script.ScriptREPL", "imagej", jars_dir
        )
        assert result == "org.scijava.script.ScriptREPL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
