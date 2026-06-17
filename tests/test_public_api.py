#!/usr/bin/env python3
"""
Validates that __all__ in each public jgo module matches its actual public symbols.

If this test fails, update __all__ in the offending module to include the new
symbol (for a new public API addition) or remove the stale entry.
"""

import importlib
import types

import pytest

PUBLIC_MODULES = [
    # jgo top-level excluded: its __all__ is intentionally narrow (run/build/resolve/__version__)
    # and testing it would require restructuring how subpackage imports land in the namespace.
    "jgo.cli",
    "jgo.cli.rich",
    "jgo.config",
    "jgo.env",
    "jgo.exec",
    "jgo.maven",
    "jgo.parse",
    "jgo.util",
]


def _expected_all(module):
    return sorted(
        k
        for k, v in vars(module).items()
        if not k.startswith("_")
        and (
            (isinstance(v, types.ModuleType) and v.__name__.startswith("jgo."))
            or (hasattr(v, "__module__") and v.__module__.startswith("jgo."))
        )
    )


@pytest.mark.parametrize("module_name", PUBLIC_MODULES)
def test_all_is_complete(module_name):
    module = importlib.import_module(module_name)
    actual = sorted(module.__all__)
    expected = _expected_all(module)
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    assert not missing, f"{module_name}.__all__ is missing: {missing}"
    assert not extra, f"{module_name}.__all__ has stale entries: {extra}"
