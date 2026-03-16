"""Pytest configuration and shared fixtures."""

import shutil
import subprocess
from pathlib import Path

import pytest

from jgo.util.mvn import ensure_maven_available
from tests.fixtures.thicket import DEFAULT_SEED, generate_thicket

_BOOTSTRAP_SENTINEL = Path(".cache/m2_repo/.bootstrapped")


@pytest.fixture(scope="session")
def thicket_poms(tmp_path_factory):
    """
    Generate thicket POMs for testing.

    This is a session-scoped fixture that generates the thicket POM hierarchy
    once at the beginning of the test session. The POMs are generated with a
    fixed random seed for reproducibility.

    Returns:
        Path: Directory containing generated thicket POMs
    """
    # Create a temporary directory for this test session
    pom_dir = tmp_path_factory.mktemp("thicket_poms")

    # Generate the thicket POMs with a fixed seed for reproducibility
    generate_thicket(pom_dir, seed=DEFAULT_SEED)

    return pom_dir


@pytest.fixture(scope="session")
def m2_repo(tmp_path_factory):
    """
    Provide a writable Maven repository directory for testing.

    Seeds the temp directory from the persistent .cache/m2_repo if it exists,
    so previously downloaded artifacts are available without re-downloading.

    Returns:
        Path: Temporary Maven repository directory for this test session
    """
    test_repo = tmp_path_factory.mktemp("m2_repo")
    cache_dir = Path(".cache/m2_repo")
    if cache_dir.exists():
        shutil.copytree(cache_dir, test_repo, dirs_exist_ok=True)
    return test_repo


@pytest.fixture(scope="session")
def maven_bootstrap(m2_repo):
    """
    Ensure Maven's own infrastructure JARs are present in the repository.

    Runs mvn dependency:list and dependency:tree against a bootstrap POM to
    pre-populate the persistent cache with Maven's plugin infrastructure.
    Skipped if the sentinel file indicates a previous bootstrap completed.

    Only tests that use MvnResolver need this fixture.

    Returns:
        Path: Same Maven repository directory as m2_repo, now bootstrapped
    """
    cache_dir = Path(".cache/m2_repo")
    cache_dir.mkdir(parents=True, exist_ok=True)

    if not _BOOTSTRAP_SENTINEL.exists():
        bootstrap_pom = Path(__file__).parent / "fixtures" / "bootstrap-pom.xml"
        maven_cmd = ensure_maven_available()
        for goal in ["dependency:list", "dependency:tree"]:
            subprocess.run(
                [
                    maven_cmd,
                    "-f",
                    str(bootstrap_pom),
                    f"-Dmaven.repo.local={cache_dir}",
                    goal,
                ],
                check=True,
                capture_output=True,
            )
        _BOOTSTRAP_SENTINEL.touch()
        # Sync newly downloaded infrastructure into the session's test repo
        shutil.copytree(cache_dir, m2_repo, dirs_exist_ok=True)

    return m2_repo
