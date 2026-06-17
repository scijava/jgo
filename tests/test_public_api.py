#!/usr/bin/env python3
"""
Checks that jgo's public API is exported correctly and completely, and any changes
since the last release align with the advertised dev version according to SemVer.

If test_all_is_complete fails, update __all__ in the offending module.
If test_semver_version fails, update the version in pyproject.toml.
"""

from __future__ import annotations

import importlib
import pkgutil
import re
import subprocess
import types
from pathlib import Path

import griffe
import pytest

import jgo

ROOT = Path(__file__).parent.parent


def _discover_public_subpackages():
    """Return all non-private jgo subpackages (excludes jgo itself — see test_all_is_complete)."""
    return sorted(
        modname
        for _, modname, ispkg in pkgutil.walk_packages(jgo.__path__, prefix="jgo.")
        if ispkg and not any(part.startswith("_") for part in modname.split("."))
    )


PUBLIC_MODULES = _discover_public_subpackages()


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


def _get_submodule(root, module_name):
    """Navigate from a loaded root package to a named submodule (e.g. 'jgo.cli.rich')."""
    obj = root
    for part in module_name.split(".")[1:]:
        obj = obj.members[part]
    return obj


def _public_api(obj: griffe.Object, prefix: str = "") -> set[str]:
    result: set[str] = set()
    # For modules: use __all__ if declared, else fall back to underscore convention.
    # For classes: always use underscore convention (classes don't declare __all__).
    if isinstance(obj, griffe.Module) and obj.exports is not None:
        # str() coercion: griffe 2.x exports may contain ExprName, not just str
        candidate_names: set[str] = {str(n) for n in obj.exports}
    else:
        candidate_names = {n for n in obj.members if not n.startswith("_")}
    for name in candidate_names:
        member = obj.members.get(name)
        if member is None:
            continue
        full = f"{prefix}.{name}" if prefix else name
        if isinstance(member, griffe.Alias):
            try:
                if not member.target_path.startswith("jgo."):
                    continue
                result.add(full)
                target = member.final_target
                if isinstance(target, griffe.Class):
                    result |= _public_api(target, full)
            except Exception:
                pass
        else:
            result.add(full)
            if isinstance(member, (griffe.Module, griffe.Class)):
                result |= _public_api(member, full)
    return result


def _last_release_tag() -> str | None:
    result = subprocess.run(
        ["git", "tag", "--sort=-v:refname"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    tags = [t for t in result.stdout.splitlines() if re.fullmatch(r"\d+\.\d+\.\d+", t)]
    return tags[0] if tags else None


def _current_release_tag() -> str | None:
    result = subprocess.run(
        ["git", "describe", "--tags", "--exact-match", "HEAD"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        return None
    tag = result.stdout.strip()
    return tag if re.fullmatch(r"\d+\.\d+\.\d+", tag) else None


@pytest.mark.parametrize("module_name", PUBLIC_MODULES)
def test_all_is_declared(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert hasattr(module, "__all__"), f"{module_name} must declare __all__"


@pytest.mark.parametrize("module_name", PUBLIC_MODULES)
def test_all_is_complete(module_name: str) -> None:
    module = importlib.import_module(module_name)
    actual = sorted(module.__all__)
    expected = _expected_all(module)
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    assert not missing, f"{module_name}.__all__ is missing: {missing}"
    assert not extra, f"{module_name}.__all__ has stale entries: {extra}"


def test_semver_version() -> None:
    from jgo.util.toml import load_toml_file

    last_tag = _last_release_tag()
    if last_tag is None:
        pytest.skip("No release tags found")

    pyproject = load_toml_file(ROOT / "pyproject.toml")
    assert pyproject is not None, "pyproject.toml not found"
    current_version: str = pyproject["project"]["version"]
    release_tag = _current_release_tag()

    if release_tag is not None:
        assert not current_version.endswith(".dev0"), (
            f"Version {current_version!r} should not end in .dev0 on a release tag"
        )
        assert current_version == release_tag, (
            f"Version {current_version!r} does not match release tag {release_tag!r}"
        )
        return

    assert current_version.endswith(".dev0"), (
        f"Version {current_version!r} must end in .dev0 when not on a release tag"
    )
    base_version = current_version.removesuffix(".dev0")

    last = tuple(int(x) for x in last_tag.split("."))
    curr = tuple(int(x) for x in base_version.split("."))
    x, y, z = last

    if curr == (x + 1, 0, 0):
        claimed_bump = "major"
    elif curr == (x, y + 1, 0):
        claimed_bump = "minor"
    elif curr == (x, y, z + 1):
        claimed_bump = "patch"
    else:
        pytest.fail(
            f"Version {current_version!r} is not a valid SemVer bump from {last_tag!r}"
        )

    old_root = griffe.load_git(
        "jgo", ref=last_tag, repo=str(ROOT), search_paths=["src"]
    )
    new_root = griffe.load("jgo", search_paths=[str(ROOT / "src")])
    old_api: set[str] = set()
    new_api: set[str] = set()
    for module_name in PUBLIC_MODULES:
        try:
            old_api |= _public_api(_get_submodule(old_root, module_name), module_name)
        except KeyError:
            pass  # module didn't exist in the old version
        new_api |= _public_api(_get_submodule(new_root, module_name), module_name)
    removed = old_api - new_api
    added = new_api - old_api

    if removed:
        required_bump = "major"
    elif added:
        required_bump = "minor"
    else:
        required_bump = "patch"

    assert claimed_bump == required_bump, (
        f"Version bump is {claimed_bump!r} but API changes require {required_bump!r}.\n"
        f"  Added:   {sorted(added) or 'none'}\n"
        f"  Removed: {sorted(removed) or 'none'}"
    )
