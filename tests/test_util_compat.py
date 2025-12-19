"""Tests for deprecated util/compat.py functions."""

import pytest

from jgo.util.compat import add_jvm_args_as_necessary


def test_add_jvm_args_deprecated_warning():
    """Test that deprecation warning is raised."""
    with pytest.warns(
        DeprecationWarning, match="add_jvm_args_as_necessary.*deprecated"
    ):
        add_jvm_args_as_necessary([])


def test_add_jvm_args_backward_compatibility():
    """Test that old API still works."""
    # Should add heap size and GC
    with pytest.warns(DeprecationWarning):
        result = add_jvm_args_as_necessary([])

    assert any("-Xmx" in arg for arg in result)
    assert any("-XX:+UseConcMarkSweepGC" in arg for arg in result)


def test_add_jvm_args_respects_existing_heap():
    """Test that existing -Xmx is not overridden."""
    with pytest.warns(DeprecationWarning):
        result = add_jvm_args_as_necessary(["-Xmx1G"])

    # Should only have the one -Xmx we provided
    heap_args = [arg for arg in result if "-Xmx" in arg]
    assert len(heap_args) == 1
    assert "-Xmx1G" in heap_args


def test_add_jvm_args_custom_gc():
    """Test custom GC option."""
    with pytest.warns(DeprecationWarning):
        result = add_jvm_args_as_necessary([], gc_option="-XX:+UseG1GC")

    assert "-XX:+UseG1GC" in result
