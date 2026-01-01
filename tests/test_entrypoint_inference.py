"""
Test entrypoint inference from coordinate references.
"""

import tempfile
from pathlib import Path


def test_coordinate_reference_inference():
    """
    Test that coordinate references in entrypoints are properly inferred.
    """
    from jgo.env import EnvironmentBuilder, EnvironmentSpec
    from jgo.maven import MavenContext, PythonResolver

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create a spec with coordinate reference entrypoint
        spec = EnvironmentSpec(
            name="test-inference",
            description="Test coordinate reference inference",
            coordinates=["org.scijava:parsington:3.1.0"],
            entrypoints={"main": "org.scijava:parsington:3.1.0"},
            default_entrypoint="main",
            cache_dir=tmp_path / ".jgo",
        )

        spec_file = tmp_path / "jgo.toml"
        spec.save(spec_file)

        # Build environment
        context = MavenContext(
            resolver=PythonResolver(),
            repo_cache=tmp_path / ".m2" / "repository",
        )

        builder = EnvironmentBuilder(context, cache_dir=tmp_path / ".jgo")
        env = builder.from_spec(spec, update=False)

        # Check that lockfile was generated
        lockfile_path = env.path / "jgo.lock.toml"
        assert lockfile_path.exists()

        # Load lockfile and check entrypoints
        from jgo.env.lockfile import LockFile

        lockfile = LockFile.load(lockfile_path)

        # Should have concrete main class inferred from JAR
        assert lockfile.entrypoints
        assert "main" in lockfile.entrypoints

        # The inferred class should not contain colons (it's a concrete class name)
        inferred_class = lockfile.entrypoints["main"]
        assert ":" not in inferred_class
        assert "." in inferred_class  # Should be fully qualified


def test_explicit_class_name_in_entrypoint():
    """
    Test that explicit class names in entrypoints are preserved.
    """
    from jgo.env import EnvironmentBuilder, EnvironmentSpec
    from jgo.maven import MavenContext, PythonResolver

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create a spec with explicit class name entrypoint
        spec = EnvironmentSpec(
            name="test-explicit",
            description="Test explicit class name",
            coordinates=["org.scijava:scijava-common:2.97.1"],
            entrypoints={"main": "ScriptREPL"},  # Simple name, will be auto-completed
            default_entrypoint="main",
            cache_dir=tmp_path / ".jgo",
        )

        spec_file = tmp_path / "jgo.toml"
        spec.save(spec_file)

        # Build environment
        context = MavenContext(
            resolver=PythonResolver(),
            repo_cache=tmp_path / ".m2" / "repository",
        )

        builder = EnvironmentBuilder(context, cache_dir=tmp_path / ".jgo")
        env = builder.from_spec(spec, update=False)

        # Load lockfile
        from jgo.env.lockfile import LockFile

        lockfile = LockFile.load(env.path / "jgo.lock.toml")

        # Should have auto-completed the class name
        assert lockfile.entrypoints
        assert "main" in lockfile.entrypoints

        # Should be fully qualified (auto-completed)
        completed_class = lockfile.entrypoints["main"]
        assert "ScriptREPL" in completed_class
        assert "." in completed_class  # Should be fully qualified


def test_lockfile_has_spec_hash():
    """
    Test that lockfile includes spec hash for staleness detection.
    """
    from jgo.env import EnvironmentBuilder, EnvironmentSpec
    from jgo.maven import MavenContext, PythonResolver

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        spec = EnvironmentSpec(
            name="test-hash",
            coordinates=["org.scijava:parsington:3.1.0"],
            cache_dir=tmp_path / ".jgo",
        )

        spec_file = tmp_path / "jgo.toml"
        spec.save(spec_file)

        # Build environment
        context = MavenContext(
            resolver=PythonResolver(),
            repo_cache=tmp_path / ".m2" / "repository",
        )

        builder = EnvironmentBuilder(context, cache_dir=tmp_path / ".jgo")
        env = builder.from_spec(spec, update=False)

        # Load lockfile
        from jgo.env.lockfile import LockFile

        lockfile = LockFile.load(env.path / "jgo.lock.toml")

        # Should have spec hash
        assert lockfile.spec_hash is not None
        assert len(lockfile.spec_hash) == 16  # 16 hex characters
